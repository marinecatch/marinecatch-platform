# app/api/v1/routes/payouts.py
#
# WHY THIS FILE EXISTS:
# Fisher payout ledger endpoints.
# Financial identity for fishers.
# Admin oversight for all platform payouts.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.services.payout_service import (
    get_fisher_payout_summary,
    get_pending_payouts,
    get_payout_ledger_summary,
)

router = APIRouter(prefix="/payouts", tags=["Payouts"])


@router.get("/fisher/{fisher_id}")
def fisher_payout_summary(
    fisher_id:   int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Lifetime payout summary for one fisher.
    Fisher can see their own. Admin can see any.

    Shows: total earned, pending, payout history, consistency score.
    This becomes the fisher's financial identity on the platform.
    """
    if current_user.role != "admin" and current_user.id != fisher_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return get_fisher_payout_summary(db, fisher_id)


@router.get("/pending")
def pending_payouts(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    All payouts pending or processing.
    Admin uses this to action outstanding fisher payments.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return get_pending_payouts(db)


@router.get("/ledger")
def payout_ledger(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Platform-wide payout summary.
    Total paid to fishers, pending, failed, MarineCatch revenue.
    Admin finance dashboard.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return get_payout_ledger_summary(db)