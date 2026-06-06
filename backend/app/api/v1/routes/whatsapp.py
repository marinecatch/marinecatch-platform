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
    """
    Route incoming message to appropriate handler.
    Keyword-based routing for MVP.
    """
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
            "To order: type *ORDER tuna 20* (species + kg)"
        )
        await send_text(from_phone, "\n".join(lines))
        return

    # ── SPECIES LOOKUP ────────────────────────────────────────
    species_list = ["tuna", "octopus", "prawns", "lobster",
                    "snapper", "kingfish", "sardines", "crab"]
    if text in species_list:
        lots = get_available_lots(db, species=text, limit=3)
        if not lots:
            await send_text(
                from_phone,
                f"No {text.title()} available right now.\n\n"
                f"Type FISH to see all available species.\n"
                f"Type MENU to go back."
            )
            return

        lines = [f"*{text.title()} Available* 🐟\n"]
        for lot in lots:
            lines.append(
                f"• {lot.available_kg}kg @ KES {lot.selling_price_per_kg}/kg\n"
                f"  Grade: {lot.grade} | {lot.condition.title()}\n"
                f"  Location: {lot.landing_site.title()}\n"
                f"  Lot: {lot.lot_number}"
            )
        lines.append(
            f"\nTo order: type *ORDER {text} 20* (replace 20 with kg you need)"
        )
        await send_text(from_phone, "\n".join(lines))
        return

    # ── ORDER STATUS LOOKUP ───────────────────────────────────
    if text.startswith("order status") or text.startswith("status"):
        # Extract order ID — "order status 5" or "status 5"
        parts = text.split()
        order_id = None
        for part in parts:
            if part.isdigit():
                order_id = int(part)
                break

        if not order_id:
            await send_text(
                from_phone,
                "To check your order status, type:\n"
                "*ORDER STATUS 5* (replace 5 with your order ID)\n\n"
                "Type MENU to go back."
            )
            return

        # Find the order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await send_text(
                from_phone,
                f"Order #{order_id} not found.\n\n"
                "Please check your order ID and try again.\n"
                "Type MENU to go back."
            )
            return

        # Find buyer to verify ownership
        buyer = db.query(User).filter(User.id == order.buyer_id).first()
        lot   = db.query(InventoryLot).filter(
            InventoryLot.id == order.lot_id
        ).first() if order.lot_id else None

        status_emoji = {
            "pending_payment": "⏳",
            "confirmed":       "✅",
            "preparing":       "🔧",
            "dispatched":      "🚚",
            "delivered":       "📦",
            "completed":       "✅",
            "cancelled":       "❌",
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
        if lot:
            message += f"• Lot: {lot.lot_number}\n"

        message += "\nType MENU to go back."
        await send_text(from_phone, message)
        return

    # ── ORDER PLACEMENT REQUEST ───────────────────────────────
    if text.startswith("order "):
        parts = text.split()
        # Expected: "order tuna 20" or "order prawns 50"
        if len(parts) >= 3 and parts[1] in species_list and parts[2].isdigit():
            species    = parts[1]
            quantity   = int(parts[2])

            # Check availability
            lots = get_available_lots(db, species=species, limit=1)
            if not lots:
                await send_text(
                    from_phone,
                    f"Sorry, no {species.title()} available right now.\n\n"
                    "Type FISH to see what's available.\n"
                    "Type MENU to go back."
                )
                return

            lot        = lots[0]
            total_kes  = quantity * lot.selling_price_per_kg

            if quantity > lot.available_kg:
                await send_text(
                    from_phone,
                    f"Only {lot.available_kg}kg of {species.title()} available.\n\n"
                    f"To order {lot.available_kg}kg, type:\n"
                    f"*ORDER {species} {int(lot.available_kg)}*\n\n"
                    "Type MENU to go back."
                )
                return

            await send_text(
                from_phone,
                f"📋 *Order Request Received*\n\n"
                f"• Species: {species.title()}\n"
                f"• Quantity: {quantity}kg\n"
                f"• Price: KES {lot.selling_price_per_kg}/kg\n"
                f"• Total: KES {total_kes:,.0f}\n"
                f"• Location: {lot.landing_site.title()}\n\n"
                f"Our team will contact you within 30 minutes to confirm.\n\n"
                f"For urgent orders call: +254700000000\n\n"
                f"Reference: {lot.lot_number}\n"
                f"MarineCatch Africa 🐟"
            )
            return

        # Malformed order command
        await send_text(
            from_phone,
            "To place an order, type:\n"
            "*ORDER species kg*\n\n"
            "Examples:\n"
            "• ORDER tuna 20\n"
            "• ORDER prawns 50\n"
            "• ORDER octopus 10\n\n"
            "Type FISH to see available species."
        )
        return

    # ── MY ORDERS ─────────────────────────────────────────────
    if text in ["my orders", "orders"] or button_id == "btn_orders":
        await send_text(
            from_phone,
            "📦 *Check Your Order Status*\n\n"
            "Type your order ID to get status:\n"
            "*ORDER STATUS 1* (replace 1 with your order ID)\n\n"
            "Don't have your order ID?\n"
            "Contact us: orders@marinecatch.co.ke\n\n"
            "Type MENU to go back."
        )
        return

    # ── PRICE INQUIRY ─────────────────────────────────────────
    if text.startswith("price") or text.startswith("bei"):
        parts = text.split()
        if len(parts) >= 2 and parts[1] in species_list:
            species = parts[1]
            lots    = get_available_lots(db, species=species, limit=1)
            if lots:
                lot = lots[0]
                await send_text(
                    from_phone,
                    f"💰 *{species.title()} Price*\n\n"
                    f"• Current price: KES {lot.selling_price_per_kg}/kg\n"
                    f"• Available: {lot.available_kg}kg\n"
                    f"• Grade: {lot.grade}\n"
                    f"• Location: {lot.landing_site.title()}\n\n"
                    f"To order: *ORDER {species} 20*\n"
                    f"Type MENU to go back."
                )
            else:
                await send_text(
                    from_phone,
                    f"No {species.title()} available right now.\n"
                    "Type FISH to see all available species."
                )
            return

        await send_text(
            from_phone,
            "💰 *Price Inquiry*\n\n"
            "Type: *PRICE species*\n\n"
            "Examples:\n"
            "• PRICE tuna\n"
            "• PRICE prawns\n"
            "• PRICE octopus\n\n"
            "Type FISH to see all available fish with prices."
        )
        return

    # ── SUPPORT ───────────────────────────────────────────────
    if text in ["support", "help", "msaada"] or button_id == "btn_support":
        await send_text(
            from_phone,
            "📞 *MarineCatch Africa Support*\n\n"
            "Orders & Procurement:\n"
            "📧 orders@marinecatch.co.ke\n\n"
            "Payments & Invoices:\n"
            "📧 finance@marinecatch.co.ke\n\n"
            "Available Mon-Sat, 6am-8pm EAT\n\n"
            "Type MENU to return to main menu."
        )
        return

    # ── DEFAULT ───────────────────────────────────────────────
    await send_text(
        from_phone,
        "Sorry, I didn't understand that. 🤔\n\n"
        "Type *MENU* for options\n"
        "Type *FISH* to see available seafood\n"
        "Type *PRICE tuna* for price inquiry\n"
        "Type *ORDER tuna 20* to place an order\n"
        "Type *ORDER STATUS 1* to check order status\n\n"
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