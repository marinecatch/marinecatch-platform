# app/services/payment_service.py
#
# WHY THIS FILE EXISTS:
# Connects orders to M-Pesa payments.
# Orchestrates the full payment lifecycle:
# - Create PaymentTransaction record
# - Initiate STK Push
# - Handle callback from Safaricom
# - Update order status on payment confirmation
# - Queue fisher payout
#
# Retail flow (STK Push):
# place_order → initiate_stk_push → webhook_callback → confirm_payment
#
# Institutional flow (credit):
# place_order → create_credit_transaction → admin_confirms → confirm_payment

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from typing import Optional
import random
import string

from app.models.payment import (
    PaymentTransaction, PaymentStatus, PaymentChannel,
    PaymentMethod, PaymentDirection, PaymentPurpose,
    CreditStatus, PayoutStatus
)
from app.models.order import Order, OrderStatus
from app.models.inventory_lot import InventoryLot
from app.services.inventory_service import release_stock


# ── TRANSACTION REFERENCE GENERATOR ──────────────────────────────
def generate_transaction_reference(db: Session) -> str:
    """
    Generate unique transaction reference.
    Format: MC-PAY-YYYYMMDD-XXXXX
    Example: MC-PAY-20260517-00042
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    # Count today's transactions for sequence number
    count = db.query(PaymentTransaction).filter(
        PaymentTransaction.transaction_reference.like(f"MC-PAY-{today}-%")
    ).count()
    sequence = str(count + 1).zfill(5)
    return f"MC-PAY-{today}-{sequence}"


# ── CREATE PAYMENT TRANSACTION ────────────────────────────────────
def create_payment_transaction(
    db:               Session,
    order:            Order,
    payment_method:   PaymentMethod,
    payment_channel:  PaymentChannel,
    payer_user_id:    Optional[int] = None,
    is_credit_sale:   bool = False,
    credit_due_date:  Optional[datetime] = None,
    notes:            Optional[str] = None,
) -> PaymentTransaction:
    """
    Create a PaymentTransaction record for an order.
    Called before initiating STK Push or recording manual payment.
    """
    ref = generate_transaction_reference(db)

    # Calculate fee breakdown from order
    # commission_rate stored as string like "2.5%"
    try:
        rate = float(order.commission_rate.replace("%", "")) / 100
    except Exception:
        rate = 0.025

    subtotal   = round(order.quantity_kg * order.price_per_kg, 2)
    commission = order.platform_fee_kes
    total      = order.total_kes

    # Supplier gets fish value minus commission
    supplier_amount     = order.net_to_fisher_kes
    marinecatch_amount  = commission

    # Credit terms
    credit_status = CreditStatus.NOT_APPLICABLE
    if is_credit_sale:
        credit_status = CreditStatus.PENDING_APPROVAL

    # Reservation expiry — 10 minutes for retail STK Push
    # Null for credit/institutional buyers
    reserved_until = None
    if not is_credit_sale and payment_method == PaymentMethod.MPESA_STK:
        reserved_until = datetime.now(timezone.utc) + timedelta(minutes=10)

    txn = PaymentTransaction(
        transaction_reference = ref,
        order_id              = order.id,
        payer_user_id         = payer_user_id or order.buyer_id,
        payee_user_id         = order.fisherman_id,
        payment_direction     = PaymentDirection.INBOUND,
        payment_purpose       = PaymentPurpose.ORDER_PAYMENT,
        payment_channel       = payment_channel,
        payment_method        = payment_method,
        payment_provider      = "safaricom" if payment_channel == PaymentChannel.MPESA else None,
        currency              = "KES",
        exchange_rate         = 1.0,
        subtotal_amount       = subtotal,
        commission_amount     = commission,
        storage_fee_amount    = 0.0,
        handling_fee_amount   = 0.0,
        qa_fee_amount         = 0.0,
        logistics_fee_amount  = 0.0,
        tax_amount            = 0.0,
        total_amount          = total,
        payment_status        = PaymentStatus.PENDING,
        is_credit_sale        = is_credit_sale,
        credit_due_date       = credit_due_date,
        credit_status         = credit_status,
        supplier_amount       = supplier_amount,
        marinecatch_amount    = marinecatch_amount,
        payout_status         = PayoutStatus.PENDING,
        country               = "KE",
        notes                 = notes,
    )

    db.add(txn)

    # Update order reserved_until for retail buyers
    if reserved_until:
        order.reserved_until = reserved_until

    db.commit()
    db.refresh(txn)
    return txn


# ── INITIATE STK PUSH ─────────────────────────────────────────────
async def initiate_stk_push(
    db:           Session,
    txn:          PaymentTransaction,
    phone_number: str,
) -> dict:
    """
    Send STK Push to buyer's phone and update transaction.
    Returns Safaricom response.
    """
    from app.services.mpesa_service import stk_push

    try:
        response = await stk_push(
            phone_number          = phone_number,
            amount                = txn.total_amount,
            transaction_reference = txn.transaction_reference,
            description           = f"MarineCatch {txn.transaction_reference}"
        )

        # Store Safaricom IDs for webhook matching
        txn.checkout_request_id  = response.get("CheckoutRequestID")
        txn.merchant_request_id  = response.get("MerchantRequestID")
        txn.mpesa_phone_number   = phone_number
        txn.payment_status       = PaymentStatus.PROCESSING

        db.commit()
        db.refresh(txn)

        return {
            "success":              True,
            "transaction_reference": txn.transaction_reference,
            "checkout_request_id":  txn.checkout_request_id,
            "message":              f"STK Push sent to {phone_number}. Enter your M-Pesa PIN to complete payment.",
            "amount":               txn.total_amount,
            "expires_in_minutes":   10,
        }

    except Exception as e:
        txn.payment_status = PaymentStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=502,
            detail=f"M-Pesa STK Push failed: {str(e)}"
        )


# ── HANDLE M-PESA CALLBACK ────────────────────────────────────────
def handle_mpesa_callback(
    db:       Session,
    callback: dict,
) -> dict:
    """
    Process callback from Safaricom after STK Push.
    Safaricom sends this to your MPESA_CALLBACK_URL.

    ResultCode 0 = success
    ResultCode 1 = insufficient funds
    ResultCode 1032 = user cancelled
    ResultCode 1037 = timeout
    """
    stk_callback = callback.get("Body", {}).get("stkCallback", {})
    result_code  = stk_callback.get("ResultCode")
    checkout_id  = stk_callback.get("CheckoutRequestID")

    # Find the transaction
    txn = db.query(PaymentTransaction).filter(
        PaymentTransaction.checkout_request_id == checkout_id
    ).first()

    if not txn:
        return {"status": "ignored", "reason": "transaction not found"}

    if result_code == 0:
        # Payment successful
        metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        meta = {item["Name"]: item.get("Value") for item in metadata}

        txn.mpesa_receipt_number = meta.get("MpesaReceiptNumber")
        txn.payment_status       = PaymentStatus.PAID
        txn.paid_at              = datetime.now(timezone.utc)
        txn.payout_status        = PayoutStatus.PENDING

        # Update order status
        order = db.query(Order).filter(Order.id == txn.order_id).first()
        if order:
            order.status       = OrderStatus.CONFIRMED
            order.reserved_until = None

        db.commit()
        return {
            "status":  "success",
            "receipt": txn.mpesa_receipt_number,
            "amount":  txn.total_amount,
        }

    else:
        # Payment failed or cancelled
        if result_code in [1037, 1032]:
            txn.payment_status = PaymentStatus.EXPIRED
        else:
            txn.payment_status = PaymentStatus.FAILED

        # Don't release stock yet — buyer has 10 minute window to retry
        db.commit()
        return {
            "status":      "failed",
            "result_code": result_code,
            "message":     stk_callback.get("ResultDesc"),
        }


# ── EXPIRE STALE RESERVATIONS ─────────────────────────────────────
def expire_stale_reservations(db: Session) -> int:
    """
    Release stock for orders past their reservation window.
    Call this periodically — every 2 minutes via background task.
    For MVP: call manually or on each new order placement.

    Returns count of orders expired.
    """
    now     = datetime.now(timezone.utc)
    expired = db.query(Order).filter(
        Order.status         == OrderStatus.PENDING_PAYMENT,
        Order.reserved_until != None,
        Order.reserved_until <= now,
    ).all()

    count = 0
    for order in expired:
        # Release inventory
        if order.lot_id and order.quantity_kg:
            release_stock(db, order.lot_id, order.quantity_kg)

        # Cancel order
        order.status = OrderStatus.CANCELLED

        # Mark payment as expired
        txn = db.query(PaymentTransaction).filter(
            PaymentTransaction.order_id == order.id,
            PaymentTransaction.payment_status == PaymentStatus.PROCESSING,
        ).first()
        if txn:
            txn.payment_status = PaymentStatus.EXPIRED

        count += 1

    if count > 0:
        db.commit()

    return count


# ── GET PAYMENT BY ORDER ──────────────────────────────────────────
def get_payment_by_order(db: Session, order_id: int) -> Optional[PaymentTransaction]:
    """Get the most recent payment transaction for an order."""
    return db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id == order_id
    ).order_by(PaymentTransaction.created_at.desc()).first()


# ── GET PAYMENT BY REFERENCE ──────────────────────────────────────
def get_payment_by_reference(
    db: Session, reference: str
) -> Optional[PaymentTransaction]:
    return db.query(PaymentTransaction).filter(
        PaymentTransaction.transaction_reference == reference
    ).first()


# ── MANUAL PAYMENT CONFIRMATION (admin) ───────────────────────────
def confirm_payment_manually(
    db:           Session,
    order_id:     int,
    confirmed_by: str,
    payment_method: str = "cash",
    notes:        Optional[str] = None,
) -> PaymentTransaction:
    """
    Admin manually confirms a payment.
    Used for: cash payments, bank transfers, institutional credit approval.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get or create payment transaction
    txn = get_payment_by_order(db, order_id)
    if not txn:
        raise HTTPException(
            status_code=404,
            detail="No payment transaction found for this order"
        )

    txn.payment_status = PaymentStatus.PAID
    txn.confirmed_by   = confirmed_by
    txn.paid_at        = datetime.now(timezone.utc)
    txn.payout_status  = PayoutStatus.PENDING
    txn.notes          = notes

    order.status         = OrderStatus.CONFIRMED
    order.reserved_until = None

    db.commit()
    db.refresh(txn)
    return txn
# ── FISHER PAYOUT ─────────────────────────────────────────────────
async def initiate_fisher_payout(
    db:       Session,
    order_id: int,
    admin:    str,
) -> dict:
    """
    Trigger B2C payout to fisher after order is delivered.
    Called when order status moves to DELIVERED.

    Flow:
    1. Get the order and find the fisher
    2. Get the payment transaction
    3. Calculate fisher's payout amount
    4. Send B2C payment to fisher's phone
    5. Update payout status
    """
    from app.services.mpesa_service import b2c_payment

    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Order must be delivered
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=400,
            detail=f"Order must be DELIVERED before payout. Current: {order.status.value}"
        )

    # Get payment transaction
    txn = get_payment_by_order(db, order_id)
    if not txn:
        raise HTTPException(
            status_code=404,
            detail="No payment transaction found for this order"
        )

    # Payment must be confirmed
    if txn.payment_status != PaymentStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail=f"Payment must be PAID before fisher payout. Current: {txn.payment_status.value}"
        )

    # Already paid out
    if txn.payout_status == PayoutStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail="Fisher payout already completed"
        )

    # Get fisher's phone number
    from app.models.user import User
    fisher = db.query(User).filter(User.id == order.fisherman_id).first()
    if not fisher:
        raise HTTPException(
            status_code=404,
            detail="Fisher not found for this order"
        )

    if not fisher.phone:
        raise HTTPException(
            status_code=400,
            detail="Fisher has no phone number registered for M-Pesa payout"
        )

    payout_amount = txn.supplier_amount
    if not payout_amount or payout_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid payout amount"
        )

    # Generate payout reference
    payout_ref = f"MC-PAYOUT-{order_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Update payout status to processing
    txn.payout_status = PayoutStatus.PROCESSING
    db.commit()

    try:
        # Send B2C payment
        response = await b2c_payment(
            phone_number          = fisher.phone,
            amount                = payout_amount,
            transaction_reference = payout_ref,
            remarks               = f"MarineCatch payout order {order_id}"
        )

        # Update transaction with payout details
        txn.payout_status    = PayoutStatus.PROCESSING
        txn.payout_reference = response.get("ConversationID", payout_ref)
        txn.confirmed_by     = admin
        db.commit()

        return {
            "success":        True,
            "order_id":       order_id,
            "fisher_name":    fisher.name,
            "fisher_phone":   fisher.phone,
            "payout_amount":  payout_amount,
            "payout_ref":     payout_ref,
            "message":        f"Payout of KES {payout_amount} initiated to {fisher.name} ({fisher.phone})"
        }

    except Exception as e:
        txn.payout_status = PayoutStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=502,
            detail=f"B2C payout failed: {str(e)}"
        )