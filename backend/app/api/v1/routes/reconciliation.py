# app/api/v1/routes/reconciliation.py
#
# WHY THIS FILE EXISTS:
# Admin endpoints for financial reconciliation.
# Answers the 7 operational trust questions per order.
# Used for daily finance reports and collections follow-up.

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.services.reconciliation_service import (
    reconcile_order,
    reconcile_all_orders,
    get_overdue_credit_orders,
)

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.get("/order/{order_id}")
def get_order_reconciliation(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Full reconciliation for one order.
    Shows: payment status, fisher payout, commission, stock integrity.
    Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return reconcile_order(db, order_id)


@router.get("/report")
def get_reconciliation_report(
    status: Optional[str] = Query(None),
    limit:  int           = Query(100, le=500),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Daily reconciliation report — all orders.
    Filter by order status. Shows clean vs needs_attention counts.
    Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return reconcile_all_orders(db, status=status, limit=limit)


@router.get("/overdue")
def get_overdue_payments(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    All credit sales where payment is overdue.
    Used for collections follow-up.
    Admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return get_overdue_credit_orders(db)