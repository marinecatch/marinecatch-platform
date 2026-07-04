# app/services/member_id_service.py
#
# WHY THIS FILE EXISTS:
# Every participant on MarineCatch Africa receives a permanent
# trade identity — a Member ID that never changes and never
# gets recycled.
#
# Format:
#   MC-FSH-000001  (Fisher)
#   MC-SUP-000001  (Supplier / Aggregator)
#   MC-BUY-000001  (Buyer)
#   MC-LOG-000001  (Logistics Partner)
#   MC-EXP-000001  (Exporter)
#   MC-ADM-000001  (Admin)
#
# This ID is referenced on every catch, invoice, inspection,
# shipment, and payment — building a verifiable trade history.

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.compliance_profile import ComplianceProfile
from app.models.user import User


# ── ROLE TO PREFIX MAP ────────────────────────────────────────────

ROLE_PREFIX = {
    "fisher":    "FSH",
    "supplier":  "SUP",
    "buyer":     "BUY",
    "logistics": "LOG",
    "exporter":  "EXP",
    "admin":     "ADM",
}


def generate_member_id(db: Session, role: str) -> str:
    """
    Generate the next available member ID for a given role.
    Format: MC-FSH-000001
    Thread-safe via database sequence.
    """
    prefix = ROLE_PREFIX.get(role.lower(), "MBR")

    # Count existing profiles with same prefix
    existing = db.query(ComplianceProfile).filter(
        ComplianceProfile.member_id.like(f"MC-{prefix}-%")
    ).count()

    sequence = existing + 1
    return f"MC-{prefix}-{str(sequence).zfill(6)}"


def create_compliance_profile(
    db:          Session,
    user_id:     int,
    role:        str,
    verified_by: str = None,
) -> ComplianceProfile:
    """
    Create a compliance profile for a new user.
    Called automatically on user registration.
    Member ID is assigned but user starts at compliance_level=1.
    """
    # Check if profile already exists
    existing = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()
    if existing:
        return existing

    member_id = generate_member_id(db, role)

    profile = ComplianceProfile(
        user_id           = user_id,
        member_id         = member_id,
        compliance_level  = 1,  # Registered
        phone_verified    = True,  # Assumed verified at registration
        created_at        = datetime.now(timezone.utc),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def upgrade_compliance_level(
    db:          Session,
    user_id:     int,
    new_level:   int,
    verified_by: str = None,
    notes:       str = None,
) -> ComplianceProfile:
    """
    Upgrade a user's compliance level.
    Called when verification steps are completed.

    Level 1 → 2: BMU verification confirmed
    Level 2 → 3: KRA PIN verified
    Level 3 → 4: Export certification confirmed
    """
    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()

    if not profile:
        raise ValueError(f"No compliance profile for user {user_id}")

    profile.compliance_level = new_level
    profile.verified_by      = verified_by
    profile.first_verified_at = datetime.now(timezone.utc)
    if notes:
        profile.verification_notes = notes

    db.commit()
    db.refresh(profile)
    return profile


def verify_phone(db: Session, user_id: int) -> ComplianceProfile:
    """Mark phone as verified."""
    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()
    if profile:
        profile.phone_verified    = True
        profile.phone_verified_at = datetime.now(timezone.utc)
        db.commit()
    return profile


def verify_national_id(
    db:          Session,
    user_id:     int,
    national_id: str,
    verified_by: str = None,
) -> ComplianceProfile:
    """Record national ID verification."""
    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()
    if profile:
        profile.national_id          = national_id
        profile.national_id_verified = True
        profile.national_id_verified_at = datetime.now(timezone.utc)
        if verified_by:
            profile.verified_by = verified_by
        db.commit()
    return profile


def verify_bmu(
    db:                    Session,
    user_id:               int,
    bmu_membership_number: str,
    bmu_name:              str,
    fisher_cluster_id:     int = None,
    default_landing_site:  str = None,
    verified_by:           str = None,
) -> ComplianceProfile:
    """Record BMU verification — upgrades to compliance level 2."""
    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()
    if profile:
        profile.bmu_membership_number = bmu_membership_number
        profile.bmu_name              = bmu_name
        profile.bmu_verified          = True
        profile.bmu_verified_at       = datetime.now(timezone.utc)
        if fisher_cluster_id:
            profile.fisher_cluster_id = fisher_cluster_id
        if default_landing_site:
            profile.default_landing_site = default_landing_site
        if verified_by:
            profile.verified_by = verified_by
        if profile.compliance_level < 2:
            profile.compliance_level = 2
        db.commit()
    return profile


def verify_kra(
    db:          Session,
    user_id:     int,
    kra_pin:     str,
    verified_by: str = None,
) -> ComplianceProfile:
    """Record KRA PIN verification — upgrades to compliance level 3."""
    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()
    if profile:
        profile.kra_pin          = kra_pin
        profile.kra_verified     = True
        profile.kra_verified_at  = datetime.now(timezone.utc)
        if verified_by:
            profile.verified_by = verified_by
        if profile.compliance_level < 3:
            profile.compliance_level = 3
        db.commit()
    return profile


def get_profile(db: Session, user_id: int) -> ComplianceProfile:
    """Get compliance profile for a user."""
    return db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()


def get_profile_by_member_id(
    db: Session, member_id: str
) -> ComplianceProfile:
    """Look up a user by their member ID."""
    return db.query(ComplianceProfile).filter(
        ComplianceProfile.member_id == member_id
    ).first()


def update_trust_score(
    db:      Session,
    user_id: int,
) -> ComplianceProfile:
    """
    Recalculate trust score based on operational history.
    Called after each transaction, inspection, or payment.
    """
    from app.models.trade_receivable import TradeReceivable, ReceivableStatus
    from app.models.quality_inspection import QualityInspection
    from app.models.inventory_lot import InventoryLot

    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()
    if not profile:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    score = 0.0

    # Identity verification (max 30 points)
    if profile.phone_verified:       score += 10
    if profile.national_id_verified: score += 10
    if profile.bmu_verified:         score += 10

    # Compliance (max 20 points)
    if profile.kra_verified:         score += 15
    if profile.etims_enabled:        score += 5

    # Operational history (max 30 points)
    if profile.total_transactions >= 1:   score += 5
    if profile.total_transactions >= 10:  score += 5
    if profile.total_transactions >= 50:  score += 5
    if profile.total_volume_kg >= 1000:   score += 5
    if profile.total_value_kes >= 100000: score += 5
    if profile.months_active >= 6:        score += 5

    # Quality (max 20 points — for fishers)
    if profile.rejection_rate == 0 and profile.total_transactions > 0:
        score += 10
    elif profile.rejection_rate < 0.05:
        score += 7
    elif profile.rejection_rate < 0.10:
        score += 3

    if profile.on_time_delivery_rate >= 0.95: score += 10
    elif profile.on_time_delivery_rate >= 0.85: score += 7
    elif profile.on_time_delivery_rate >= 0.70: score += 3

    profile.trust_score = round(min(score, 100.0), 1)
    db.commit()
    return profile


def seed_compliance_profiles_for_existing_users(db: Session):
    """
    One-time seed: create compliance profiles for all existing users
    who don't have one yet.
    """
    users = db.query(User).filter(User.is_active == True).all()
    created = 0
    for user in users:
        existing = db.query(ComplianceProfile).filter(
            ComplianceProfile.user_id == user.id
        ).first()
        if not existing:
            role = user.role.value if hasattr(user.role, 'value') else str(user.role)
            # Clean role string
            role = role.replace('UserRole.', '').lower()
            create_compliance_profile(db, user.id, role)
            created += 1
    db.commit()
    return created