# app/api/v1/routes/payments.py
#
# WHY THIS FILE EXISTS:
# HTTP layer for all payment operations.
# Thin layer — validates input, calls payment_service, returns response.
#
# Endpoints:
#   POST /payments/initiate          → buyer initiates STK Push
#   POST /payments/mpesa/callback    → Safaricom webhook (no auth)
#   POST /payments/confirm           → admin manually confirms payment
#   GET  /payments/order/{order_id}  → get payment status for an order
#   POST /payments/expire            → admin manually triggers expiry check

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.services.payment_service import (
    create_payment_transaction,
    initiate_stk_push,
    handle_mpesa_callback,
    expire_stale_reservations,
    get_payment_by_order,
    confirm_payment_manually,
    initiate_fisher_payout,
)
from app.services.kcb_service import parse_kcb_callback
from app.models.payment import PaymentMethod, PaymentChannel
from app.models.order import Order

router = APIRouter(prefix="/payments", tags=["Payments"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class STKPushRequest(BaseModel):
    order_id:     int
    phone_number: str


class ManualConfirmRequest(BaseModel):
    order_id:       int
    confirmed_by:   Optional[str] = None
    payment_method: Optional[str] = "cash"
    notes:          Optional[str] = None


# ── INITIATE STK PUSH ─────────────────────────────────────────────

@router.post("/initiate")
async def initiate_payment(
    payload:     STKPushRequest,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Buyer initiates M-Pesa STK Push payment for their order.
    Sends payment prompt to their phone.
    They have 10 minutes to complete payment before stock is released.

    Example:
    Neptune Hotels places order, gets STK Push to 0711000001.
    Enters PIN, payment confirmed, order moves to CONFIRMED.
    """
    # Get the order
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Security: buyer can only pay for their own order
    if order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only pay for your own orders"
        )

    # Check order is in payable state
    if order.status.value not in ["pending_payment"]:
        raise HTTPException(
            status_code=400,
            detail=f"Order cannot be paid in current status: {order.status.value}"
        )

    # Create payment transaction record
    txn = create_payment_transaction(
        db=              db,
        order=           order,
        payment_method=  PaymentMethod.MPESA_STK,
        payment_channel= PaymentChannel.MPESA,
        payer_user_id=   current_user.id,
        is_credit_sale=  False,
        notes=           f"STK Push initiated by {current_user.name}",
    )

    # Send STK Push
    result = await initiate_stk_push(
        db=           db,
        txn=          txn,
        phone_number= payload.phone_number,
    )

    return result


# ── M-PESA CALLBACK (no auth — Safaricom calls this) ─────────────

@router.post("/mpesa/callback")
async def mpesa_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint for Safaricom M-Pesa callbacks.
    Safaricom calls this after STK Push is completed or fails.
    NO authentication — Safaricom doesn't send tokens.

    This endpoint must be publicly accessible.
    In production: set MPESA_CALLBACK_URL to your domain.
    In sandbox: use ngrok to expose localhost.
    """
    try:
        callback_data = await request.json()
    except Exception:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    result = handle_mpesa_callback(db, callback_data)

    # Always return success to Safaricom
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


# ── GET PAYMENT STATUS ────────────────────────────────────────────

@router.get("/order/{order_id}")
def get_payment_status(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Get payment status for a specific order.
    Buyer checks if their payment went through.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    txn = get_payment_by_order(db, order_id)
    if not txn:
        return {
            "order_id":       order_id,
            "order_status":   order.status,
            "payment_status": "no_payment_initiated",
        }

    return {
        "order_id":              order_id,
        "order_status":          order.status,
        "transaction_reference": txn.transaction_reference,
        "payment_status":        txn.payment_status,
        "payment_method":        txn.payment_method,
        "total_amount":          txn.total_amount,
        "currency":              txn.currency,
        "mpesa_receipt":         txn.mpesa_receipt_number,
        "paid_at":               txn.paid_at,
        "reserved_until":        order.reserved_until,
        "payout_status":         txn.payout_status,
    }


# ── MANUAL CONFIRM (admin) ────────────────────────────────────────

@router.post("/confirm")
def manual_confirm(
    payload:     ManualConfirmRequest,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Admin manually confirms a payment.
    Used for: cash, bank transfer, institutional credit approval.

    Example:
    Hotel pays via bank transfer.
    Admin confirms receipt and marks order as paid.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can manually confirm payments"
        )

    txn = confirm_payment_manually(
        db=             db,
        order_id=       payload.order_id,
        confirmed_by=   payload.confirmed_by or current_user.name,
        payment_method= payload.payment_method or "cash",
        notes=          payload.notes,
    )

    return {
        "success":               True,
        "transaction_reference": txn.transaction_reference,
        "payment_status":        txn.payment_status,
        "order_id":              txn.order_id,
        "total_amount":          txn.total_amount,
        "confirmed_by":          txn.confirmed_by,
        "paid_at":               txn.paid_at,
        "message":               f"Payment confirmed for order {payload.order_id}"
    }


# ── EXPIRE STALE RESERVATIONS (admin) ────────────────────────────

@router.post("/expire-check")
def run_expiry_check(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Check for and expire stale unpaid reservations.
    Admin triggers this manually for MVP.
    Phase 3: automated background task runs every 2 minutes.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can run expiry check"
        )

    count = expire_stale_reservations(db)

    return {
        "success":         True,
        "expired_orders":  count,
        "message":         f"{count} stale reservation(s) expired and stock released."
    }

# ── FISHER PAYOUT (admin) ─────────────────────────────────────────

@router.post("/payout/{order_id}")
async def trigger_fisher_payout(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Admin triggers fisher payout after order is delivered.
    Sends B2C M-Pesa payment directly to fisher's phone.

    Requirements:
    - Order must be in DELIVERED status
    - Payment must be confirmed (PAID)
    - Fisher must have a phone number registered

    Example:
    Neptune Hotels confirms tuna delivery.
    Admin triggers payout — Bakari Usi receives KES 15,210 on his phone.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can trigger fisher payouts"
        )

    result = await initiate_fisher_payout(
        db=       db,
        order_id= order_id,
        admin=    current_user.name,
    )

    return result

# ── KCB BUNI INTEGRATION ────────────────────────────────────────

@router.post("/kcb/validate")
async def kcb_validate(request: Request):
    """
    IPN Account validation endpoint (per KCB Buni spec).
    Called by KCB to validate account/reference before a
    Funds Transfer transaction proceeds.
    """
    payload = await request.json()
    print(f"KCB validation request: {payload}")

    # Basic validation — always accept for now since we don't
    # have KCB's exact account reference format yet
    return {
        "ResultCode": "0",
        "ResultDesc": "Accepted",
    }


@router.post("/kcb/confirm")
async def kcb_confirm(request: Request, db: Session = Depends(get_db)):
    """
    STK Callback endpoint (per KCB Buni spec).
    Called by KCB after an M-Pesa Express (STK Push) payment
    from a buyer completes — success or failure.
    """
    payload = await request.json()
    print(f"KCB STK callback received: {payload}")

    parsed = parse_kcb_callback(payload)

    if parsed["success"]:
        print(
            f"KCB payment SUCCESS: KES {parsed['amount']} from "
            f"{parsed['phone_number']}, receipt {parsed['mpesa_receipt']}"
        )
        # TODO: Match parsed['checkout_request_id'] or amount/phone
        # to a pending TradeReceivable, then call:
        # settlement_service.record_payment(db, receivable_id, ...)
    else:
        print(
            f"KCB payment FAILED: {parsed['result_desc']} "
            f"(code {parsed['result_code']})"
        )

    return {
        "ResultCode": "0",
        "ResultDesc": "Accepted",
    }


@router.post("/kcb/callback")
async def kcb_callback(request: Request):
    """
    B2C Funds Transfer callback endpoint (per KCB Buni spec).
    Called by KCB after MarineCatch's payout to a supplier/
    fisher via bank transfer completes. This is where we
    match to a SupplierPayment and call record_supplier_payout().
    """
    payload = await request.json()
    print(f"KCB callback received: {payload}")

    parsed = parse_kcb_callback(payload)

    # TODO: Match parsed['reference'] to a SupplierPayment
    # and call settlement_service.record_supplier_payout()

    return {
        "ResultCode": "0",
        "ResultDesc": "Received",
    }