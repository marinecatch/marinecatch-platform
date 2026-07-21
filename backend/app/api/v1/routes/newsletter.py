# app/api/v1/routes/newsletter.py
#
# MarineCatch Blue Economy Intelligence — subscriber management.
# Public signup endpoint (no auth) + admin management endpoints.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.models.newsletter_subscriber import NewsletterSubscriber

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class SubscribeRequest(BaseModel):
    email:            str
    name:             Optional[str] = None
    organization:     Optional[str] = None
    stakeholder_type: str = "other"
    country:          Optional[str] = None
    source:           Optional[str] = None
    utm_source:       Optional[str] = None
    utm_campaign:     Optional[str] = None


# ── PUBLIC — SUBSCRIBE ────────────────────────────────────────────

@router.post("/subscribe", status_code=201)
def subscribe(payload: SubscribeRequest, db: Session = Depends(get_db)):
    """
    Public endpoint — no auth required.
    Sign up for MarineCatch Blue Economy Intelligence.
    """
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == payload.email
    ).first()

    if existing:
        return {
            "success": True,
            "message": "You're already subscribed. Thank you!",
            "already_subscribed": True,
        }

    subscriber = NewsletterSubscriber(
        email            = payload.email,
        name             = payload.name,
        organization      = payload.organization,
        stakeholder_type = payload.stakeholder_type,
        country          = payload.country,
        source           = payload.source or "landing_page",
        utm_source       = payload.utm_source,
        utm_campaign     = payload.utm_campaign,
        status           = "confirmed",
        # Note: double opt-in via email confirmation link is a
        # future enhancement once email infrastructure (Brevo/
        # MailerLite) is integrated. For now, direct confirm.
    )
    db.add(subscriber)
    db.commit()

    return {
        "success": True,
        "message": "Thank you for subscribing to MarineCatch Blue Economy Intelligence!",
    }


# ── ADMIN — MANAGEMENT ─────────────────────────────────────────────

@router.get("/subscribers")
def list_subscribers(
    stakeholder_type: Optional[str] = Query(None),
    status:           Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(NewsletterSubscriber)
    if stakeholder_type:
        query = query.filter(NewsletterSubscriber.stakeholder_type == stakeholder_type)
    if status:
        query = query.filter(NewsletterSubscriber.status == status)

    subscribers = query.order_by(NewsletterSubscriber.created_at.desc()).all()

    return {
        "total": len(subscribers),
        "subscribers": [
            {
                "id":               s.id,
                "email":            s.email,
                "name":             s.name,
                "organization":     s.organization,
                "stakeholder_type": s.stakeholder_type,
                "country":          s.country,
                "source":           s.source,
                "utm_source":       s.utm_source,
                "status":           s.status,
                "created_at":       s.created_at,
            } for s in subscribers
        ]
    }


@router.get("/overview")
def newsletter_overview(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Summary stats for the admin dashboard."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    total = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.status == "confirmed"
    ).count()

    breakdown = {}
    subscribers = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.status == "confirmed"
    ).all()
    for s in subscribers:
        key = s.stakeholder_type or "other"
        breakdown[key] = breakdown.get(key, 0) + 1

    week_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    from datetime import timedelta
    week_ago = week_ago - timedelta(days=7)
    new_this_week = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.created_at >= week_ago
    ).count()

    return {
        "total_subscribers":  total,
        "breakdown_by_type":  breakdown,
        "new_this_week":      new_this_week,
    }


@router.delete("/subscribers/{subscriber_id}")
def unsubscribe(
    subscriber_id: int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Admin can mark a subscriber as unsubscribed."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    subscriber = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.id == subscriber_id
    ).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    subscriber.status = "unsubscribed"
    db.commit()
    return {"success": True}