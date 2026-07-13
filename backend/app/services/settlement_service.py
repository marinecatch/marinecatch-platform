# app/services/settlement_service.py
#
# WHY THIS FILE EXISTS:
# Core settlement logic for MarineCatch trade operations.
#
# MarineCatch sits between fishers/suppliers and buyers.
# This service manages:
# 1. Trade receivables — what buyers owe MarineCatch
# 2. Supplier payments — what MarineCatch owes fishers/suppliers
# 3. Working capital position — the gap between the two
# 4. Overdue detection and alerts
# 5. Credit score updates for buyers

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Optional
import secrets

from app.models.trade_receivable import TradeReceivable, ReceivableStatus
from app.models.supplier_payment import SupplierPayment, SupplierPaymentStatus
from app.models.user import User


# ── INVOICE NUMBER GENERATOR ──────────────────────────────────────

def generate_invoice_number(db: Session) -> str:
    """Generate MC-INV-YYYYMMDD-NNNN format invoice number."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = db.query(TradeReceivable).filter(
        TradeReceivable.invoice_number.like(f"MC-INV-{today}-%")
    ).count()
    return f"MC-INV-{today}-{str(count + 1).zfill(4)}"


def generate_payment_reference(db: Session) -> str:
    """Generate MC-PAY-YYYYMMDD-NNNN format payment reference."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = db.query(SupplierPayment).filter(
        SupplierPayment.reference.like(f"MC-PAY-{today}-%")
    ).count()
    return f"MC-PAY-{today}-{str(count + 1).zfill(4)}"


# ── PAYMENT TERMS TO DAYS ─────────────────────────────────────────

TERMS_TO_DAYS = {
    "immediate": 0,
    "net_3":     3,
    "net_7":     7,
    "net_14":    14,
    "net_30":    30,
    "net_45":    45,
}


def calculate_due_date(payment_terms: str, from_date: datetime = None) -> datetime:
    """Calculate due date from payment terms."""
    base = from_date or datetime.now(timezone.utc)
    days = TERMS_TO_DAYS.get(payment_terms, 30)
    return base + timedelta(days=days)


# ── TRADE RECEIVABLES ─────────────────────────────────────────────

def create_receivable(
    db:               Session,
    buyer_id:         int,
    gross_amount_kes: float,
    payment_terms:    str,
    order_id:         Optional[int] = None,
    species:          Optional[str] = None,
    quantity_kg:      Optional[float] = None,
    delivery_location: Optional[str] = None,
    received_by:      Optional[str] = None,
    created_by:       Optional[str] = None,
    notes:            Optional[str] = None,
) -> TradeReceivable:
    """
    Create a trade receivable when MarineCatch delivers to a buyer.
    Called after delivery confirmation.
    """
    invoice_number = generate_invoice_number(db)
    now            = datetime.now(timezone.utc)
    due_date       = calculate_due_date(payment_terms, now)

    receivable = TradeReceivable(
        invoice_number      = invoice_number,
        order_id            = order_id,
        buyer_id            = buyer_id,
        gross_amount_kes    = gross_amount_kes,
        vat_kes             = 0.0,
        total_amount_kes    = gross_amount_kes,
        paid_amount_kes     = 0.0,
        outstanding_kes     = gross_amount_kes,
        payment_terms       = payment_terms,
        delivery_date       = now,
        invoice_date        = now,
        due_date            = due_date,
        status              = ReceivableStatus.INVOICED,
        species             = species,
        quantity_kg         = quantity_kg,
        delivery_location   = delivery_location,
        received_by         = received_by,
        created_by          = created_by,
        notes               = notes,
    )
    db.add(receivable)
    db.commit()
    db.refresh(receivable)
    return receivable


def record_payment(
    db:               Session,
    receivable_id:    int,
    amount_paid:      float,
    payment_method:   str,
    payment_reference: Optional[str] = None,
    notes:            Optional[str] = None,
) -> TradeReceivable:
    """
    Record a payment received from a buyer.
    Updates outstanding balance and status.
    """
    receivable = db.query(TradeReceivable).filter(
        TradeReceivable.id == receivable_id
    ).first()

    if not receivable:
        raise ValueError(f"Receivable {receivable_id} not found")

    receivable.paid_amount_kes  += amount_paid
    receivable.outstanding_kes   = receivable.total_amount_kes - receivable.paid_amount_kes
    receivable.payment_method    = payment_method
    receivable.payment_reference = payment_reference
    receivable.payment_notes     = notes

    if receivable.outstanding_kes <= 0:
        receivable.status    = ReceivableStatus.PAID
        receivable.paid_date = datetime.now(timezone.utc)
    elif receivable.paid_amount_kes > 0:
        receivable.status = ReceivableStatus.PARTIALLY_PAID

    db.commit()
    db.refresh(receivable)

    # Update buyer credit score
    _update_buyer_credit_score(db, receivable.buyer_id)

    # Update compliance profile trust score
    try:
        from app.services.member_id_service import update_trust_score
        update_trust_score(db, receivable.buyer_id)
    except Exception as e:
        print(f"Trust score update failed: {e}")

    return receivable


def get_overdue_receivables(db: Session) -> list:
    """Get all overdue receivables — past due date and unpaid."""
    now = datetime.now(timezone.utc)
    return db.query(TradeReceivable).filter(
        TradeReceivable.due_date < now,
        TradeReceivable.status.in_([
            ReceivableStatus.INVOICED,
            ReceivableStatus.PARTIALLY_PAID,
        ])
    ).order_by(TradeReceivable.due_date.asc()).all()


def mark_overdue(db: Session) -> int:
    """Mark all past-due invoices as overdue. Returns count updated."""
    now      = datetime.now(timezone.utc)
    overdue  = db.query(TradeReceivable).filter(
        TradeReceivable.due_date < now,
        TradeReceivable.status.in_([
            ReceivableStatus.INVOICED,
            ReceivableStatus.PARTIALLY_PAID,
        ])
    ).all()

    for r in overdue:
        r.status = ReceivableStatus.OVERDUE

    db.commit()
    return len(overdue)


# ── SUPPLIER PAYMENTS ─────────────────────────────────────────────

def create_supplier_payment(
    db:                   Session,
    supplier_id:          int,
    purchase_amount_kes:  float,
    payment_terms:        str,
    lot_id:               Optional[int] = None,
    order_id:             Optional[int] = None,
    species:              Optional[str] = None,
    quantity_kg:          Optional[float] = None,
    created_by:           Optional[str] = None,
    notes:                Optional[str] = None,
) -> SupplierPayment:
    """
    Create a supplier payment record when MarineCatch receives from a fisher/supplier.
    """
    reference    = generate_payment_reference(db)
    now          = datetime.now(timezone.utc)
    payment_date = calculate_due_date(payment_terms, now)

    payment = SupplierPayment(
        reference           = reference,
        lot_id              = lot_id,
        order_id            = order_id,
        supplier_id         = supplier_id,
        purchase_amount_kes = purchase_amount_kes,
        paid_amount_kes     = 0.0,
        outstanding_kes     = purchase_amount_kes,
        payment_terms       = payment_terms,
        delivery_date       = now,
        agreed_payment_date = payment_date,
        status              = SupplierPaymentStatus.PENDING,
        species             = species,
        quantity_kg         = quantity_kg,
        created_by          = created_by,
        notes               = notes,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


async def record_supplier_payout(
    db:               Session,
    payment_id:       int,
    amount_paid:      float,
    payment_method:   str,
    mpesa_reference:  Optional[str] = None,
    bank_reference:   Optional[str] = None,
    notes:            Optional[str] = None,
) -> SupplierPayment:
    """Record a payout made to a fisher or supplier."""
    payment = db.query(SupplierPayment).filter(
        SupplierPayment.id == payment_id
    ).first()

    if not payment:
        raise ValueError(f"Supplier payment {payment_id} not found")

    payment.paid_amount_kes += amount_paid
    payment.outstanding_kes  = payment.purchase_amount_kes - payment.paid_amount_kes
    payment.payment_method   = payment_method
    payment.mpesa_reference  = mpesa_reference
    payment.bank_reference   = bank_reference
    payment.notes            = notes

    if payment.outstanding_kes <= 0:
        payment.status    = SupplierPaymentStatus.PAID
        payment.paid_date = datetime.now(timezone.utc)
    elif payment.paid_amount_kes > 0:
        payment.status = SupplierPaymentStatus.PARTIAL

    db.commit()
    db.refresh(payment)

    # Update supplier's compliance profile stats and trust score
    try:
        from app.models.compliance_profile import ComplianceProfile
        profile = db.query(ComplianceProfile).filter(
            ComplianceProfile.user_id == payment.supplier_id
        ).first()
        if profile and payment.status == SupplierPaymentStatus.PAID:
            profile.total_transactions = (profile.total_transactions or 0) + 1
            profile.total_volume_kg    = (profile.total_volume_kg or 0.0) + (payment.quantity_kg or 0.0)
            profile.total_value_kes    = (profile.total_value_kes or 0.0) + payment.purchase_amount_kes
            db.commit()

            # KRA compliance prompt — unlock institutional buyers at KES 500K
            KRA_PROMPT_THRESHOLD = 500000.0
            if (profile.total_value_kes >= KRA_PROMPT_THRESHOLD
                    and not profile.kra_verified):
                try:
                    from app.services.whatsapp_service import send_text
                    from app.models.user import User as UserModel
                    supplier = db.query(UserModel).filter(
                        UserModel.id == payment.supplier_id
                    ).first()
                    if supplier and supplier.phone:
                        await send_text(
                            supplier.phone,
                            f"🎉 *Congratulations {supplier.name}!*\n\n"
                            f"You've sold over KES {int(profile.total_value_kes):,} "
                            f"through MarineCatch Africa.\n\n"
                            f"💼 *Unlock Bigger Buyers*\n"
                            f"Add your KRA PIN to qualify for hotels, "
                            f"processors, and export buyers who need "
                            f"tax-compliant suppliers.\n\n"
                            f"Reply with:\n"
                            f"*KRA A123456789B*\n"
                            f"(replace with your actual KRA PIN)\n\n"
                            f"MarineCatch Africa 🐟"
                        )
                except Exception as notify_err:
                    print(f"KRA prompt notification failed: {notify_err}")

        from app.services.member_id_service import update_trust_score
        update_trust_score(db, payment.supplier_id)
    except Exception as e:
        print(f"Trust score update failed: {e}")

    return payment


def get_pending_supplier_payments(db: Session) -> list:
    """Get all pending supplier payments — what MarineCatch owes."""
    return db.query(SupplierPayment).filter(
        SupplierPayment.status.in_([
            SupplierPaymentStatus.PENDING,
            SupplierPaymentStatus.SCHEDULED,
            SupplierPaymentStatus.PARTIAL,
        ])
    ).order_by(SupplierPayment.agreed_payment_date.asc()).all()


# ── WORKING CAPITAL POSITION ──────────────────────────────────────

def get_working_capital_position(db: Session) -> dict:
    """
    Calculate MarineCatch's current working capital position.
    Shows: what buyers owe us vs what we owe suppliers.
    The gap is our working capital requirement.
    """
    # Total receivables (what buyers owe us)
    receivables = db.query(
        func.sum(TradeReceivable.outstanding_kes)
    ).filter(
        TradeReceivable.status.in_([
            ReceivableStatus.INVOICED,
            ReceivableStatus.PARTIALLY_PAID,
            ReceivableStatus.OVERDUE,
        ])
    ).scalar() or 0.0

    # Overdue receivables
    overdue_receivables = db.query(
        func.sum(TradeReceivable.outstanding_kes)
    ).filter(
        TradeReceivable.status == ReceivableStatus.OVERDUE
    ).scalar() or 0.0

    # Total payables (what we owe suppliers)
    payables = db.query(
        func.sum(SupplierPayment.outstanding_kes)
    ).filter(
        SupplierPayment.status.in_([
            SupplierPaymentStatus.PENDING,
            SupplierPaymentStatus.SCHEDULED,
            SupplierPaymentStatus.PARTIAL,
            SupplierPaymentStatus.OVERDUE,
        ])
    ).scalar() or 0.0

    # Total invoiced (all time)
    total_invoiced = db.query(
        func.sum(TradeReceivable.total_amount_kes)
    ).scalar() or 0.0

    # Total collected (all time)
    total_collected = db.query(
        func.sum(TradeReceivable.paid_amount_kes)
    ).scalar() or 0.0

    # Total paid to suppliers (all time)
    total_paid_suppliers = db.query(
        func.sum(SupplierPayment.paid_amount_kes)
    ).scalar() or 0.0

    return {
        "receivables": {
            "outstanding_kes":  round(receivables, 0),
            "overdue_kes":      round(overdue_receivables, 0),
            "total_invoiced_kes": round(total_invoiced, 0),
            "total_collected_kes": round(total_collected, 0),
        },
        "payables": {
            "outstanding_kes":      round(payables, 0),
            "total_paid_suppliers": round(total_paid_suppliers, 0),
        },
        "working_capital": {
            "gap_kes": round(payables - receivables, 0),
            # Positive = you need more cash (owe more than you're owed)
            # Negative = you're in good shape (owed more than you owe)
            "net_position_kes": round(receivables - payables, 0),
        }
    }


# ── BUYER CREDIT SCORING ──────────────────────────────────────────

def _update_buyer_credit_score(db: Session, buyer_id: int):
    """
    Auto-update buyer credit score after each payment.
    Based on: on-time payment rate, total orders, outstanding balance.
    """
    buyer = db.query(User).filter(User.id == buyer_id).first()
    if not buyer:
        return

    receivables = db.query(TradeReceivable).filter(
        TradeReceivable.buyer_id == buyer_id
    ).all()

    if not receivables:
        return

    total           = len(receivables)
    paid_on_time    = sum(1 for r in receivables
                         if r.status == ReceivableStatus.PAID
                         and r.paid_date and r.due_date
                         and r.paid_date <= r.due_date)
    overdue_count   = sum(1 for r in receivables
                         if r.status == ReceivableStatus.OVERDUE)
    outstanding     = sum(r.outstanding_kes for r in receivables
                         if r.status in [
                             ReceivableStatus.INVOICED,
                             ReceivableStatus.PARTIALLY_PAID,
                             ReceivableStatus.OVERDUE
                         ])

    on_time_rate = (paid_on_time / total) if total > 0 else 0.0

    # Score logic
    if total < 2:
        score = "unrated"
    elif overdue_count > 2 or on_time_rate < 0.5:
        score = "high_risk"
    elif overdue_count > 0 or on_time_rate < 0.8:
        score = "medium_risk"
    else:
        score = "low_risk"

    buyer.credit_score              = score
    buyer.on_time_payment_rate      = round(on_time_rate * 100, 1)
    buyer.total_orders_count        = total
    buyer.outstanding_balance_kes   = round(outstanding, 0)

    db.commit()