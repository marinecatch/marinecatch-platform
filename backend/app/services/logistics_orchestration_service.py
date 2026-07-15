# app/services/logistics_orchestration_service.py
#
# WHY THIS FILE EXISTS:
# Core logistics orchestration logic. MarineCatch coordinates
# partners, storage nodes, and coolers — it does not own the
# underlying infrastructure. This service manages the full
# journey of a lot: pickup, storage, long-haul, last-mile,
# and return — potentially across multiple partners.

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional

from app.models.logistics_partner import LogisticsPartner
from app.models.storage_node import StorageNode
from app.models.cooler_asset import CoolerAsset
from app.models.transport_job import TransportJob
from app.models.custody_event import CustodyEvent
from app.models.logistics_exception import LogisticsException


# ── LOGISTICS PARTNERS ────────────────────────────────────────────

def create_partner(
    db:            Session,
    name:          str,
    partner_type:  str,
    contact_phone: Optional[str] = None,
    contact_person: Optional[str] = None,
    coverage_areas: Optional[str] = None,
    cold_chain_capable: bool = False,
    max_payload_kg: Optional[float] = None,
    commission_model: str = "flat_fee",
    base_rate_kes: Optional[float] = None,
    per_km_rate_kes: Optional[float] = None,
    per_kg_rate_kes: Optional[float] = None,
    notes: Optional[str] = None,
) -> LogisticsPartner:
    """Register a new logistics partner — rider, bus company, courier, etc."""
    partner = LogisticsPartner(
        name               = name,
        partner_type       = partner_type,
        contact_phone      = contact_phone,
        contact_person     = contact_person,
        coverage_areas     = coverage_areas,
        cold_chain_capable = cold_chain_capable,
        max_payload_kg     = max_payload_kg,
        commission_model   = commission_model,
        base_rate_kes      = base_rate_kes,
        per_km_rate_kes    = per_km_rate_kes,
        per_kg_rate_kes    = per_kg_rate_kes,
        notes              = notes,
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def get_partners_by_coverage(db: Session, location: str) -> list:
    """Find partners covering a specific location."""
    return db.query(LogisticsPartner).filter(
        LogisticsPartner.is_active == True,
        LogisticsPartner.coverage_areas.ilike(f"%{location}%")
    ).all()


def update_partner_performance(db: Session, partner_id: int):
    """
    Recalculate a partner's on-time rate and dispute rate
    based on completed transport jobs and logged exceptions.
    """
    partner = db.query(LogisticsPartner).filter(
        LogisticsPartner.id == partner_id
    ).first()
    if not partner:
        return None

    jobs = db.query(TransportJob).filter(
        TransportJob.partner_id == partner_id,
        TransportJob.status == "completed"
    ).all()

    total = len(jobs)
    if total == 0:
        return partner

    on_time = sum(
        1 for j in jobs
        if j.actual_arrival and j.scheduled_arrival
        and j.actual_arrival <= j.scheduled_arrival
    )

    exceptions = db.query(LogisticsException).join(
        TransportJob, LogisticsException.transport_job_id == TransportJob.id
    ).filter(TransportJob.partner_id == partner_id).count()

    partner.total_jobs_completed = total
    partner.on_time_rate = round(on_time / total, 3) if total > 0 else 0.0
    partner.dispute_rate = round(exceptions / total, 3) if total > 0 else 0.0

    db.commit()
    db.refresh(partner)
    return partner


# ── STORAGE NODES ──────────────────────────────────────────────────

def create_storage_node(
    db:              Session,
    name:            str,
    operator_name:   str,
    location:        str,
    capacity_kg:     float,
    power_source:    Optional[str] = None,
    has_ice_machine: bool = False,
    cost_model:      str = "informal",
    cost_rate_kes:   Optional[float] = None,
    access_terms:    Optional[str] = None,
    partner_id:      Optional[int] = None,
) -> StorageNode:
    """Register a cold storage node in the network."""
    node = StorageNode(
        name            = name,
        operator_name   = operator_name,
        location        = location,
        capacity_kg     = capacity_kg,
        available_kg    = capacity_kg,
        power_source    = power_source,
        has_ice_machine = has_ice_machine,
        cost_model      = cost_model,
        cost_rate_kes   = cost_rate_kes,
        access_terms    = access_terms,
        partner_id      = partner_id,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def reserve_storage_space(
    db: Session, node_id: int, weight_kg: float
) -> StorageNode:
    """Reserve space at a storage node — decrements available_kg."""
    node = db.query(StorageNode).filter(StorageNode.id == node_id).first()
    if not node:
        raise ValueError(f"Storage node {node_id} not found")
    if node.available_kg < weight_kg:
        raise ValueError(
            f"Insufficient space at {node.name}: "
            f"{node.available_kg}kg available, {weight_kg}kg requested"
        )
    node.available_kg -= weight_kg
    db.commit()
    db.refresh(node)
    return node


def release_storage_space(
    db: Session, node_id: int, weight_kg: float
) -> StorageNode:
    """Release reserved space — used when stock leaves storage."""
    node = db.query(StorageNode).filter(StorageNode.id == node_id).first()
    if not node:
        raise ValueError(f"Storage node {node_id} not found")
    node.available_kg = min(node.available_kg + weight_kg, node.capacity_kg)
    db.commit()
    db.refresh(node)
    return node


# ── COOLER ASSETS ─────────────────────────────────────────────────

def generate_cooler_code(db: Session) -> str:
    count = db.query(CoolerAsset).count()
    return f"MC-COOL-{str(count + 1).zfill(3)}"


def register_cooler(
    db:                 Session,
    capacity_kg:        float,
    purchase_value_kes: Optional[float] = None,
) -> CoolerAsset:
    """Register a new cooler asset owned by MarineCatch."""
    cooler = CoolerAsset(
        asset_code          = generate_cooler_code(db),
        capacity_kg         = capacity_kg,
        owner               = "marinecatch",
        status              = "available",
        purchase_value_kes  = purchase_value_kes,
        purchase_date       = datetime.now(timezone.utc),
    )
    db.add(cooler)
    db.commit()
    db.refresh(cooler)
    return cooler


def update_cooler_status(
    db:               Session,
    cooler_id:        int,
    status:           str,
    current_holder:   Optional[str] = None,
    current_location: Optional[str] = None,
    incident_notes:   Optional[str] = None,
) -> CoolerAsset:
    """Update a cooler's status as it moves through the chain."""
    cooler = db.query(CoolerAsset).filter(CoolerAsset.id == cooler_id).first()
    if not cooler:
        raise ValueError(f"Cooler {cooler_id} not found")

    cooler.status = status
    if current_holder:
        cooler.current_holder = current_holder
    if current_location:
        cooler.current_location = current_location
    if incident_notes:
        cooler.incident_notes = incident_notes

    db.commit()
    db.refresh(cooler)
    return cooler


def get_available_coolers(db: Session) -> list:
    """Get all coolers currently available for a new job."""
    return db.query(CoolerAsset).filter(
        CoolerAsset.status == "available"
    ).all()


# ── TRANSPORT JOBS ─────────────────────────────────────────────────

def create_transport_job(
    db:                   Session,
    pickup_location:      str,
    destination_location: str,
    job_type:             str,
    partner_id:           Optional[int] = None,
    cooler_asset_id:      Optional[int] = None,
    order_id:             Optional[int] = None,
    lot_id:                Optional[int] = None,
    shipment_id:           Optional[int] = None,
    sequence_number:       int = 1,
    scheduled_departure:   Optional[datetime] = None,
    scheduled_arrival:     Optional[datetime] = None,
    cost_kes:              Optional[float] = None,
    tracking_reference:    Optional[str] = None,
    notes:                 Optional[str] = None,
) -> TransportJob:
    """
    Create a transport job — one leg of a journey.
    A single shipment can have multiple jobs (motorbike + bus + rider).
    """
    job = TransportJob(
        shipment_id          = shipment_id,
        sequence_number      = sequence_number,
        order_id             = order_id,
        lot_id               = lot_id,
        pickup_location      = pickup_location,
        destination_location = destination_location,
        partner_id           = partner_id,
        cooler_asset_id      = cooler_asset_id,
        job_type             = job_type,
        status               = "pending",
        scheduled_departure  = scheduled_departure,
        scheduled_arrival    = scheduled_arrival,
        cost_kes             = cost_kes,
        tracking_reference   = tracking_reference,
        notes                = notes,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Mark cooler as in transit if assigned
    if cooler_asset_id:
        update_cooler_status(
            db, cooler_asset_id, "in_transit",
            current_location=pickup_location
        )

    return job


def update_job_status(
    db:                Session,
    job_id:            int,
    status:            str,
    actual_departure:  Optional[datetime] = None,
    actual_arrival:    Optional[datetime] = None,
    temperature_at_delivery: Optional[float] = None,
) -> TransportJob:
    """Update transport job status as it progresses."""
    job = db.query(TransportJob).filter(TransportJob.id == job_id).first()
    if not job:
        raise ValueError(f"Transport job {job_id} not found")

    job.status = status
    if actual_departure:
        job.actual_departure = actual_departure
    if actual_arrival:
        job.actual_arrival = actual_arrival
    if temperature_at_delivery is not None:
        job.temperature_at_delivery = temperature_at_delivery

    db.commit()
    db.refresh(job)

    # Update cooler location on completion
    if status == "completed" and job.cooler_asset_id:
        update_cooler_status(
            db, job.cooler_asset_id, "available",
            current_location=job.destination_location
        )

    # Update partner performance stats
    if status == "completed" and job.partner_id:
        update_partner_performance(db, job.partner_id)

    return job


def get_active_jobs(db: Session) -> list:
    """Get all jobs currently in progress."""
    return db.query(TransportJob).filter(
        TransportJob.status.in_(["pending", "in_transit"])
    ).order_by(TransportJob.scheduled_departure.asc()).all()


# ── CUSTODY EVENTS ─────────────────────────────────────────────────

def record_custody_event(
    db:               Session,
    event_type:       str,
    from_party:       Optional[str] = None,
    to_party:         Optional[str] = None,
    location:         Optional[str] = None,
    lot_id:           Optional[int] = None,
    transport_job_id: Optional[int] = None,
    condition_notes:  Optional[str] = None,
    recorded_by:      Optional[str] = None,
) -> CustodyEvent:
    """Record a chain-of-custody handoff event."""
    event = CustodyEvent(
        lot_id           = lot_id,
        transport_job_id = transport_job_id,
        from_party       = from_party,
        to_party         = to_party,
        event_type       = event_type,
        location         = location,
        condition_notes  = condition_notes,
        recorded_by      = recorded_by,
        event_at         = datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_custody_chain(db: Session, lot_id: int) -> list:
    """Get full chain of custody for a lot, in order."""
    return db.query(CustodyEvent).filter(
        CustodyEvent.lot_id == lot_id
    ).order_by(CustodyEvent.event_at.asc()).all()


# ── EXCEPTIONS ─────────────────────────────────────────────────────

def report_exception(
    db:               Session,
    transport_job_id: int,
    exception_type:   str,
    description:      str,
    severity:         str = "medium",
    reported_by:      Optional[str] = None,
) -> LogisticsException:
    """Report a logistics exception — breakdown, delay, damage, etc."""
    exception = LogisticsException(
        transport_job_id = transport_job_id,
        exception_type   = exception_type,
        severity         = severity,
        description      = description,
        resolution_status = "open",
        reported_by      = reported_by,
        reported_at      = datetime.now(timezone.utc),
    )
    db.add(exception)
    db.commit()
    db.refresh(exception)

    # Mark the job as delayed
    job = db.query(TransportJob).filter(
        TransportJob.id == transport_job_id
    ).first()
    if job and job.status not in ["completed", "failed"]:
        job.status = "delayed"
        db.commit()

    return exception


def resolve_exception(
    db:               Session,
    exception_id:     int,
    resolution_notes: str,
) -> LogisticsException:
    """Mark an exception as resolved."""
    exception = db.query(LogisticsException).filter(
        LogisticsException.id == exception_id
    ).first()
    if not exception:
        raise ValueError(f"Exception {exception_id} not found")

    exception.resolution_status = "resolved"
    exception.resolution_notes  = resolution_notes
    exception.resolved_at       = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exception)
    return exception


def get_open_exceptions(db: Session) -> list:
    """Get all unresolved logistics exceptions."""
    return db.query(LogisticsException).filter(
        LogisticsException.resolution_status.in_(["open", "in_progress"])
    ).order_by(LogisticsException.reported_at.desc()).all()


# ── NETWORK SUMMARY ────────────────────────────────────────────────

def get_logistics_network_summary(db: Session) -> dict:
    """Overview of the entire logistics network for dashboard."""
    total_partners  = db.query(LogisticsPartner).filter(
        LogisticsPartner.is_active == True
    ).count()
    total_storage   = db.query(StorageNode).filter(
        StorageNode.is_active == True
    ).count()
    total_capacity  = db.query(
        func.sum(StorageNode.capacity_kg)
    ).filter(StorageNode.is_active == True).scalar() or 0.0
    available_capacity = db.query(
        func.sum(StorageNode.available_kg)
    ).filter(StorageNode.is_active == True).scalar() or 0.0

    total_coolers   = db.query(CoolerAsset).count()
    available_coolers = db.query(CoolerAsset).filter(
        CoolerAsset.status == "available"
    ).count()
    lost_damaged    = db.query(CoolerAsset).filter(
        CoolerAsset.status.in_(["damaged", "lost"])
    ).count()

    active_jobs     = db.query(TransportJob).filter(
        TransportJob.status.in_(["pending", "in_transit"])
    ).count()
    delayed_jobs    = db.query(TransportJob).filter(
        TransportJob.status == "delayed"
    ).count()

    open_exceptions = db.query(LogisticsException).filter(
        LogisticsException.resolution_status.in_(["open", "in_progress"])
    ).count()

    return {
        "partners": {
            "total_active": total_partners,
        },
        "storage": {
            "total_nodes":         total_storage,
            "total_capacity_kg":   round(total_capacity, 1),
            "available_capacity_kg": round(available_capacity, 1),
            "utilization_pct":     round(
                (1 - available_capacity/total_capacity) * 100, 1
            ) if total_capacity > 0 else 0.0,
        },
        "coolers": {
            "total":            total_coolers,
            "available":        available_coolers,
            "lost_or_damaged":  lost_damaged,
        },
        "jobs": {
            "active":   active_jobs,
            "delayed":  delayed_jobs,
        },
        "exceptions": {
            "open": open_exceptions,
        },
    }