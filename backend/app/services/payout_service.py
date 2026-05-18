# app/services/payout_service.py
#
# WHY THIS FILE EXISTS:
# Fisher payout ledger — every payment MarineCatch has made
# to fishers, suppliers, and agents.
#
# This is not just accounting.
# This is financial identity for fishers.
#
# Over time this data becomes:
# - proof of income for bank loans
# - credit scoring for trip financing
# - ESG impact reporting
# - blue economy fund applications
# - cooperative distribution records
#
# Every payout record answers:
# - Who was paid?
# - How much?
# - For which order/catch?
# - When?
# - Via which channel?
# - What was the reference?

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone
from typing import Optional, List

from app.models.payment import PaymentTransaction, PayoutStatus, PaymentStatus
from app.models.order import Order
from app.models.user import User
from app.models.inventory_lot import InventoryLot


# ── FISHER PAYOUT SUMMARY ─────────────────────────────────────────

def get_fisher_payout_summary(
    db:        Session,
    fisher_id: int,
) -> dict:
    """
    Lifetime payout summary for one fisher.
    Shows total earnings, payout history, consistency.

    This becomes the fisher's financial identity on the platform.
    Banks and lenders will eventually use this data.
    """
    fisher = db.query(User).filter(User.id == fisher_id).first()
    if not fisher:
        return {"error": f"Fisher {fisher_id} not found"}

    # All payment transactions where this fisher is the payee
    txns = db.query(PaymentTransaction).filter(
        PaymentTransaction.payee_user_id == fisher_id
    ).all()

    # Also find orders where fisher is the source
    orders_as_fisher = db.query(Order).filter(
        Order.fisherman_id == fisher_id
    ).all()
    order_ids = [o.id for o in orders_as_fisher]

    # Get transactions linked to these orders
    order_txns = db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id.in_(order_ids)
    ).all() if order_ids else []

    # Combine both sources
    all_txn_ids = set([t.id for t in txns] + [t.id for t in order_txns])
    all_txns    = db.query(PaymentTransaction).filter(
        PaymentTransaction.id.in_(all_txn_ids)
    ).all() if all_txn_ids else []

    # Calculate totals
    total_earned_kes   = sum(
        t.supplier_amount or 0 for t in all_txns
        if t.payout_status == PayoutStatus.PAID
    )
    total_pending_kes  = sum(
        t.supplier_amount or 0 for t in all_txns
        if t.payout_status in [PayoutStatus.PENDING, PayoutStatus.PROCESSING]
    )
    total_orders       = len(set(t.order_id for t in all_txns if t.order_id))
    completed_payouts  = sum(1 for t in all_txns if t.payout_status == PayoutStatus.PAID)
    pending_payouts    = sum(1 for t in all_txns if t.payout_status in [
        PayoutStatus.PENDING, PayoutStatus.PROCESSING
    ])

    # Payout history
    history = []
    for txn in sorted(all_txns, key=lambda x: x.created_at or datetime.min, reverse=True):
        order = db.query(Order).filter(Order.id == txn.order_id).first() if txn.order_id else None
        lot   = db.query(InventoryLot).filter(
            InventoryLot.id == order.lot_id
        ).first() if order and order.lot_id else None

        history.append({
            "transaction_reference": txn.transaction_reference,
            "order_id":              txn.order_id,
            "species":               order.species if order else None,
            "quantity_kg":           order.quantity_kg if order else None,
            "lot_number":            lot.lot_number if lot else None,
            "payout_amount_kes":     txn.supplier_amount,
            "payout_status":         txn.payout_status.value,
            "payout_reference":      txn.payout_reference,
            "payout_date":           txn.payout_date,
            "created_at":            txn.created_at,
        })

    # Consistency score — simple ratio of completed vs total
    consistency_score = None
    if total_orders > 0:
        consistency_score = round(completed_payouts / total_orders * 100, 1)

    return {
        "fisher_id":           fisher_id,
        "fisher_name":         fisher.name,
        "fisher_phone":        fisher.phone,
        "settlement_account":  fisher.settlement_account_id,
        "settlement_type":     fisher.settlement_account_type,
        "account_verified":    fisher.settlement_account_verified,
        "summary": {
            "total_earned_kes":   round(total_earned_kes, 2),
            "total_pending_kes":  round(total_pending_kes, 2),
            "total_orders":       total_orders,
            "completed_payouts":  completed_payouts,
            "pending_payouts":    pending_payouts,
            "consistency_score":  consistency_score,
            "note": "Consistency score = % of orders with completed payout"
        },
        "payout_history":      history,
    }


# ── ALL PENDING PAYOUTS ───────────────────────────────────────────

def get_pending_payouts(db: Session) -> List[dict]:
    """
    All payouts that are pending or processing.
    Admin uses this to action outstanding fisher payments.
    """
    pending = db.query(PaymentTransaction).filter(
        and_(
            PaymentTransaction.payout_status.in_([
                PayoutStatus.PENDING,
                PayoutStatus.PROCESSING,
            ]),
            PaymentTransaction.payment_status == PaymentStatus.PAID,
            PaymentTransaction.supplier_amount > 0,
        )
    ).order_by(PaymentTransaction.created_at.asc()).all()

    results = []
    for txn in pending:
        order  = db.query(Order).filter(Order.id == txn.order_id).first()
        fisher = db.query(User).filter(User.id == order.fisherman_id).first() if order else None

        results.append({
            "transaction_reference": txn.transaction_reference,
            "order_id":              txn.order_id,
            "order_status":          order.status.value if order else None,
            "fisher_name":           fisher.name if fisher else None,
            "fisher_phone":          fisher.phone if fisher else None,
            "payout_amount_kes":     txn.supplier_amount,
            "payout_status":         txn.payout_status.value,
            "payout_reference":      txn.payout_reference,
            "days_since_payment":    (
                datetime.now(timezone.utc) - txn.paid_at
            ).days if txn.paid_at else None,
        })

    return results


# ── PAYOUT LEDGER SUMMARY ─────────────────────────────────────────

def get_payout_ledger_summary(db: Session) -> dict:
    """
    Platform-wide payout summary.
    Total paid to fishers, total pending, total failed.
    Used by admin finance dashboard.
    """
    all_txns = db.query(PaymentTransaction).filter(
        PaymentTransaction.supplier_amount > 0
    ).all()

    total_paid       = sum(t.supplier_amount or 0 for t in all_txns if t.payout_status == PayoutStatus.PAID)
    total_pending    = sum(t.supplier_amount or 0 for t in all_txns if t.payout_status in [PayoutStatus.PENDING, PayoutStatus.PROCESSING])
    total_failed     = sum(t.supplier_amount or 0 for t in all_txns if t.payout_status == PayoutStatus.FAILED)
    total_mc_revenue = sum(t.marinecatch_amount or 0 for t in all_txns if t.payment_status == PaymentStatus.PAID)

    return {
        "generated_at":          datetime.now(timezone.utc).isoformat(),
        "total_paid_to_fishers_kes":   round(total_paid, 2),
        "total_pending_kes":           round(total_pending, 2),
        "total_failed_kes":            round(total_failed, 2),
        "total_marinecatch_revenue_kes": round(total_mc_revenue, 2),
        "total_transactions":          len(all_txns),
        "paid_count":     sum(1 for t in all_txns if t.payout_status == PayoutStatus.PAID),
        "pending_count":  sum(1 for t in all_txns if t.payout_status in [PayoutStatus.PENDING, PayoutStatus.PROCESSING]),
        "failed_count":   sum(1 for t in all_txns if t.payout_status == PayoutStatus.FAILED),
    }