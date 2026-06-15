# app/services/ussd_service.py
#
# WHY THIS FILE EXISTS:
# USSD interface for fishers on feature phones.
# Zero data required — works on any network, any handset.
#
# Architecture:
# - Stateless: every request contains full session history in `text`
# - text="" means first request (main menu)
# - text="1" means user chose option 1
# - text="1*tuna" means user chose option 1, then typed "tuna"
# - text="1*tuna*45" means option 1, typed "tuna", typed "45"
#
# Response format:
# CON message → continue session (show next menu)
# END message → end session (final message, no input)
#
# Three flows for MVP:
# 1. Log Catch → creates inventory record
# 2. Check Prices → shows current market prices
# 3. My Payments → shows payout summary

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.models.user import User
from app.models.inventory_lot import InventoryLot, LotStatus, OwnershipType
from app.models.payment import PaymentTransaction, PayoutStatus


# ── SPECIES MAP ───────────────────────────────────────────────────
# USSD uses numbers — map to species names

SPECIES_MAP = {
    "1": "tuna",
    "2": "octopus",
    "3": "prawns",
    "4": "lobster",
    "5": "snapper",
    "6": "kingfish",
    "7": "sardines",
    "8": "crab",
}

LANDING_SITES = {
    "1": "kibuyuni",
    "2": "kinondo",
    "3": "shimoni",
    "4": "ukunda",
    "5": "vanga",
    "6": "other",
}


# ── MAIN ROUTER ───────────────────────────────────────────────────

def handle_ussd(
    db:           Session,
    session_id:   str,
    phone_number: str,
    text:         str,
) -> str:
    """
    Main USSD session handler.
    Routes based on text input history.
    Returns CON or END response string.
    """
    # Clean phone number
    phone = phone_number.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    # Parse session state from text
    parts = text.split("*") if text else []
    level = len(parts)

    # ── MAIN MENU (level 0) ───────────────────────────────────
    if text == "" or level == 0:
        return (
            "CON Welcome to MarineCatch Africa\n"
            "Habari ya Samaki\n\n"
            "1. Log Catch / Ingiza Samaki\n"
            "2. Check Prices / Angalia Bei\n"
            "3. My Payments / Malipo Yangu\n"
            "4. Contact Support"
        )

    main_choice = parts[0]

    # ── FLOW 1: LOG CATCH ─────────────────────────────────────
    if main_choice == "1":
        return handle_log_catch(db, phone, parts)

    # ── FLOW 2: CHECK PRICES ──────────────────────────────────
    elif main_choice == "2":
        return handle_check_prices(db, parts)

    # ── FLOW 3: MY PAYMENTS ───────────────────────────────────
    elif main_choice == "3":
        return handle_my_payments(db, phone, parts)

    # ── FLOW 4: SUPPORT ───────────────────────────────────────
    elif main_choice == "4":
        return (
            "END MarineCatch Africa Support\n\n"
            "Call/WhatsApp: +254700000000\n"
            "Email: support@marinecatch.co.ke\n\n"
            "Mon-Sat: 6am - 8pm"
        )

    else:
        return "END Invalid option. Please try again.\nDial *384*71253#"


# ── FLOW 1: LOG CATCH ─────────────────────────────────────────────

def handle_log_catch(db: Session, phone: str, parts: list) -> str:
    """
    Multi-step catch logging flow.
    parts[0] = "1" (main menu choice)
    parts[1] = species number
    parts[2] = weight in kg
    parts[3] = landing site number
    parts[4] = confirmation (1=yes, 2=no)
    """
    level = len(parts)

    # Step 1 — Choose species
    if level == 1:
        return (
            "CON Log Catch / Ingiza Samaki\n"
            "Select species / Chagua samaki:\n\n"
            "1. Tuna / Jodari\n"
            "2. Octopus / Pweza\n"
            "3. Prawns / Kamba\n"
            "4. Lobster / Kamba Kochi\n"
            "5. Snapper / Changu\n"
            "6. Kingfish / Nguru\n"
            "7. Sardines / Dagaa\n"
            "8. Crab / Kaa"
        )

    # Step 2 — Enter weight
    if level == 2:
        species_num = parts[1]
        if species_num not in SPECIES_MAP:
            return "END Invalid species. Please try again.\nDial *384*71253#"
        species = SPECIES_MAP[species_num]
        return (
            f"CON {species.title()} selected.\n\n"
            f"Enter weight in kg:\n"
            f"(Example: 45 for 45kg)"
        )

    # Step 3 — Enter price per kg
    if level == 3:
        weight_str = parts[2]
        if not weight_str.isdigit() or int(weight_str) <= 0:
            return "END Invalid weight. Please try again.\nDial *384*71253#"
        species = SPECIES_MAP.get(parts[1], "unknown")
        return (
            f"CON {species.title()} — {parts[2]}kg\n\n"
            f"Enter price per kg (KES):\n"
            f"(Example: 780 for KES 780/kg)"
        )

    # Step 4 — Choose landing site
    if level == 4:
        price_str = parts[3]
        if not price_str.isdigit() or int(price_str) <= 0:
            return "END Invalid price. Please try again.\nDial *384*71253#"
        return (
            "CON Select landing site:\n\n"
            "1. Kibuyuni\n"
            "2. Kinondo\n"
            "3. Shimoni\n"
            "4. Ukunda\n"
            "5. Vanga\n"
            "6. Other"
        )

    # Step 5 — Confirm
    if level == 5:
        site_num = parts[4]
        if site_num not in LANDING_SITES:
            return "END Invalid landing site. Please try again.\nDial *384*71253#"
        species      = SPECIES_MAP.get(parts[1], "unknown")
        weight_kg    = int(parts[2])
        price_kg     = int(parts[3])
        landing_site = LANDING_SITES[site_num]
        return (
            f"CON Confirm catch / Thibitisha:\n\n"
            f"Species: {species.title()}\n"
            f"Weight: {weight_kg}kg\n"
            f"Price: KES {price_kg}/kg\n"
            f"Site: {landing_site.title()}\n\n"
            f"1. Confirm / Thibitisha\n"
            f"2. Cancel / Ghairi"
        )

    # Step 6 — Save to database
    if level == 6:
        confirmation = parts[5]

        if confirmation == "2":
            return "END Catch cancelled.\nDial *384*71253# to try again."

        if confirmation != "1":
            return "END Invalid option.\nDial *384*71253# to try again."

        species      = SPECIES_MAP.get(parts[1], "unknown")
        weight_kg    = int(parts[2])
        price_kg     = int(parts[3])
        landing_site = LANDING_SITES.get(parts[4], "other")

        # Find fisher by phone
        fisher = db.query(User).filter(
            User.phone.contains(phone[-9:])
        ).first()

        # Use admin user as fallback if fisher not registered
        if not fisher:
            fisher = db.query(User).filter(
                User.role == "admin"
            ).first()

        fisher_id   = fisher.id if fisher else 1
        fisher_name = fisher.name if fisher else "USSD Fisher"

        # Generate lot number
        today    = datetime.now(timezone.utc).strftime("%Y%m%d")
        count    = db.query(InventoryLot).filter(
            InventoryLot.lot_number.like(f"MC-USSD-{today}-%")
        ).count()
        lot_number = f"MC-USSD-{today}-{str(count + 1).zfill(4)}"

        # Create pending inventory lot
        try:
            lot = InventoryLot(
                lot_number         = lot_number,
                traceability_code  = f"MC-TRACE-USSD-{lot_number}",
                species            = species,
                weight_kg          = float(weight_kg),
                available_kg       = float(weight_kg),
                reserved_kg        = 0.0,
                landing_site       = landing_site,
                catch_date         = datetime.now(timezone.utc).date(),
                source_user_id     = fisher_id,
                source_name        = fisher_name,
                ownership_type     = OwnershipType.MARKETPLACE,
                lot_status         = LotStatus.AVAILABLE,
                selling_price_per_kg = float(price_kg),
                notes              = f"Logged via USSD by {phone}.",
            )

            db.add(lot)
            db.commit()

            return (
                f"END Catch logged! Samaki imesajiliwa!\n\n"
                f"Lot: {lot_number}\n"
                f"Species: {species.title()}\n"
                f"Weight: {weight_kg}kg\n"
                f"Price: KES {price_kg}/kg\n"
                f"Site: {landing_site.title()}\n\n"
                f"Asante! Thank you!"
            )

        except Exception as e:
            db.rollback()
            return "END Error saving catch. Please try again.\nDial *384*71253#"

# ── FLOW 2: CHECK PRICES ──────────────────────────────────────────

def handle_check_prices(db: Session, parts: list) -> str:
    """
    Price check flow — show current market prices.
    """
    level = len(parts)

    # Step 1 — Choose species
    if level == 1:
        return (
            "CON Check Prices / Angalia Bei\n\n"
            "1. Tuna / Jodari\n"
            "2. Octopus / Pweza\n"
            "3. Prawns / Kamba\n"
            "4. Lobster / Kamba Kochi\n"
            "5. Snapper / Changu\n"
            "6. Kingfish / Nguru\n"
            "7. Sardines / Dagaa\n"
            "8. Crab / Kaa\n"
            "9. All species"
        )

    # Step 2 — Show price
    if level == 2:
        choice = parts[1]

        if choice == "9":
            # Show all available species with prices
            lots = db.query(InventoryLot).filter(
                InventoryLot.lot_status == LotStatus.AVAILABLE,
                InventoryLot.available_kg > 0,
                InventoryLot.selling_price_per_kg > 0,
            ).all()

            if not lots:
                return "END No fish available right now.\nCheck again later."

            # Group by species
            prices = {}
            for lot in lots:
                if lot.species not in prices:
                    prices[lot.species] = lot.selling_price_per_kg

            lines = ["END Current Prices / Bei za Leo:\n"]
            for species, price in sorted(prices.items()):
                lines.append(f"{species.title()}: KES {price}/kg")
            lines.append("\nMarineCatch Africa")
            return "\n".join(lines)

        # Single species
        if choice not in SPECIES_MAP:
            return "END Invalid option.\nDial *384*71253# to try again."

        species = SPECIES_MAP[choice]

        # Find latest available lot for this species
        lot = db.query(InventoryLot).filter(
            InventoryLot.species == species,
            InventoryLot.lot_status == LotStatus.AVAILABLE,
            InventoryLot.available_kg > 0,
            InventoryLot.selling_price_per_kg > 0,
        ).order_by(InventoryLot.created_at.desc()).first()

        if not lot:
            return (
                f"END No {species.title()} available.\n"
                f"Hakuna {species.title()} sasa hivi.\n\n"
                f"Check again tomorrow.\n"
                f"Angalia kesho."
            )

        return (
            f"END {species.title()} Price / Bei:\n\n"
            f"KES {lot.selling_price_per_kg}/kg\n"
            f"Available: {lot.available_kg}kg\n"
            f"Location: {lot.landing_site.title()}\n\n"
            f"To sell: Call +254700000000\n"
            f"MarineCatch Africa"
        )

    return "END Invalid option.\nDial *384*71253#"


# ── FLOW 3: MY PAYMENTS ───────────────────────────────────────────

def handle_my_payments(db: Session, phone: str, parts: list) -> str:
    """
    Payment summary for fisher.
    Shows pending and completed payouts.
    """
    # Find fisher by phone
    fisher = db.query(User).filter(
        User.phone.contains(phone[-9:])
    ).first()

    if not fisher:
        return (
            "END Phone number not registered.\n"
            "Nambari haijasajiliwa.\n\n"
            "Contact: +254700000000\n"
            "to register your number."
        )

    # Get payout summary from payment transactions
    from app.models.order import Order

    orders = db.query(Order).filter(
        Order.fisherman_id == fisher.id
    ).all()

    order_ids = [o.id for o in orders]

    if not order_ids:
        return (
            f"END Habari {fisher.name}!\n\n"
            f"No transactions yet.\n"
            f"Bado hakuna malipo.\n\n"
            f"Log a catch to get started:\n"
            f"Dial *384*71253#"
        )

    txns = db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id.in_(order_ids)
    ).all() if order_ids else []

    total_paid    = sum(
        t.supplier_amount or 0 for t in txns
        if t.payout_status == PayoutStatus.PAID
    )
    total_pending = sum(
        t.supplier_amount or 0 for t in txns
        if t.payout_status in [PayoutStatus.PENDING, PayoutStatus.PROCESSING]
    )

    # Last payment
    paid_txns = [t for t in txns if t.payout_status == PayoutStatus.PAID]
    last_paid_date = None
    if paid_txns:
        last = max(paid_txns, key=lambda t: t.created_at or datetime.min)
        last_paid_date = last.created_at.strftime("%d %b %Y") if last.created_at else None

    response = (
        f"END Habari {fisher.name}!\n\n"
        f"Total Earned: KES {total_paid:,.0f}\n"
        f"Pending: KES {total_pending:,.0f}\n"
    )
    if last_paid_date:
        response += f"Last Payment: {last_paid_date}\n"

    response += (
        f"\nFor details call:\n"
        f"+254700000000\n"
        f"MarineCatch Africa"
    )

    return response