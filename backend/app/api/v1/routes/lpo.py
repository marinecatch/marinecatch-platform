# app/api/v1/routes/lpo.py
#
# WHY THIS FILE EXISTS:
# Admin endpoints for institutional LPO order flow.
# Bridges informal procurement with structured digital commerce.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.services.lpo_service import (
    create_lpo_order,
    get_order_by_lpo,
    get_all_lpo_orders,
)
from app.services.lpo_request_service import (
    submit_lpo_request,
    get_pending_lpo_requests,
    fulfill_lpo_request_item,
    reject_lpo_request,
)

router = APIRouter(prefix="/lpo", tags=["LPO Orders"])


class LPOCreate(BaseModel):
    buyer_id:                  int
    lot_id:                    int
    quantity_kg:               float
    lpo_reference:             str
    procurement_officer:       Optional[str]  = None
    expected_fulfillment_date: Optional[str]  = None
    payment_terms_days:        int            = 7
    delivery_address:          Optional[str]  = None
    delivery_distance_km:      Optional[float] = None
    notes:                     Optional[str]  = None


@router.post("/", status_code=201)
def log_lpo_order(
    payload:     LPOCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Admin logs an LPO received from an institutional buyer.
    Creates a confirmed order with LPO reference.
    Stock reserved immediately. Invoice issued separately.

    Example:
    Neptune Hotels sends LPO-2026-0142 for 50kg tuna, Net 7.
    Admin logs it here. Order confirmed. Invoice generated.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    order = create_lpo_order(
        db=                       db,
        buyer_id=                 payload.buyer_id,
        lot_id=                   payload.lot_id,
        quantity_kg=              payload.quantity_kg,
        lpo_reference=            payload.lpo_reference,
        procurement_officer=      payload.procurement_officer,
        expected_fulfillment_date= payload.expected_fulfillment_date,
        payment_terms_days=       payload.payment_terms_days,
        delivery_address=         payload.delivery_address,
        delivery_distance_km=     payload.delivery_distance_km,
        notes=                    payload.notes,
        created_by=               current_user.name,
    )

    return {
        "success":           True,
        "order_id":          order.id,
        "lpo_reference":     order.lpo_reference,
        "buyer_id":          order.buyer_id,
        "species":           order.species,
        "quantity_kg":       order.quantity_kg,
        "total_kes":         order.total_kes,
        "payment_terms_days": order.payment_terms_days,
        "status":            order.status,
        "message":           f"LPO {order.lpo_reference} logged. Order {order.id} confirmed."
    }


@router.get("/")
def list_lpo_orders(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """All orders that came from LPOs. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return get_all_lpo_orders(db)


@router.get("/{lpo_reference}")
def get_lpo_order(
    lpo_reference: str,
    current_user  = Depends(get_current_user),
    db: Session   = Depends(get_db),
):
    """Find an order by LPO reference number."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    order = get_order_by_lpo(db, lpo_reference)
    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"No order found for LPO reference: {lpo_reference}"
        )
    return {
        "order_id":          order.id,
        "lpo_reference":     order.lpo_reference,
        "species":           order.species,
        "quantity_kg":       order.quantity_kg,
        "total_kes":         order.total_kes,
        "payment_terms_days": order.payment_terms_days,
        "status":            order.status,
        "delivery_address":  order.delivery_address,
        "notes":             order.notes,
        "created_at":        order.created_at,
    }
# ── BUYER-FACING LPO REQUEST SUBMISSION ──────────────────────────

class LPORequestItemIn(BaseModel):
    species:     str
    quantity_kg: float
    notes:       Optional[str] = None


class LPORequestCreate(BaseModel):
    lpo_reference:             str
    items:                     List[LPORequestItemIn]
    procurement_officer:       Optional[str] = None
    expected_fulfillment_date: Optional[str] = None
    payment_terms_days:        int = 7
    delivery_address:          Optional[str] = None
    notes:                     Optional[str] = None


@router.post("/requests", status_code=201)
def submit_lpo_request_route(
    payload:      LPORequestCreate,
    current_user = Depends(get_current_user),
    db: Session   = Depends(get_db),
):
    """
    Buyer submits a purchase order request — species and
    quantities only, no lot_id. Admin reviews and assigns
    real inventory lots per item.
    """
    request = submit_lpo_request(
        db=db,
        buyer_id=current_user.id,
        lpo_reference=payload.lpo_reference,
        items=[item.dict() for item in payload.items],
        procurement_officer=payload.procurement_officer,
        expected_fulfillment_date=payload.expected_fulfillment_date,
        payment_terms_days=payload.payment_terms_days,
        delivery_address=payload.delivery_address,
        notes=payload.notes,
    )
    return {
        "success": True,
        "request_id": request.id,
        "status": request.status,
        "message": f"LPO request {request.lpo_reference} submitted for review.",
    }


# ── ADMIN REVIEW OF LPO REQUESTS ──────────────────────────────────

@router.get("/requests/pending")
def list_pending_lpo_requests_route(
    current_user = Depends(get_current_user),
    db: Session   = Depends(get_db),
):
    """Admin: all LPO requests awaiting review."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return {"requests": get_pending_lpo_requests(db)}


class FulfillItemRequest(BaseModel):
    lot_id: int


@router.post("/requests/items/{item_id}/fulfill")
def fulfill_lpo_request_item_route(
    item_id: int,
    payload: FulfillItemRequest,
    current_user = Depends(get_current_user),
    db: Session   = Depends(get_db),
):
    """
    Admin assigns a real inventory lot to one line item of an
    LPO request, creating the actual Order.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return fulfill_lpo_request_item(
        db=db,
        item_id=item_id,
        lot_id=payload.lot_id,
        created_by=current_user.name,
    )


class RejectLPORequest(BaseModel):
    reason: str


@router.post("/requests/{request_id}/reject")
def reject_lpo_request_route(
    request_id: int,
    payload:    RejectLPORequest,
    current_user = Depends(get_current_user),
    db: Session   = Depends(get_db),
):
    """Admin rejects an LPO request outright."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    request = reject_lpo_request(
        db=db,
        request_id=request_id,
        reviewed_by=current_user.name,
        reason=payload.reason,
    )
    return {"success": True, "status": request.status}