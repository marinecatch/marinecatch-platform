# app/services/lpo_request_service.py
#
# WHY THIS FILE EXISTS:
# Buyer-facing front door to the existing LPO pipeline.
# Buyers submit a request (species + quantities, their own
# PO reference, payment terms) without picking a lot_id —
# admin reviews, assigns real inventory lots item-by-item,
# and converts each line into a real Order using the EXISTING,
# unmodified create_lpo_order() in lpo_service.py.

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import Optional, List

from app.models.lpo_request import LPORequest, LPORequestItem
from app.models.user import User
from app.services.lpo_service import create_lpo_order


def submit_lpo_request(
    db: Session,
    buyer_id: int,
    lpo_reference: str,
    items: List[dict],
    # each item: {"species": str, "quantity_kg": float, "notes": Optional[str]}
    procurement_officer: Optional[str] = None,
    expected_fulfillment_date: Optional[str] = None,
    payment_terms_days: int = 7,
    delivery_address: Optional[str] = None,
    notes: Optional[str] = None,
) -> LPORequest:
    """Buyer submits a purchase order request for admin review."""
    buyer = db.query(User).filter(User.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    if not items:
        raise HTTPException(status_code=400, detail="At least one item is required")

    request = LPORequest(
        buyer_id=buyer_id,
        lpo_reference=lpo_reference,
        procurement_officer=procurement_officer,
        expected_fulfillment_date=expected_fulfillment_date,
        payment_terms_days=payment_terms_days,
        delivery_address=delivery_address,
        notes=notes,
        status="pending",
    )
    db.add(request)
    db.flush()  # get request.id before adding items

    for item in items:
        db.add(LPORequestItem(
            lpo_request_id=request.id,
            species=item["species"],
            quantity_kg=item["quantity_kg"],
            notes=item.get("notes"),
        ))

    db.commit()
    db.refresh(request)
    return request


def get_pending_lpo_requests(db: Session, limit: int = 50) -> list:
    """Admin view: all LPO requests awaiting review."""
    requests = db.query(LPORequest).filter(
        LPORequest.status == "pending"
    ).order_by(LPORequest.created_at.desc()).limit(limit).all()

    results = []
    for req in requests:
        buyer = db.query(User).filter(User.id == req.buyer_id).first()
        results.append({
            "id": req.id,
            "lpo_reference": req.lpo_reference,
            "buyer_name": buyer.name if buyer else None,
            "buyer_id": req.buyer_id,
            "procurement_officer": req.procurement_officer,
            "expected_fulfillment_date": req.expected_fulfillment_date,
            "payment_terms_days": req.payment_terms_days,
            "delivery_address": req.delivery_address,
            "notes": req.notes,
            "created_at": req.created_at,
            "items": [
                {
                    "id": item.id,
                    "species": item.species,
                    "quantity_kg": item.quantity_kg,
                    "notes": item.notes,
                    "fulfilled_lot_id": item.fulfilled_lot_id,
                    "resulting_order_id": item.resulting_order_id,
                }
                for item in req.items
            ],
        })
    return results


def fulfill_lpo_request_item(
    db: Session,
    item_id: int,
    lot_id: int,
    created_by: str,
) -> dict:
    """
    Admin assigns a real inventory lot to one line of an LPO
    request, creating the real Order via the existing,
    unmodified create_lpo_order().
    """
    item = db.query(LPORequestItem).filter(LPORequestItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="LPO request item not found")

    if item.resulting_order_id:
        raise HTTPException(status_code=400, detail="This item has already been fulfilled")

    request = item.lpo_request

    order = create_lpo_order(
        db=db,
        buyer_id=request.buyer_id,
        lot_id=lot_id,
        quantity_kg=item.quantity_kg,
        lpo_reference=request.lpo_reference,
        procurement_officer=request.procurement_officer,
        expected_fulfillment_date=request.expected_fulfillment_date,
        payment_terms_days=request.payment_terms_days,
        delivery_address=request.delivery_address,
        notes=item.notes or request.notes,
        created_by=created_by,
    )

    item.fulfilled_lot_id = lot_id
    item.resulting_order_id = order.id
    db.commit()

    # If every item on this request now has a resulting order, mark it approved
    remaining = db.query(LPORequestItem).filter(
        LPORequestItem.lpo_request_id == request.id,
        LPORequestItem.resulting_order_id.is_(None),
    ).count()
    if remaining == 0:
        request.status = "approved"
        request.reviewed_by = created_by
        request.reviewed_at = datetime.now(timezone.utc)
        db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "order_total_kes": order.total_kes,
        "request_status": request.status,
    }


def reject_lpo_request(
    db: Session,
    request_id: int,
    reviewed_by: str,
    reason: str,
) -> LPORequest:
    """Admin rejects an LPO request outright — no items fulfilled."""
    request = db.query(LPORequest).filter(LPORequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="LPO request not found")

    request.status = "rejected"
    request.reviewed_by = reviewed_by
    request.reviewed_at = datetime.now(timezone.utc)
    request.rejection_reason = reason
    db.commit()
    db.refresh(request)
    return request