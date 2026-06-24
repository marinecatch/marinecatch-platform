# app/api/v1/routes/settlement.py
#
# Settlement management endpoints.
# Handles trade receivables (buyer payments) and
# supplier payments (fisher/supplier payouts).

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.services.settlement_service import (
    create_receivable,
    record_payment,
    get_overdue_receivables,
    mark_overdue,
    create_supplier_payment,
    record_supplier_payout,
    get_pending_supplier_payments,
    get_working_capital_position,
)
from app.models.trade_receivable import TradeReceivable, ReceivableStatus
from app.models.supplier_payment import SupplierPayment, SupplierPaymentStatus
from app.models.user import User

router = APIRouter(prefix="/settlement", tags=["Settlement"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class ReceivableCreate(BaseModel):
    buyer_id:          int
    gross_amount_kes:  float
    payment_terms:     str = "net_30"
    order_id:          Optional[int] = None
    species:           Optional[str] = None
    quantity_kg:       Optional[float] = None
    delivery_location: Optional[str] = None
    received_by:       Optional[str] = None
    notes:             Optional[str] = None


class PaymentRecord(BaseModel):
    amount_paid:       float
    payment_method:    str
    payment_reference: Optional[str] = None
    notes:             Optional[str] = None


class SupplierPaymentCreate(BaseModel):
    supplier_id:          int
    purchase_amount_kes:  float
    payment_terms:        str = "immediate"
    lot_id:               Optional[int] = None
    order_id:             Optional[int] = None
    species:              Optional[str] = None
    quantity_kg:          Optional[float] = None
    notes:                Optional[str] = None


class SupplierPayoutRecord(BaseModel):
    amount_paid:      float
    payment_method:   str
    mpesa_reference:  Optional[str] = None
    bank_reference:   Optional[str] = None
    notes:            Optional[str] = None


# ── WORKING CAPITAL ───────────────────────────────────────────────

@router.get("/working-capital")
def working_capital(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """MarineCatch working capital position — receivables vs payables."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return get_working_capital_position(db)


# ── TRADE RECEIVABLES ─────────────────────────────────────────────

@router.post("/receivables", status_code=201)
def create_trade_receivable(
    payload:     ReceivableCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Create a receivable when MarineCatch delivers to a buyer."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    receivable = create_receivable(
        db                = db,
        buyer_id          = payload.buyer_id,
        gross_amount_kes  = payload.gross_amount_kes,
        payment_terms     = payload.payment_terms,
        order_id          = payload.order_id,
        species           = payload.species,
        quantity_kg       = payload.quantity_kg,
        delivery_location = payload.delivery_location,
        received_by       = payload.received_by,
        created_by        = current_user.name,
        notes             = payload.notes,
    )

    return {
        "success":        True,
        "invoice_number": receivable.invoice_number,
        "total_kes":      receivable.total_amount_kes,
        "due_date":       receivable.due_date,
        "payment_terms":  receivable.payment_terms,
        "status":         receivable.status,
    }


@router.get("/receivables")
def list_receivables(
    status:      Optional[str] = Query(None),
    buyer_id:    Optional[int] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """List all trade receivables."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(TradeReceivable)
    if status:
        query = query.filter(TradeReceivable.status == status)
    if buyer_id:
        query = query.filter(TradeReceivable.buyer_id == buyer_id)

    receivables = query.order_by(TradeReceivable.due_date.asc()).all()

    result = []
    for r in receivables:
        buyer = db.query(User).filter(User.id == r.buyer_id).first()
        result.append({
            "id":              r.id,
            "invoice_number":  r.invoice_number,
            "buyer_name":      buyer.name if buyer else "—",
            "buyer_id":        r.buyer_id,
            "total_kes":       r.total_amount_kes,
            "paid_kes":        r.paid_amount_kes,
            "outstanding_kes": r.outstanding_kes,
            "payment_terms":   r.payment_terms,
            "due_date":        r.due_date,
            "delivery_date":   r.delivery_date,
            "status":          r.status,
            "species":         r.species,
            "quantity_kg":     r.quantity_kg,
            "delivery_location": r.delivery_location,
            "etims_issued":    r.etims_issued,
            "invoice_stamped": r.invoice_stamped,
        })

    return {"total": len(result), "receivables": result}


@router.get("/receivables/overdue")
def overdue_receivables(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Get all overdue receivables with days overdue."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    mark_overdue(db)
    overdue = get_overdue_receivables(db)
    now     = datetime.now()

    result = []
    for r in overdue:
        buyer = db.query(User).filter(User.id == r.buyer_id).first()
        days_overdue = (now - r.due_date.replace(tzinfo=None)).days if r.due_date else 0
        result.append({
            "id":              r.id,
            "invoice_number":  r.invoice_number,
            "buyer_name":      buyer.name if buyer else "—",
            "buyer_phone":     buyer.phone if buyer else "—",
            "outstanding_kes": r.outstanding_kes,
            "due_date":        r.due_date,
            "days_overdue":    days_overdue,
            "species":         r.species,
            "delivery_location": r.delivery_location,
        })

    return {"total": len(result), "overdue": result}


@router.post("/receivables/{receivable_id}/payment")
def record_buyer_payment(
    receivable_id: int,
    payload:       PaymentRecord,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Record a payment received from a buyer."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    receivable = record_payment(
        db                = db,
        receivable_id     = receivable_id,
        amount_paid       = payload.amount_paid,
        payment_method    = payload.payment_method,
        payment_reference = payload.payment_reference,
        notes             = payload.notes,
    )

    return {
        "success":         True,
        "invoice_number":  receivable.invoice_number,
        "paid_kes":        receivable.paid_amount_kes,
        "outstanding_kes": receivable.outstanding_kes,
        "status":          receivable.status,
    }


# ── SUPPLIER PAYMENTS ─────────────────────────────────────────────

@router.post("/supplier-payments", status_code=201)
def create_supplier_pmt(
    payload:     SupplierPaymentCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Create a supplier payment record when receiving from a fisher/supplier."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    payment = create_supplier_payment(
        db                   = db,
        supplier_id          = payload.supplier_id,
        purchase_amount_kes  = payload.purchase_amount_kes,
        payment_terms        = payload.payment_terms,
        lot_id               = payload.lot_id,
        order_id             = payload.order_id,
        species              = payload.species,
        quantity_kg          = payload.quantity_kg,
        created_by           = current_user.name,
        notes                = payload.notes,
    )

    return {
        "success":              True,
        "reference":            payment.reference,
        "purchase_amount_kes":  payment.purchase_amount_kes,
        "payment_terms":        payment.payment_terms,
        "agreed_payment_date":  payment.agreed_payment_date,
        "status":               payment.status,
    }


@router.get("/supplier-payments")
def list_supplier_payments(
    status:      Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """List all supplier payments — what MarineCatch owes."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(SupplierPayment)
    if status:
        query = query.filter(SupplierPayment.status == status)
    if supplier_id:
        query = query.filter(SupplierPayment.supplier_id == supplier_id)

    payments = query.order_by(SupplierPayment.agreed_payment_date.asc()).all()

    result = []
    for p in payments:
        supplier = db.query(User).filter(User.id == p.supplier_id).first()
        result.append({
            "id":                   p.id,
            "reference":            p.reference,
            "supplier_name":        supplier.name if supplier else "—",
            "supplier_phone":       supplier.phone if supplier else "—",
            "purchase_amount_kes":  p.purchase_amount_kes,
            "paid_amount_kes":      p.paid_amount_kes,
            "outstanding_kes":      p.outstanding_kes,
            "payment_terms":        p.payment_terms,
            "agreed_payment_date":  p.agreed_payment_date,
            "status":               p.status,
            "species":              p.species,
            "quantity_kg":          p.quantity_kg,
            "mpesa_reference":      p.mpesa_reference,
        })

    return {"total": len(result), "payments": result}


@router.post("/supplier-payments/{payment_id}/payout")
def record_payout(
    payment_id:  int,
    payload:     SupplierPayoutRecord,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Record a payout made to a fisher or supplier."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    payment = record_supplier_payout(
        db               = db,
        payment_id       = payment_id,
        amount_paid      = payload.amount_paid,
        payment_method   = payload.payment_method,
        mpesa_reference  = payload.mpesa_reference,
        bank_reference   = payload.bank_reference,
        notes            = payload.notes,
    )

    return {
        "success":         True,
        "reference":       payment.reference,
        "paid_kes":        payment.paid_amount_kes,
        "outstanding_kes": payment.outstanding_kes,
        "status":          payment.status,
    }


@router.get("/supplier-payments/pending")
def pending_supplier_payments(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Get pending supplier payments — what MarineCatch needs to pay out."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    pending = get_pending_supplier_payments(db)
    now     = datetime.now()

    result = []
    for p in pending:
        supplier = db.query(User).filter(User.id == p.supplier_id).first()
        days_until = (p.agreed_payment_date.replace(tzinfo=None) - now).days \
            if p.agreed_payment_date else 0
        result.append({
            "id":                  p.id,
            "reference":           p.reference,
            "supplier_name":       supplier.name if supplier else "—",
            "supplier_phone":      supplier.phone if supplier else "—",
            "outstanding_kes":     p.outstanding_kes,
            "payment_terms":       p.payment_terms,
            "agreed_payment_date": p.agreed_payment_date,
            "days_until_due":      days_until,
            "overdue":             days_until < 0,
            "species":             p.species,
        })

    return {"total": len(result), "pending": result}