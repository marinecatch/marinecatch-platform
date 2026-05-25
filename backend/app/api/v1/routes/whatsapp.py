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
    """
    Handle incoming WhatsApp messages.
    Routes based on message content to appropriate service.
    Always returns 200 to Meta — never let Meta retry.
    """
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

    # Route incoming messages
    await route_incoming_message(
        db=db,
        from_phone=from_phone,
        text=text,
        button_id=button_id,
    )

    # Always return 200 to Meta
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
    AI-powered routing comes later.
    """
    from app.services.inventory_service import get_available_lots

    # Main menu triggers
    if text in ["hi", "hello", "habari", "menu", "start", "help"]:
        await send_menu(
            phone=  from_phone,
            header= "MarineCatch Africa 🐟",
            body=   "Welcome! How can we help you today?",
            footer= "Reply with a number or tap a button",
            buttons=[
                {"id": "btn_fish",   "title": "🐟 View Available Fish"},
                {"id": "btn_orders", "title": "📦 My Orders"},
                {"id": "btn_support","title": "💬 Contact Support"},
            ]
        )
        return

    # Fish availability
    if text in ["fish", "samaki", "available", "stock"] or button_id == "btn_fish":
        lots = get_available_lots(db, limit=5)
        if not lots:
            await send_text(from_phone, "No fish available right now. Please check again later.")
            return

        lines = ["*Available Seafood — MarineCatch Africa* 🐟\n"]
        for lot in lots:
            lines.append(
                f"• *{lot.species.title()}* — {lot.available_kg}kg\n"
                f"  KES {lot.selling_price_per_kg}/kg | {lot.landing_site.title()}\n"
                f"  Lot: {lot.lot_number}"
            )
        lines.append("\nReply with species name for details or type MENU to go back.")
        await send_text(from_phone, "\n".join(lines))
        return

    # Species-specific lookup
    species_list = ["tuna", "octopus", "prawns", "lobster", "snapper",
                    "kingfish", "sardines", "crab"]
    if text in species_list:
        lots = get_available_lots(db, species=text, limit=3)
        if not lots:
            await send_text(
                from_phone,
                f"No {text.title()} available right now. Type MENU to see all available fish."
            )
            return

        lines = [f"*{text.title()} Available* 🐟\n"]
        for lot in lots:
            lines.append(
                f"• {lot.available_kg}kg at KES {lot.selling_price_per_kg}/kg\n"
                f"  Grade: {lot.grade} | {lot.condition.title()}\n"
                f"  Location: {lot.landing_site.title()}\n"
                f"  Lot: {lot.lot_number}\n"
                f"  Expires: {lot.estimated_expiry.strftime('%d %b %Y') if lot.estimated_expiry else 'N/A'}"
            )
        lines.append("\nTo place an order, contact us or visit marinecatch.co.ke")
        await send_text(from_phone, "\n".join(lines))
        return

    # Support
    if text in ["support", "help", "msaada"] or button_id == "btn_support":
        await send_text(
            from_phone,
            "📞 *MarineCatch Africa Support*\n\n"
            "For orders and procurement:\n"
            "📧 orders@marinecatch.co.ke\n\n"
            "For payments and invoices:\n"
            "📧 finance@marinecatch.co.ke\n\n"
            "Our team is available Mon-Sat, 6am-8pm.\n\n"
            "Type MENU to return to main menu."
        )
        return

    # Default response
    await send_text(
        from_phone,
        "Sorry, I didn't understand that. 🤔\n\n"
        "Type *MENU* to see options or *FISH* to view available seafood.\n\n"
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