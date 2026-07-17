# app/api/v1/routes/whatsapp.py
#
# WHY THIS FILE EXISTS:
# WhatsApp webhook handler and outbound notification endpoints.
# ONE BACKEND — MANY INTERFACES.
# All business logic stays in existing services.
#
# Endpoints:
# GET  /whatsapp/webhook    → Meta webhook verification
# POST /whatsapp/webhook    → Incoming message handler
# POST /whatsapp/notify/order-confirmed   → Notify buyer
# POST /whatsapp/notify/payment-received  → Notify buyer
# POST /whatsapp/notify/dispatched        → Notify buyer
# POST /whatsapp/notify/fisher-payout     → Notify fisher
# POST /whatsapp/notify/admin-alert       → Alert admin
# POST /whatsapp/notify/cold-chain-breach → Cold chain alert

from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.database.connection import get_db
from app.api.v1.routes.users import get_current_user
from app.services.whatsapp_service import (
    send_text,
    send_menu,
    notify_order_confirmed,
    notify_payment_received,
    notify_order_dispatched,
    notify_fisher_payout,
    notify_admin_alert,
    notify_cold_chain_breach,
    parse_incoming_message,
)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


# ── SCHEMAS ───────────────────────────────────────────────────────

class OrderConfirmedNotification(BaseModel):
    phone:       str
    buyer_name:  str
    order_id:    int
    species:     str
    quantity_kg: float
    total_kes:   float
    reference:   str


class PaymentNotification(BaseModel):
    phone:      str
    buyer_name: str
    amount_kes: float
    reference:  str
    order_id:   int


class DispatchNotification(BaseModel):
    phone:               str
    buyer_name:          str
    order_id:            int
    species:             str
    driver_name:         str
    driver_phone:        str
    vehicle_reg:         str
    estimated_delivery:  str


class PayoutNotification(BaseModel):
    phone:       str
    fisher_name: str
    amount_kes:  float
    species:     str
    quantity_kg: float
    reference:   str


class AdminAlert(BaseModel):
    phone:   str
    subject: str
    details: str


class ColdChainAlert(BaseModel):
    phone:        str
    shipment_ref: str
    temperature:  float
    threshold:    float
    driver_name:  str


# ── WEBHOOK VERIFICATION ──────────────────────────────────────────

@router.get("/webhook")
async def verify_webhook(
    hub_mode:       str = Query(None, alias="hub.mode"),
    hub_challenge:  str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Meta webhook verification endpoint.
    Meta sends a GET request to verify your webhook URL.
    Must respond with hub.challenge if token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


# ── INCOMING MESSAGE HANDLER ──────────────────────────────────────

@router.post("/webhook")
async def handle_incoming(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}

    msg = parse_incoming_message(body)

    if msg.get("type") in ["no_message", "parse_error"]:
        return {"status": "ok"}

    from_phone = msg.get("from_phone", "")
    text       = (msg.get("text") or "").lower().strip()
    button_id  = msg.get("button_id", "")


    try:
        await route_incoming_message(
            db=db,
            from_phone=from_phone,
            text=text,
            button_id=button_id,
        )
    except Exception as e:
        import traceback
        print(f"WA ERROR: {e}")
        print(traceback.format_exc())

    return {"status": "ok"}


async def route_incoming_message(
    db:         Session,
    from_phone: str,
    text:       str,
    button_id:  str,
):
    # TODO POST-LAUNCH: Expand fisher flows
    # - Image posting for catch evidence and quality verification
    # - Logistics coordination with drivers
    # - Multilingual: Swahili menus for coastal fisher communities
    # Priority: August 2026, after first real fishers onboard

    from app.services.inventory_service import get_available_lots
    from app.models.order import Order
    from app.models.user import User, UserRole
    from app.models.inventory_lot import InventoryLot
    from app.models.payment import PaymentTransaction, PayoutStatus

    # ── IDENTIFY USER ROLE ────────────────────────────────────
    clean_phone = from_phone.replace("+", "").replace(" ", "")
    user = db.query(User).filter(
        User.phone.contains(clean_phone[-9:])
    ).first()

    user_role = user.role if user else "unknown"

    # ── ROUTE BY ROLE ─────────────────────────────────────────
    if user_role == "fisher":
        await route_fisher_message(db, from_phone, text, button_id, user)
    else:
        await route_buyer_message(db, from_phone, text, button_id, user)


async def route_fisher_message(
    db:         Session,
    from_phone: str,
    text:       str,
    button_id:  str,
    fisher,
):
    """Handle incoming messages from fishers."""
    from app.services.inventory_service import get_available_lots
    from app.models.order import Order
    from app.models.payment import PaymentTransaction, PayoutStatus
    from app.models.inventory_lot import InventoryLot, LotStatus, OwnershipType
    from datetime import datetime, timezone

    fisher_name = fisher.name.split()[0] if fisher else "Fisher"

    # ── KRA PIN SELF-SUBMISSION ────────────────────────────────
    if text.upper().startswith("KRA "):
        kra_pin = text[4:].strip().upper()
        # Basic KRA PIN format validation: Letter + 9 digits + Letter
        if len(kra_pin) == 11 and kra_pin[0].isalpha() and kra_pin[-1].isalpha() \
                and kra_pin[1:10].isdigit():
            try:
                from app.services.member_id_service import verify_kra
                profile = verify_kra(db, fisher.id, kra_pin, "Self-submitted via WhatsApp")
                await send_text(
                    from_phone,
                    f"✅ *KRA PIN Recorded!*\n\n"
                    f"PIN: {kra_pin}\n"
                    f"Member ID: {profile.member_id}\n\n"
                    f"Our team will verify this and unlock access to "
                    f"hotels, processors, and export buyers within "
                    f"24 hours.\n\n"
                    f"Asante {fisher_name}! 🐟\n"
                    f"MarineCatch Africa"
                )
            except Exception as e:
                await send_text(
                    from_phone,
                    "Sorry, we couldn't save your KRA PIN. Please try again "
                    "or contact support: +254707939810"
                )
        else:
            await send_text(
                from_phone,
                f"❌ Invalid KRA PIN format.\n\n"
                f"A KRA PIN looks like: A123456789B\n"
                f"(1 letter, 9 digits, 1 letter)\n\n"
                f"Try again: *KRA A123456789B*"
            )
        return

    # ── FISHER MAIN MENU ──────────────────────────────────────
    if text in ["hi", "hello", "habari", "menu", "start", "help"]:
        await send_menu(
            phone=   from_phone,
            header=  f"Habari {fisher_name}! 🐟",
            body=    "MarineCatch Africa\nChagua chaguo lako:",
            footer=  "Powered by MarineCatch Africa",
            buttons=[
                {"id": "fisher_catch",   "title": "Log Catch 🐠"},
                {"id": "fisher_payout",  "title": "My Payouts 💚"},
                {"id": "fisher_prices",  "title": "Check Prices 💰"},
            ]
        )
        return

    # ── LOG CATCH — Step 1: species, weight, site ─────────────────
    if text in ["log catch", "catch", "samaki", "ingiza"] or button_id == "fisher_catch":
        await send_text(
            from_phone,
            f"🎣 *Log Your Catch*\n\n"
            f"Type your catch details:\n\n"
            f"*CATCH species weight site*\n\n"
            f"Examples:\n"
            f"• CATCH tuna 45 kibuyuni\n"
            f"• CATCH octopus 20 shimoni\n"
            f"• CATCH prawns 30 kinondo\n\n"
            f"Available sites: kibuyuni, kinondo, shimoni, ukunda, vanga\n\n"
            f"Type MENU to go back."
        )
        return

    # ── CATCH SUBMISSION — Step 1: create draft, ask for price ────
    if text.startswith("catch "):
        parts = text.split()
        if len(parts) >= 4:
            species_input = parts[1].lower()
            weight_str    = parts[2]
            site_input    = parts[3].lower()

            valid_species = ["tuna", "octopus", "prawns", "lobster",
                           "snapper", "kingfish", "sardines", "crab"]
            valid_sites   = ["kibuyuni", "kinondo", "shimoni",
                           "ukunda", "vanga", "mwambao", "other"]

            if species_input not in valid_species:
                await send_text(
                    from_phone,
                    f"❌ Unknown species: {species_input}\n\n"
                    f"Valid: {', '.join(valid_species)}\n\n"
                    f"Try again: *CATCH tuna 45 kibuyuni*"
                )
                return

            if not weight_str.isdigit() or int(weight_str) <= 0:
                await send_text(
                    from_phone,
                    "❌ Invalid weight. Enter a number.\n\n"
                    "Example: *CATCH tuna 45 kibuyuni*"
                )
                return

            if site_input not in valid_sites:
                site_input = "other"

            weight_kg = float(weight_str)

            # Create catch draft
            from app.services.catch_draft_service import create_catch_draft
            draft = create_catch_draft(
                db=db,
                fisher_id=fisher.id,
                species=species_input,
                weight_kg=weight_kg,
                landing_site=site_input,
                channel="whatsapp",
            )

            await send_text(
                from_phone,
                f"✅ *Catch Recorded*\n\n"
                f"• Species: {species_input.title()}\n"
                f"• Weight: {weight_kg}kg\n"
                f"• Site: {site_input.title()}\n"
                f"• Draft: {draft.reference_number}\n\n"
                f"💰 *What is your asking price per kg? (KES)*\n\n"
                f"Type just the number, e.g: *780*\n\n"
                f"This is what you would like to receive per kg.\n"
                f"MarineCatch sets the final market price after inspection."
            )
            return

        await send_text(
            from_phone,
            "❌ Invalid format.\n\n"
            "Use: *CATCH species weight site*\n"
            "Example: *CATCH tuna 45 kibuyuni*"
        )
        return

    # ── CATCH SUBMISSION — Step 2: fisher provides asking price ───
    if text.isdigit() or (text.replace('.','',1).isdigit() and text.count('.') <= 1):
        from app.services.catch_draft_service import (
            get_pending_draft_for_fisher, set_asking_price
        )
        pending_draft = get_pending_draft_for_fisher(db, fisher.id)

        if pending_draft:
            price = float(text)
            if price <= 0 or price > 50000:
                await send_text(
                    from_phone,
                    "❌ Invalid price. Enter a price between 1 and 50,000 KES/kg."
                )
                return

            draft = set_asking_price(db, pending_draft.id, price)

            await send_text(
                from_phone,
                f"🐟 *Catch Submitted Successfully!*\n\n"
                f"• Draft: {draft.reference_number}\n"
                f"• Species: {draft.species.title()}\n"
                f"• Weight: {draft.weight_kg}kg\n"
                f"• Site: {draft.landing_site.title()}\n"
                f"• Your asking price: KES {price:,.0f}/kg\n\n"
                f"⏳ *Status: Pending Quality Inspection*\n\n"
                f"Our team will inspect your catch and set the\n"
                f"final market price. You'll be notified once\n"
                f"it's listed on the marketplace.\n\n"
                f"Asante {fisher_name}! 🌊\n"
                f"MarineCatch Africa"
            )
            return

    # ── MY PAYOUTS ────────────────────────────────────────────
    if text in ["payout", "payouts", "malipo", "pay"] or button_id == "fisher_payout":
        from app.models.order import Order

        orders = db.query(Order).filter(
            Order.fisherman_id == fisher.id
        ).all()

        order_ids = [o.id for o in orders]
        txns = db.query(PaymentTransaction).filter(
            PaymentTransaction.order_id.in_(order_ids)
        ).all() if order_ids else []

        total_paid = sum(
            t.supplier_amount or 0 for t in txns
            if t.payout_status == PayoutStatus.PAID
        )
        total_pending = sum(
            t.supplier_amount or 0 for t in txns
            if t.payout_status in [PayoutStatus.PENDING, PayoutStatus.PROCESSING]
        )

        last_paid_txn = sorted(
            [t for t in txns if t.payout_status == PayoutStatus.PAID],
            key=lambda x: x.created_at or datetime.min,
            reverse=True
        )

        last_date = last_paid_txn[0].created_at.strftime("%d %b %Y") \
            if last_paid_txn else "No payments yet"

        await send_text(
            from_phone,
            f"💚 *Malipo Yako — {fisher_name}*\n\n"
            f"• Jumla Iliyolipwa: KES {total_paid:,.0f}\n"
            f"• Inangoja: KES {total_pending:,.0f}\n"
            f"• Malipo ya Mwisho: {last_date}\n\n"
            f"Kwa maswali: +254700000000\n"
            f"MarineCatch Africa 🐟"
        )
        return

    # ── CHECK PRICES ──────────────────────────────────────────
    if text in ["prices", "bei", "price"] or button_id == "fisher_prices":
        from app.models.inventory_lot import InventoryLot, LotStatus

        lots = db.query(InventoryLot).filter(
            InventoryLot.lot_status == LotStatus.AVAILABLE,
            InventoryLot.selling_price_per_kg > 0,
        ).all()

        if not lots:
            await send_text(from_phone,
                "Bei za sasa hazipo.\nPiga simu: +254700000000")
            return

        prices = {}
        for lot in lots:
            if lot.species not in prices:
                prices[lot.species] = lot.selling_price_per_kg

        lines = ["💰 *Bei za Sasa — MarineCatch*\n"]
        for species, price in sorted(prices.items()):
            lines.append(f"• {species.title()}: KES {price:,.0f}/kg")
        lines.append("\nKwa bei bora zaidi: +254700000000")

        await send_text(from_phone, "\n".join(lines))
        return

    # ── SUPPORT ───────────────────────────────────────────────
    if text in ["support", "help", "msaada"]:
        await send_text(
            from_phone,
            f"📞 *Msaada — MarineCatch Africa*\n\n"
            f"Piga simu: +254700000000\n"
            f"WhatsApp: +254700000000\n"
            f"Email: support@marinecatch.co.ke\n\n"
            f"Saa za kazi: Jumatatu-Jumamosi, 6am-8pm\n\n"
            f"Type MENU kurudi kwenye menyu."
        )
        return

    # ── DEFAULT ───────────────────────────────────────────────
    await send_text(
        from_phone,
        f"Samahani {fisher_name}, sikuelewa. 🤔\n\n"
        f"Type *MENU* kwa chaguo\n"
        f"Type *CATCH tuna 45 kibuyuni* kusajili samaki\n"
        f"Type *PAYOUT* kuona malipo\n"
        f"Type *PRICES* kuona bei\n\n"
        f"MarineCatch Africa 🐟"
    )


async def route_buyer_message(
    db:         Session,
    from_phone: str,
    text:       str,
    button_id:  str,
    user,
):
    """Handle incoming messages from buyers and unknown users."""
    from app.services.inventory_service import get_available_lots
    from app.models.order import Order
    from app.models.user import User
    from app.models.inventory_lot import InventoryLot

    # ── MAIN MENU ─────────────────────────────────────────────
    if text in ["hi", "hello", "habari", "menu", "start", "help"]:
        await send_menu(
            phone=   from_phone,
            header=  "MarineCatch Africa 🐟",
            body=    "Welcome! How can we help you today?",
            footer=  "Fresh seafood from Kenya's coast",
            buttons=[
                {"id": "btn_fish",   "title": "View Fish 🐟"},
                {"id": "btn_orders", "title": "My Orders 📦"},
                {"id": "btn_support","title": "Support 💬"},
            ]
        )
        return

    # ── FISH AVAILABILITY ─────────────────────────────────────
    if text in ["fish", "samaki", "available", "stock"] or button_id == "btn_fish":
        lots = get_available_lots(db, limit=5)
        if not lots:
            await send_text(from_phone,
                "No fish available right now. Please check again later.\n\n"
                "Type MENU to go back.")
            return

        lines = ["*Available Seafood — MarineCatch Africa* 🐟\n"]
        for lot in lots:
            lines.append(
                f"• *{lot.species.title()}* — {lot.available_kg}kg\n"
                f"  KES {lot.selling_price_per_kg}/kg | {lot.landing_site.title()}\n"
                f"  Lot: {lot.lot_number}"
            )
        lines.append(
            "\nType species name for details.\n"
            "Example: *tuna* or *octopus*\n\n"
            "To order: type *ORDER tuna 20*"
        )
        await send_text(from_phone, "\n".join(lines))
        return

    # ── SPECIES LOOKUP ────────────────────────────────────────
    species_list = ["tuna", "octopus", "prawns", "lobster",
                    "snapper", "kingfish", "sardines", "crab"]
    if text in species_list:
        lots = get_available_lots(db, species=text, limit=3)
        if not lots:
            await send_text(from_phone,
                f"No {text.title()} available right now.\n\n"
                f"Type FISH to see all available species.")
            return

        lines = [f"*{text.title()} Available* 🐟\n"]
        for lot in lots:
            lines.append(
                f"• {lot.available_kg}kg @ KES {lot.selling_price_per_kg}/kg\n"
                f"  Grade: {lot.grade} | {lot.condition.title()}\n"
                f"  Location: {lot.landing_site.title()}\n"
                f"  Lot: {lot.lot_number}"
            )
        lines.append(f"\nTo order: type *ORDER {text} 20*")
        await send_text(from_phone, "\n".join(lines))
        return

    # ── ORDER STATUS ──────────────────────────────────────────
    if text.startswith("order status") or text.startswith("status"):
        parts = text.split()
        order_id = None
        for part in parts:
            if part.isdigit():
                order_id = int(part)
                break

        if not order_id:
            await send_text(from_phone,
                "To check order status:\n*ORDER STATUS 5*\n\nType MENU to go back.")
            return

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await send_text(from_phone,
                f"Order #{order_id} not found.\nType MENU to go back.")
            return

        status_emoji = {
            "pending_payment": "⏳", "confirmed": "✅",
            "preparing": "🔧", "dispatched": "🚚",
            "delivered": "📦", "completed": "✅", "cancelled": "❌",
        }
        emoji = status_emoji.get(order.status.value, "📋")

        message = (
            f"{emoji} *Order #{order_id} Status*\n\n"
            f"• Species: {order.species.title()}\n"
            f"• Quantity: {order.quantity_kg}kg\n"
            f"• Amount: KES {order.total_kes:,.0f}\n"
            f"• Status: *{order.status.value.replace('_', ' ').title()}*\n"
        )
        if order.delivery_address:
            message += f"• Delivery: {order.delivery_address}\n"
        message += "\nType MENU to go back."
        await send_text(from_phone, message)
        return

    # ── ORDER PLACEMENT ───────────────────────────────────────
    if text.startswith("order ") and not text.startswith("order status"):
        parts = text.split()
        if len(parts) >= 3 and parts[1] in species_list and parts[2].isdigit():
            species  = parts[1]
            quantity = int(parts[2])
            lots     = get_available_lots(db, species=species, limit=1)

            if not lots:
                await send_text(from_phone,
                    f"Sorry, no {species.title()} available.\n"
                    "Type FISH to see what's available.")
                return

            lot       = lots[0]
            total_kes = quantity * lot.selling_price_per_kg

            if quantity > lot.available_kg:
                await send_text(from_phone,
                    f"Only {lot.available_kg}kg available.\n"
                    f"Type: *ORDER {species} {int(lot.available_kg)}*")
                return

            # Look up buyer's user account
            from app.models.user import User as UserModel
            clean_phone = from_phone.replace("+", "").replace(" ", "")
            buyer = db.query(UserModel).filter(
                UserModel.phone.contains(clean_phone[-9:])
            ).first()

            if not buyer:
                await send_text(from_phone,
                    "📋 *Order Request Received*\n\n"
                    f"• Species: {species.title()}\n"
                    f"• Quantity: {quantity}kg\n"
                    f"• Total: KES {total_kes:,.0f}\n\n"
                    "You're not yet a registered MarineCatch buyer.\n"
                    "Our team will contact you within 30 minutes to\n"
                    "complete your order and registration.\n\n"
                    "Call: +254707939810\n"
                    f"Ref: {lot.lot_number}\n"
                    "MarineCatch Africa 🐟")
                return

            # Place the real order — reserves stock
            try:
                from app.services.order_service import place_order
                order = place_order(
                    db=               db,
                    buyer_id=         buyer.id,
                    lot_id=           lot.id,
                    quantity_kg=      float(quantity),
                    delivery_address= buyer.location or "To be confirmed",
                    notes=            "Order placed via WhatsApp",
                )

                await send_text(from_phone,
                    f"✅ *Order Confirmed!*\n\n"
                    f"• Order #{order.id}\n"
                    f"• Species: {species.title()}\n"
                    f"• Quantity: {quantity}kg\n"
                    f"• Price: KES {lot.selling_price_per_kg}/kg\n"
                    f"• Total: KES {order.total_kes:,.0f}\n"
                    f"• Location: {lot.landing_site.title()}\n\n"
                    f"Status: Pending Payment\n"
                    f"Our team will contact you to arrange payment\n"
                    f"and delivery.\n\n"
                    f"Ref: {lot.lot_number}\n"
                    f"MarineCatch Africa 🐟")
            except Exception as e:
                await send_text(from_phone,
                    "Sorry, we couldn't complete your order right now.\n"
                    "Our team will contact you shortly.\n\n"
                    f"Ref: {lot.lot_number}\n"
                    "Call: +254707939810")
            return

        await send_text(from_phone,
            "To place an order:\n*ORDER species kg*\n\n"
            "Examples:\n• ORDER tuna 20\n• ORDER prawns 50\n\n"
            "Type FISH to see available species.")
        return

    # ── MY ORDERS ─────────────────────────────────────────────
    if text in ["my orders", "orders"] or button_id == "btn_orders":
        await send_text(from_phone,
            "📦 *Check Your Order Status*\n\n"
            "Type: *ORDER STATUS 1*\n(replace 1 with your order ID)\n\n"
            "No order ID? Contact: orders@marinecatch.co.ke\n\n"
            "Type MENU to go back.")
        return

    # ── PRICE INQUIRY ─────────────────────────────────────────
    if text.startswith("price") or text.startswith("bei"):
        parts = text.split()
        if len(parts) >= 2 and parts[1] in species_list:
            species = parts[1]
            lots    = get_available_lots(db, species=species, limit=1)
            if lots:
                lot = lots[0]
                await send_text(from_phone,
                    f"💰 *{species.title()} Price*\n\n"
                    f"• Price: KES {lot.selling_price_per_kg}/kg\n"
                    f"• Available: {lot.available_kg}kg\n"
                    f"• Location: {lot.landing_site.title()}\n\n"
                    f"To order: *ORDER {species} 20*")
            else:
                await send_text(from_phone,
                    f"No {species.title()} available.\nType FISH for all species.")
            return

        await send_text(from_phone,
            "💰 *Price Inquiry*\n\nType: *PRICE species*\n\n"
            "Examples:\n• PRICE tuna\n• PRICE prawns\n\n"
            "Type FISH to see all available fish.")
        return

    # ── SUPPORT ───────────────────────────────────────────────
    if text in ["support", "help", "msaada"] or button_id == "btn_support":
        await send_text(from_phone,
            "📞 *MarineCatch Africa Support*\n\n"
            "Orders: orders@marinecatch.co.ke\n"
            "Finance: finance@marinecatch.co.ke\n\n"
            "Mon-Sat, 6am-8pm EAT\n\n"
            "Type MENU to return.")
        return

    # ── DEFAULT — AI FALLBACK ─────────────────────────────────
    try:
        from app.services.whatsapp_ai_service import get_ai_response
        ai_reply = await get_ai_response(db, text)
        await send_text(from_phone, ai_reply)
    except Exception as e:
        print(f"AI fallback failed: {e}")
        await send_text(from_phone,
            "Sorry, I didn't understand that. 🤔\n\n"
            "Type *MENU* for options\n"
            "Type *FISH* to see available seafood\n"
            "Type *PRICE tuna* for price inquiry\n"
            "Type *ORDER tuna 20* to place an order\n\n"
            "MarineCatch Africa 🐟"
        )
# ── OUTBOUND NOTIFICATIONS ────────────────────────────────────────

@router.post("/notify/order-confirmed")
async def send_order_confirmed(
    payload:     OrderConfirmedNotification,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Send order confirmation to buyer via WhatsApp."""
    result = await notify_order_confirmed(
        phone=       payload.phone,
        buyer_name=  payload.buyer_name,
        order_id=    payload.order_id,
        species=     payload.species,
        quantity_kg= payload.quantity_kg,
        total_kes=   payload.total_kes,
        reference=   payload.reference,
    )
    return {"success": True, "whatsapp_response": result}


@router.post("/notify/payment-received")
async def send_payment_received(
    payload:     PaymentNotification,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Notify buyer that payment was received."""
    result = await notify_payment_received(
        phone=      payload.phone,
        buyer_name= payload.buyer_name,
        amount_kes= payload.amount_kes,
        reference=  payload.reference,
        order_id=   payload.order_id,
    )
    return {"success": True, "whatsapp_response": result}


@router.post("/notify/dispatched")
async def send_dispatched(
    payload:     DispatchNotification,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Notify buyer that order has been dispatched."""
    result = await notify_order_dispatched(
        phone=               payload.phone,
        buyer_name=          payload.buyer_name,
        order_id=            payload.order_id,
        species=             payload.species,
        driver_name=         payload.driver_name,
        driver_phone=        payload.driver_phone,
        vehicle_reg=         payload.vehicle_reg,
        estimated_delivery=  payload.estimated_delivery,
    )
    return {"success": True, "whatsapp_response": result}


@router.post("/notify/fisher-payout")
async def send_fisher_payout(
    payload:     PayoutNotification,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Notify fisher that payout has been initiated."""
    result = await notify_fisher_payout(
        phone=       payload.phone,
        fisher_name= payload.fisher_name,
        amount_kes=  payload.amount_kes,
        species=     payload.species,
        quantity_kg= payload.quantity_kg,
        reference=   payload.reference,
    )
    return {"success": True, "whatsapp_response": result}


@router.post("/notify/admin-alert")
async def send_admin_alert(
    payload:     AdminAlert,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Send operational alert to admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    result = await notify_admin_alert(
        phone=   payload.phone,
        subject= payload.subject,
        details= payload.details,
    )
    return {"success": True, "whatsapp_response": result}


@router.post("/notify/cold-chain-breach")
async def send_cold_chain_alert(
    payload:     ColdChainAlert,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Alert admin and driver of cold chain breach."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    result = await notify_cold_chain_breach(
        phone=        payload.phone,
        shipment_ref= payload.shipment_ref,
        temperature=  payload.temperature,
        threshold=    payload.threshold,
        driver_name=  payload.driver_name,
    )
    return {"success": True, "whatsapp_response": result}