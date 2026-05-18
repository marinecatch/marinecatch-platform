# app/api/v1/routes/documents.py
#
# WHY THIS FILE EXISTS:
# Document generation endpoints.
# Invoice, receipt, delivery note for every order.
# Foundation for full commercial documentation infrastructure.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.services.document_service import (
    generate_invoice,
    generate_receipt,
    generate_delivery_note,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/invoice/{order_id}")
def get_invoice(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Generate invoice for an order.
    Admin or the buyer for that order.
    """
    result = generate_invoice(db, order_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/receipt/{order_id}")
def get_receipt(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Generate payment receipt after payment confirmed.
    """
    result = generate_receipt(db, order_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/delivery-note/{order_id}")
def get_delivery_note(
    order_id:    int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """
    Generate delivery note for dispatch.
    Travels with the fish to the buyer.
    """
    result = generate_delivery_note(db, order_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result