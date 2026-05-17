# app/services/reconciliation_service.py
#
# WHY THIS FILE EXISTS:
# Reconciliation is the source of truth for operational trust.
# Every order should be answerable:
#
# - Was buyer charged?
# - Was order fulfilled?
# - Was fisher paid?
# - Did MarineCatch retain correct commission?
# - Is payment overdue?
# - Did callback fail?
# - Was stock released correctly?
#
# This service answers all seven questions per order.
# Used by admin dashboard and daily finance reports.

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
from typing import Optional, List

from app.models.order import Order, OrderStatus
from app.models.payment import PaymentTransaction, PaymentStatus, PayoutStatus
from app.models.inventory_lot import InventoryLot, LotStatus
from app.models.user import User


# ── SINGLE ORDER RECONCILIATION ───────────────────────────────────

def reconcile_order(db: Session, order_id: int) -> dict:
    """
    Full reconciliation record for one order.
    Answers all 7 operational trust questions.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}

    # Get payment transaction
    txn = db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id == order_id
    ).order_by(PaymentTransaction.created_at.desc()).first()

    # Get inventory lot
    lot = db.query(InventoryLot).filter(
        InventoryLot.id == order.lot_id
    ).first() if order.lot_id else None

    # Get buyer
    buyer = db.query(User).filter(
        User.id == order.buyer_id
    ).first()

    # Get fisher
    fisher = db.query(User).filter(
        User.id == order.fisherman_id
    ).first() if order.fisherman_id else None

    now = datetime.now(timezone.utc)

    # ── QUESTION 1: Was buyer charged? ────────────────────────
    buyer_charged = txn is not None and txn.payment_status == PaymentStatus.PAID
    buyer_charge_status = txn.payment_status.value if txn else "no_payment_initiated"

    # ── QUESTION 2: Was order fulfilled? ──────────────────────
    fulfilled_statuses = [
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED
    ]
    order_fulfilled = order.status in fulfilled_statuses

    # ── QUESTION 3: Was fisher paid? ──────────────────────────
    fisher_paid = txn is not None and txn.payout_status == PayoutStatus.PAID
    fisher_payout_status = txn.payout_status.value if txn else "not_applicable"

    # ── QUESTION 4: Did MarineCatch retain correct commission? ─
    commission_correct = None
    commission_variance = None
    if txn and txn.commission_amount and order.platform_fee_kes:
        expected = order.platform_fee_kes
        actual   = txn.commission_amount
        commission_variance = round(actual - expected, 2)
        commission_correct  = abs(commission_variance) < 1.0

    # ── QUESTION 5: Is payment overdue? ───────────────────────
    payment_overdue = False
    overdue_days    = None
    if order.reserved_until and not buyer_charged:
        if now > order.reserved_until.replace(tzinfo=timezone.utc) if order.reserved_until.tzinfo is None else now > order.reserved_until:
            payment_overdue = True
            delta = now - order.reserved_until
            overdue_days = delta.days

    # Credit sale overdue check
    if txn and txn.is_credit_sale and txn.credit_due_date:
        due = txn.credit_due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if now > due and not buyer_charged:
            payment_overdue = True
            overdue_days = (now - due).days

    # ── QUESTION 6: Did callback fail? ────────────────────────
    callback_failed = False
    last_payment_attempt = None
    if txn:
        last_payment_attempt = txn.updated_at or txn.created_at
        if txn.payment_status in [PaymentStatus.FAILED, PaymentStatus.EXPIRED]:
            callback_failed = True

    # ── QUESTION 7: Was stock released correctly? ─────────────
    stock_correct = True
    stock_issue   = None
    if lot:
        if order.status == OrderStatus.CANCELLED:
            # Stock should be available if order cancelled
            if lot.lot_status not in [LotStatus.AVAILABLE, LotStatus.PARTIALLY_SOLD]:
                stock_correct = False
                stock_issue   = f"Order cancelled but lot status is {lot.lot_status.value}"
        elif order.status in [OrderStatus.DELIVERED, OrderStatus.COMPLETED]:
            # Stock should be sold or partially sold
            if lot.lot_status == LotStatus.AVAILABLE and lot.reserved_kg > 0:
                stock_correct = False
                stock_issue   = "Order delivered but stock still showing reserved"

    # ── RECONCILIATION STATUS ─────────────────────────────────
    issues = []
    if not buyer_charged and order.status not in [
        OrderStatus.PENDING_PAYMENT, OrderStatus.CANCELLED
    ]:
        issues.append("payment_not_confirmed")
    if not fisher_paid and order.status in [
        OrderStatus.DELIVERED, OrderStatus.COMPLETED
    ]:
        issues.append("fisher_payout_pending")
    if payment_overdue:
        issues.append("payment_overdue")
    if callback_failed:
        issues.append("payment_failed_or_expired")
    if not stock_correct:
        issues.append("stock_discrepancy")
    if commission_correct is False:
        issues.append("commission_variance")

    reconciliation_status = "clean" if not issues else "needs_attention"

    return {
        "order_id":              order_id,
        "reconciliation_status": reconciliation_status,
        "issues":                issues,
        "order": {
            "status":        order.status.value,
            "species":       order.species,
            "quantity_kg":   order.quantity_kg,
            "total_kes":     order.total_kes,
            "created_at":    order.created_at,
            "updated_at":    order.updated_at,
        },
        "buyer": {
            "name":          buyer.name if buyer else None,
            "charged":       buyer_charged,
            "charge_status": buyer_charge_status,
            "amount_kes":    txn.total_amount if txn else None,
        },
        "payment": {
            "reference":          txn.transaction_reference if txn else None,
            "method":             txn.payment_method.value if txn else None,
            "status":             buyer_charge_status,
            "paid_at":            txn.paid_at if txn else None,
            "last_attempt":       last_payment_attempt,
            "callback_failed":    callback_failed,
            "is_credit_sale":     txn.is_credit_sale if txn else False,
            "credit_due_date":    txn.credit_due_date if txn else None,
            "payment_overdue":    payment_overdue,
            "overdue_days":       overdue_days,
            "mpesa_receipt":      txn.mpesa_receipt_number if txn else None,
        },
        "fisher": {
            "name":           fisher.name if fisher else None,
            "paid":           fisher_paid,
            "payout_status":  fisher_payout_status,
            "payout_amount":  txn.supplier_amount if txn else None,
            "payout_ref":     txn.payout_reference if txn else None,
            "payout_date":    txn.payout_date if txn else None,
        },
        "marinecatch": {
            "commission_kes":    txn.commission_amount if txn else None,
            "expected_kes":      order.platform_fee_kes,
            "commission_correct": commission_correct,
            "variance_kes":      commission_variance,
            "retained_amount":   txn.marinecatch_amount if txn else None,
        },
        "inventory": {
            "lot_number":    lot.lot_number if lot else None,
            "lot_status":    lot.lot_status.value if lot else None,
            "stock_correct": stock_correct,
            "stock_issue":   stock_issue,
        },
    }


# ── BULK RECONCILIATION ───────────────────────────────────────────

def reconcile_all_orders(
    db:     Session,
    status: Optional[str] = None,
    limit:  int = 100,
) -> dict:
    """
    Reconcile all orders or filter by status.
    Used for daily finance report.
    """
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).limit(limit).all()

    results      = []
    clean_count  = 0
    issues_count = 0

    for order in orders:
        rec = reconcile_order(db, order.id)
        results.append(rec)
        if rec.get("reconciliation_status") == "clean":
            clean_count += 1
        else:
            issues_count += 1

    return {
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "total_orders":  len(results),
        "clean":         clean_count,
        "needs_attention": issues_count,
        "orders":        results,
    }


# ── OVERDUE CREDIT ORDERS ─────────────────────────────────────────

def get_overdue_credit_orders(db: Session) -> List[dict]:
    """
    Find all credit sales where payment is overdue.
    Used for collections follow-up.
    """
    now = datetime.now(timezone.utc)

    overdue_txns = db.query(PaymentTransaction).filter(
        and_(
            PaymentTransaction.is_credit_sale == True,
            PaymentTransaction.credit_due_date <= now,
            PaymentTransaction.payment_status != PaymentStatus.PAID,
        )
    ).all()

    results = []
    for txn in overdue_txns:
        order = db.query(Order).filter(Order.id == txn.order_id).first()
        buyer = db.query(User).filter(User.id == txn.payer_user_id).first()
        due   = txn.credit_due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        overdue_days = (now - due).days

        results.append({
            "order_id":       txn.order_id,
            "buyer_name":     buyer.name if buyer else None,
            "buyer_phone":    buyer.phone if buyer else None,
            "amount_kes":     txn.total_amount,
            "due_date":       txn.credit_due_date,
            "overdue_days":   overdue_days,
            "reference":      txn.transaction_reference,
            "order_status":   order.status.value if order else None,
        })

    return sorted(results, key=lambda x: x["overdue_days"], reverse=True)