# app/api/v1/routes/whatsapp_messages.py
#
# Admin-facing WhatsApp message log — visibility into
# every conversation without logging into Meta Business Manager.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.models.whatsapp_message import WhatsAppMessage

router = APIRouter(prefix="/whatsapp-log", tags=["WhatsApp Log"])


@router.get("/conversations")
def list_conversations(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """
    List unique phone numbers with their most recent message —
    an inbox-style overview.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    latest_ids = db.query(
        func.max(WhatsAppMessage.id).label('max_id')
    ).group_by(WhatsAppMessage.phone_number).subquery()

    latest_messages = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.id.in_(db.query(latest_ids.c.max_id))
    ).order_by(WhatsAppMessage.created_at.desc()).all()

    return {
        "total": len(latest_messages),
        "conversations": [
            {
                "phone_number":  m.phone_number,
                "sender_name":   m.sender_name,
                "user_role":     m.user_role,
                "last_message":  m.message_text,
                "direction":     m.direction,
                "last_activity": m.created_at,
            } for m in latest_messages
        ]
    }


@router.get("/conversation/{phone_number}")
def get_conversation(
    phone_number: str,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Full message history for one phone number."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    messages = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.phone_number == phone_number
    ).order_by(WhatsAppMessage.created_at.asc()).all()

    return {
        "phone_number": phone_number,
        "total": len(messages),
        "messages": [
            {
                "direction":    m.direction,
                "message_text": m.message_text,
                "button_id":    m.button_id,
                "created_at":   m.created_at,
            } for m in messages
        ]
    }


@router.get("/overview")
def whatsapp_overview(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Summary stats for the admin dashboard."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    total_messages = db.query(WhatsAppMessage).count()
    total_conversations = db.query(
        func.count(func.distinct(WhatsAppMessage.phone_number))
    ).scalar()
    inbound = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.direction == "inbound"
    ).count()
    outbound = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.direction == "outbound"
    ).count()

    return {
        "total_messages":       total_messages,
        "total_conversations":  total_conversations,
        "inbound":              inbound,
        "outbound":             outbound,
    }