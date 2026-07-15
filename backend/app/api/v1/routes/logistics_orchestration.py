# app/api/v1/routes/logistics_orchestration.py
#
# API endpoints for the logistics orchestration layer —
# partners, storage nodes, coolers, transport jobs, custody,
# and exceptions.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.models.logistics_partner import LogisticsPartner
from app.models.storage_node import StorageNode
from app.models.cooler_asset import CoolerAsset
from app.models.transport_job import TransportJob
from app.models.custody_event import CustodyEvent
from app.models.logistics_exception import LogisticsException
from app.services.logistics_orchestration_service import (
    create_partner,
    get_partners_by_coverage,
    create_storage_node,
    reserve_storage_space,
    release_storage_space,
    register_cooler,
    update_cooler_status,
    get_available_coolers,
    create_transport_job,
    update_job_status,
    get_active_jobs,
    record_custody_event,
    get_custody_chain,
    report_exception,
    resolve_exception,
    get_open_exceptions,
    get_logistics_network_summary,
)

router = APIRouter(prefix="/logistics-network", tags=["Logistics Orchestration"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class PartnerCreate(BaseModel):
    name: str
    partner_type: str
    contact_phone: Optional[str] = None
    contact_person: Optional[str] = None
    coverage_areas: Optional[str] = None
    cold_chain_capable: bool = False
    max_payload_kg: Optional[float] = None
    commission_model: str = "flat_fee"
    base_rate_kes: Optional[float] = None
    per_km_rate_kes: Optional[float] = None
    per_kg_rate_kes: Optional[float] = None
    notes: Optional[str] = None


class StorageNodeCreate(BaseModel):
    name: str
    operator_name: str
    location: str
    capacity_kg: float
    power_source: Optional[str] = None
    has_ice_machine: bool = False
    cost_model: str = "informal"
    cost_rate_kes: Optional[float] = None
    access_terms: Optional[str] = None
    partner_id: Optional[int] = None


class CoolerCreate(BaseModel):
    capacity_kg: float
    purchase_value_kes: Optional[float] = None


class CoolerStatusUpdate(BaseModel):
    status: str
    current_holder: Optional[str] = None
    current_location: Optional[str] = None
    incident_notes: Optional[str] = None


class TransportJobCreate(BaseModel):
    pickup_location: str
    destination_location: str
    job_type: str
    partner_id: Optional[int] = None
    cooler_asset_id: Optional[int] = None
    order_id: Optional[int] = None
    lot_id: Optional[int] = None
    shipment_id: Optional[int] = None
    sequence_number: int = 1
    scheduled_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    cost_kes: Optional[float] = None
    tracking_reference: Optional[str] = None
    notes: Optional[str] = None


class JobStatusUpdate(BaseModel):
    status: str
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    temperature_at_delivery: Optional[float] = None


class CustodyEventCreate(BaseModel):
    event_type: str
    from_party: Optional[str] = None
    to_party: Optional[str] = None
    location: Optional[str] = None
    lot_id: Optional[int] = None
    transport_job_id: Optional[int] = None
    condition_notes: Optional[str] = None


class ExceptionCreate(BaseModel):
    transport_job_id: int
    exception_type: str
    description: str
    severity: str = "medium"


class ExceptionResolve(BaseModel):
    resolution_notes: str


# ── NETWORK SUMMARY ────────────────────────────────────────────────

@router.get("/summary")
def network_summary(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return get_logistics_network_summary(db)


# ── PARTNERS ───────────────────────────────────────────────────────

@router.post("/partners", status_code=201)
def api_create_partner(
    payload: PartnerCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    partner = create_partner(db, **payload.dict())
    return {"success": True, "id": partner.id, "name": partner.name}


@router.get("/partners")
def list_partners(
    partner_type: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    query = db.query(LogisticsPartner)
    if partner_type:
        query = query.filter(LogisticsPartner.partner_type == partner_type)
    partners = query.order_by(LogisticsPartner.name.asc()).all()
    return {
        "total": len(partners),
        "partners": [
            {
                "id": p.id, "name": p.name, "partner_type": p.partner_type,
                "contact_phone": p.contact_phone, "coverage_areas": p.coverage_areas,
                "cold_chain_capable": p.cold_chain_capable,
                "commission_model": p.commission_model,
                "base_rate_kes": p.base_rate_kes,
                "on_time_rate": p.on_time_rate, "dispute_rate": p.dispute_rate,
                "total_jobs_completed": p.total_jobs_completed,
                "is_active": p.is_active,
            } for p in partners
        ]
    }


# ── STORAGE NODES ──────────────────────────────────────────────────

@router.post("/storage-nodes", status_code=201)
def api_create_storage_node(
    payload: StorageNodeCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    node = create_storage_node(db, **payload.dict())
    return {"success": True, "id": node.id, "name": node.name}


@router.get("/storage-nodes")
def list_storage_nodes(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    nodes = db.query(StorageNode).order_by(StorageNode.name.asc()).all()
    return {
        "total": len(nodes),
        "nodes": [
            {
                "id": n.id, "name": n.name, "operator_name": n.operator_name,
                "location": n.location, "capacity_kg": n.capacity_kg,
                "available_kg": n.available_kg, "power_source": n.power_source,
                "has_ice_machine": n.has_ice_machine, "cost_model": n.cost_model,
                "cost_rate_kes": n.cost_rate_kes, "access_terms": n.access_terms,
                "is_active": n.is_active,
            } for n in nodes
        ]
    }


# ── COOLERS ────────────────────────────────────────────────────────

@router.post("/coolers", status_code=201)
def api_register_cooler(
    payload: CoolerCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    cooler = register_cooler(db, payload.capacity_kg, payload.purchase_value_kes)
    return {"success": True, "asset_code": cooler.asset_code, "id": cooler.id}


@router.get("/coolers")
def list_coolers(
    status: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    query = db.query(CoolerAsset)
    if status:
        query = query.filter(CoolerAsset.status == status)
    coolers = query.order_by(CoolerAsset.asset_code.asc()).all()
    return {
        "total": len(coolers),
        "coolers": [
            {
                "id": c.id, "asset_code": c.asset_code, "capacity_kg": c.capacity_kg,
                "owner": c.owner, "status": c.status,
                "current_holder": c.current_holder, "current_location": c.current_location,
                "purchase_value_kes": c.purchase_value_kes,
                "incident_notes": c.incident_notes,
            } for c in coolers
        ]
    }


@router.patch("/coolers/{cooler_id}/status")
def api_update_cooler_status(
    cooler_id: int,
    payload: CoolerStatusUpdate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    cooler = update_cooler_status(
        db, cooler_id, payload.status,
        payload.current_holder, payload.current_location,
        payload.incident_notes,
    )
    return {"success": True, "status": cooler.status}


# ── TRANSPORT JOBS ─────────────────────────────────────────────────

@router.post("/jobs", status_code=201)
def api_create_job(
    payload: TransportJobCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    job = create_transport_job(db, **payload.dict())
    return {"success": True, "id": job.id, "status": job.status}


@router.get("/jobs/active")
def api_active_jobs(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    jobs = get_active_jobs(db)
    result = []
    for j in jobs:
        partner = db.query(LogisticsPartner).filter(
            LogisticsPartner.id == j.partner_id
        ).first() if j.partner_id else None
        result.append({
            "id": j.id, "job_type": j.job_type, "status": j.status,
            "pickup_location": j.pickup_location,
            "destination_location": j.destination_location,
            "partner_name": partner.name if partner else None,
            "scheduled_departure": j.scheduled_departure,
            "scheduled_arrival": j.scheduled_arrival,
            "tracking_reference": j.tracking_reference,
            "cost_kes": j.cost_kes,
        })
    return {"total": len(result), "jobs": result}


@router.patch("/jobs/{job_id}/status")
def api_update_job_status(
    job_id: int,
    payload: JobStatusUpdate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    job = update_job_status(
        db, job_id, payload.status,
        payload.actual_departure, payload.actual_arrival,
        payload.temperature_at_delivery,
    )
    return {"success": True, "status": job.status}


# ── CUSTODY ────────────────────────────────────────────────────────

@router.post("/custody-events", status_code=201)
def api_record_custody(
    payload: CustodyEventCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    event = record_custody_event(
        db, payload.event_type, payload.from_party, payload.to_party,
        payload.location, payload.lot_id, payload.transport_job_id,
        payload.condition_notes, current_user.name,
    )
    return {"success": True, "id": event.id}


@router.get("/custody-chain/{lot_id}")
def api_custody_chain(
    lot_id: int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    events = get_custody_chain(db, lot_id)
    return {
        "lot_id": lot_id,
        "chain": [
            {
                "event_type": e.event_type, "from_party": e.from_party,
                "to_party": e.to_party, "location": e.location,
                "event_at": e.event_at, "recorded_by": e.recorded_by,
            } for e in events
        ]
    }


# ── EXCEPTIONS ─────────────────────────────────────────────────────

@router.post("/exceptions", status_code=201)
def api_report_exception(
    payload: ExceptionCreate,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    exception = report_exception(
        db, payload.transport_job_id, payload.exception_type,
        payload.description, payload.severity, current_user.name,
    )
    return {"success": True, "id": exception.id}


@router.get("/exceptions/open")
def api_open_exceptions(
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    exceptions = get_open_exceptions(db)
    return {
        "total": len(exceptions),
        "exceptions": [
            {
                "id": e.id, "exception_type": e.exception_type,
                "severity": e.severity, "description": e.description,
                "resolution_status": e.resolution_status,
                "reported_at": e.reported_at, "reported_by": e.reported_by,
            } for e in exceptions
        ]
    }


@router.post("/exceptions/{exception_id}/resolve")
def api_resolve_exception(
    exception_id: int,
    payload: ExceptionResolve,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    exception = resolve_exception(db, exception_id, payload.resolution_notes)
    return {"success": True, "status": exception.resolution_status}