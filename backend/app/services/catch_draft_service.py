# app/services/catch_draft_service.py
#
# Manages the catch submission workflow.
# Fisher submits → draft created → inspection → InventoryLot

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.models.catch_draft import CatchDraft, CatchDraftStatus
from app.models.inventory_lot import InventoryLot, LotStatus, OwnershipType
from app.models.user import User
from app.models.compliance_profile import ComplianceProfile


def generate_draft_reference(db: Session) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = db.query(CatchDraft).filter(
        CatchDraft.reference_number.like(f"MC-DRAFT-{today}-%")
    ).count()
    return f"MC-DRAFT-{today}-{str(count + 1).zfill(4)}"


def create_catch_draft(
    db:           Session,
    fisher_id:    int,
    species:      str,
    weight_kg:    float,
    landing_site: str,
    channel:      str = "whatsapp",
) -> CatchDraft:
    """
    Create a catch draft after fisher submits species, weight, site.
    Status = awaiting_price until fisher provides asking price.
    """
    fisher = db.query(User).filter(User.id == fisher_id).first()

    # Get member ID from compliance profile
    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == fisher_id
    ).first()

    draft = CatchDraft(
        reference_number   = generate_draft_reference(db),
        fisher_id          = fisher_id,
        fisher_name        = fisher.name if fisher else None,
        fisher_phone       = fisher.phone if fisher else None,
        member_id          = profile.member_id if profile else None,
        species            = species,
        weight_kg          = weight_kg,
        landing_site       = landing_site,
        catch_date         = datetime.now(timezone.utc),
        submission_channel = channel,
        status             = CatchDraftStatus.AWAITING_PRICE,
        created_at         = datetime.now(timezone.utc),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def set_asking_price(
    db:                  Session,
    draft_id:            int,
    asking_price_per_kg: float,
) -> CatchDraft:
    """
    Fisher provides their asking price.
    Draft moves to submitted status.
    """
    draft = db.query(CatchDraft).filter(CatchDraft.id == draft_id).first()
    if not draft:
        raise ValueError(f"Draft {draft_id} not found")

    draft.asking_price_per_kg = asking_price_per_kg
    draft.status              = CatchDraftStatus.SUBMITTED
    draft.submitted_at        = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft


def get_pending_draft_for_fisher(
    db: Session, fisher_id: int
) -> Optional[CatchDraft]:
    """
    Get the most recent draft awaiting price from a fisher.
    Used during WhatsApp conversation to match price response
    to the correct pending draft.
    """
    return db.query(CatchDraft).filter(
        CatchDraft.fisher_id == fisher_id,
        CatchDraft.status == CatchDraftStatus.AWAITING_PRICE,
    ).order_by(CatchDraft.created_at.desc()).first()


def accept_draft_and_create_lot(
    db:                  Session,
    draft_id:            int,
    selling_price_per_kg: float,
    inspected_by:        str,
    quality_grade:       str = "A",
    notes:               str = None,
) -> InventoryLot:
    """
    Accept a catch draft after quality inspection.
    Creates the InventoryLot with MarineCatch's selling price.

    selling_price_per_kg = asking_price + commission + handling + logistics
    This is set by MarineCatch, not the fisher.
    """
    draft = db.query(CatchDraft).filter(CatchDraft.id == draft_id).first()
    if not draft:
        raise ValueError(f"Draft {draft_id} not found")

    today      = datetime.now(timezone.utc).strftime("%Y%m%d")
    lot_count  = db.query(InventoryLot).filter(
        InventoryLot.lot_number.like(f"MC-LOT-{today}-%")
    ).count()
    lot_number = f"MC-LOT-{today}-{str(lot_count + 1).zfill(4)}"

    lot = InventoryLot(
        lot_number           = lot_number,
        traceability_code    = f"MC-TRACE-{lot_number}",
        species              = draft.species,
        weight_kg            = draft.weight_kg,
        available_kg         = draft.weight_kg,
        reserved_kg          = 0.0,
        landing_site         = draft.landing_site,
        catch_date           = draft.catch_date.date() if draft.catch_date else None,
        source_user_id       = draft.fisher_id,
        source_name          = draft.fisher_name,
        ownership_type       = OwnershipType.MARKETPLACE,
        lot_status           = LotStatus.AVAILABLE,
        selling_price_per_kg = selling_price_per_kg,
        grade                = quality_grade,
        notes                = f"From draft {draft.reference_number}. "
                               f"Fisher asking: KES {draft.asking_price_per_kg}/kg. "
                               f"{notes or ''}",
    )
    db.add(lot)
    db.flush()

    # Update draft
    draft.status                  = CatchDraftStatus.ACCEPTED
    draft.quality_grade           = quality_grade
    draft.inspected_by            = inspected_by
    draft.inspected_at            = datetime.now(timezone.utc)
    draft.accepted_at             = datetime.now(timezone.utc)
    draft.created_inventory_lot_id = lot.id
    if notes:
        draft.inspection_notes = notes

    db.commit()
    db.refresh(lot)
    return lot


def reject_draft(
    db:               Session,
    draft_id:         int,
    rejection_reason: str,
    inspected_by:     str,
) -> CatchDraft:
    """
    Reject a catch draft after quality inspection.
    No InventoryLot is created.
    Draft remains permanently for audit trail.
    """
    draft = db.query(CatchDraft).filter(CatchDraft.id == draft_id).first()
    if not draft:
        raise ValueError(f"Draft {draft_id} not found")

    draft.status           = CatchDraftStatus.REJECTED
    draft.rejection_reason = rejection_reason
    draft.inspected_by     = inspected_by
    draft.inspected_at     = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft


def get_drafts_for_fisher(
    db: Session, fisher_id: int, limit: int = 10
) -> list:
    """Get recent catch drafts for a fisher."""
    return db.query(CatchDraft).filter(
        CatchDraft.fisher_id == fisher_id
    ).order_by(CatchDraft.created_at.desc()).limit(limit).all()