# app/api/v1/routes/sales.py
#
# WHY THIS FILE EXISTS:
# Sales & CRM dashboard data for Muna and future sales team.
# Aggregates leads, pipeline status, source attribution,
# and conversion metrics into a single view.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.models.user import User
from app.models.lead_attribution import LeadAttribution
from app.models.order import Order

router = APIRouter(prefix="/sales", tags=["Sales & CRM"])


@router.get("/pipeline-summary")
def pipeline_summary(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Lead pipeline funnel — new, contacted, qualified, converted."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    leads = db.query(User).filter(User.is_lead == True).all()

    funnel = {
        "new":            0,
        "contacted":      0,
        "qualified":      0,
        "converted":      0,
        "not_interested": 0,
    }
    for l in leads:
        status = l.lead_status or "new"
        if status in funnel:
            funnel[status] += 1

    total = len(leads)
    conversion_rate = round(
        (funnel["converted"] / total * 100), 1
    ) if total > 0 else 0.0

    return {
        "total_leads":     total,
        "funnel":          funnel,
        "conversion_rate": conversion_rate,
    }


@router.get("/leads-by-role")
def leads_by_role(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Breakdown of leads by role — fisher, buyer, supplier, etc."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    leads = db.query(User).filter(User.is_lead == True).all()

    breakdown = {}
    for l in leads:
        role = l.business_name.split(":")[0].strip() if l.business_name else l.role
        role = role.replace("UserRole.", "").lower()
        breakdown[role] = breakdown.get(role, 0) + 1

    return {"breakdown": breakdown}


@router.get("/lead-sources")
def lead_sources(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """
    Lead source breakdown — website, whatsapp, ussd, social channels.
    Uses lead_attributions table for UTM data.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    results = db.query(
        LeadAttribution.utm_source,
        func.count(LeadAttribution.id).label('count')
    ).group_by(LeadAttribution.utm_source).all()

    sources = {r.utm_source or "direct": r.count for r in results}

    # Also count conversions per source
    converted = db.query(
        LeadAttribution.utm_source,
        func.count(LeadAttribution.id).label('count')
    ).filter(
        LeadAttribution.converted_to_user == True
    ).group_by(LeadAttribution.utm_source).all()

    conversions = {r.utm_source or "direct": r.count for r in converted}

    return {
        "sources_total":       sources,
        "sources_converted":   conversions,
    }


@router.get("/leads-timeline")
def leads_timeline(
    days: int = Query(30, le=90),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Daily lead count over the past N days."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    since = datetime.now(timezone.utc) - timedelta(days=days)

    leads = db.query(User).filter(
        User.is_lead == True,
        User.created_at >= since,
    ).all()

    daily_counts = {}
    for l in leads:
        if l.created_at:
            day = l.created_at.strftime("%Y-%m-%d")
            daily_counts[day] = daily_counts.get(day, 0) + 1

    return {"daily_counts": daily_counts, "period_days": days}


@router.get("/recent-leads")
def recent_leads(
    limit:  int = Query(20, le=100),
    status: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Most recent leads, optionally filtered by pipeline status."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    query = db.query(User).filter(User.is_lead == True)
    if status:
        query = query.filter(User.lead_status == status)

    leads = query.order_by(User.created_at.desc()).limit(limit).all()

    result = []
    for l in leads:
        attribution = db.query(LeadAttribution).filter(
            LeadAttribution.lead_phone == l.phone
        ).order_by(LeadAttribution.created_at.desc()).first()

        result.append({
            "id":           l.id,
            "name":         l.name,
            "phone":        l.phone,
            "email":        l.email,
            "location":     l.location,
            "interest":     l.business_name,
            "lead_status":  l.lead_status or "new",
            "assigned_to":  l.assigned_to,
            "utm_source":   attribution.utm_source if attribution else None,
            "created_at":   l.created_at,
            "last_contacted_at": l.last_contacted_at,
        })

    return {"total": len(result), "leads": result}


@router.get("/overview")
def sales_overview(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    """Combined overview stats for the sales dashboard header."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    total_leads     = db.query(User).filter(User.is_lead == True).count()
    total_converted = db.query(User).filter(
        User.is_lead == True,
        User.lead_status == "converted"
    ).count()
    total_active_buyers = db.query(User).filter(
        User.role == "buyer",
        User.is_active == True,
        User.is_lead == False
    ).count()
    total_orders    = db.query(Order).count()

    # Leads this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    leads_this_week = db.query(User).filter(
       User.is_lead == True,
       User.created_at >= week_ago,
    ).count()

    # Unassigned leads needing attention
    unassigned = db.query(User).filter(
        User.is_lead == True,
        User.assigned_to.is_(None),
    ).count()

    return {
        "total_leads":        total_leads,
        "total_converted":    total_converted,
        "total_active_buyers": total_active_buyers,
        "total_orders":       total_orders,
        "leads_this_week":    leads_this_week,
        "unassigned_leads":   unassigned,
    }