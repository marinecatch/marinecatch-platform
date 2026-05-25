# app/services/whatsapp_service.py
#
# WHY THIS FILE EXISTS:
# WhatsApp Cloud API integration for MarineCatch Africa.
# ONE BACKEND — MANY INTERFACES principle.
# WhatsApp calls existing services — never duplicates logic.
#
# Supports:
# - Outgoing notifications (orders, payments, shipments, payouts)
# - Incoming message routing (buyer queries, fisher updates)
# - Menu systems (structured conversations)
# - Template messages (transactional notifications)
#
# Message types:
# - Text: simple notifications
# - Template: pre-approved transactional messages
# - Interactive: buttons and lists for menus
#
# Architecture:
# whatsapp_service → sends/receives messages
# whatsapp routes → handles webhooks
# existing services → business logic (never duplicated here)

import httpx
from app.config import settings


# ── BASE URL ──────────────────────────────────────────────────────

def get_whatsapp_url() -> str:
    return (
        f"https://graph.facebook.com/"
        f"{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type":  "application/json",
    }


# ── SEND TEXT MESSAGE ─────────────────────────────────────────────

async def send_text(phone: str, message: str) -> dict:
    """
    Send a plain text message to a WhatsApp number.
    phone: format 254XXXXXXXXX (no + sign)
    """
    phone = phone.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                phone,
        "type":              "text",
        "text":              {"body": message}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            get_whatsapp_url(),
            json=payload,
            headers=get_headers(),
            timeout=30.0
        )
        return response.json()


# ── SEND INTERACTIVE MENU ─────────────────────────────────────────

async def send_menu(
    phone:   str,
    header:  str,
    body:    str,
    footer:  str,
    buttons: list,
) -> dict:
    """
    Send an interactive button menu.
    Max 3 buttons per message.
    buttons: [{"id": "btn_1", "title": "View Fish"}]
    """
    phone = phone.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                phone,
        "type":              "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": header
            },
            "body":   {"text": body},
            "footer": {"text": footer},
            "action": {
                "buttons": [
                    {
                        "type":  "reply",
                        "reply": {
                            "id":    btn["id"],
                            "title": btn["title"]
                        }
                    }
                    for btn in buttons[:3]
                ]
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            get_whatsapp_url(),
            json=payload,
            headers=get_headers(),
            timeout=30.0
        )
        return response.json()


# ── SEND LIST MENU ────────────────────────────────────────────────

async def send_list_menu(
    phone:    str,
    header:   str,
    body:     str,
    footer:   str,
    button:   str,
    sections: list,
) -> dict:
    """
    Send an interactive list menu.
    Good for showing inventory or order options.
    sections: [{"title": "Available Fish", "rows": [{"id": "r1", "title": "Tuna", "description": "85kg @ KES 780/kg"}]}]
    """
    phone = phone.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                phone,
        "type":              "interactive",
        "interactive": {
            "type":   "list",
            "header": {"type": "text", "text": header},
            "body":   {"text": body},
            "footer": {"text": footer},
            "action": {
                "button":   button,
                "sections": sections
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            get_whatsapp_url(),
            json=payload,
            headers=get_headers(),
            timeout=30.0
        )
        return response.json()


# ── NOTIFICATION TEMPLATES ────────────────────────────────────────
# These are the key business notifications MarineCatch sends.
# All call send_text — template approval comes later for production.

async def notify_order_confirmed(
    phone:      str,
    buyer_name: str,
    order_id:   int,
    species:    str,
    quantity_kg: float,
    total_kes:  float,
    reference:  str,
) -> dict:
    """Notify buyer when their order is confirmed."""
    message = (
        f"✅ *Order Confirmed — MarineCatch Africa*\n\n"
        f"Hello {buyer_name},\n\n"
        f"Your order has been confirmed:\n"
        f"• Order ID: #{order_id}\n"
        f"• Species: {species.title()}\n"
        f"• Quantity: {quantity_kg}kg\n"
        f"• Total: KES {total_kes:,.0f}\n"
        f"• Reference: {reference}\n\n"
        f"We will notify you when your order is dispatched.\n\n"
        f"MarineCatch Africa 🐟"
    )
    return await send_text(phone, message)


async def notify_payment_received(
    phone:      str,
    buyer_name: str,
    amount_kes: float,
    reference:  str,
    order_id:   int,
) -> dict:
    """Notify buyer when payment is confirmed."""
    message = (
        f"💰 *Payment Received — MarineCatch Africa*\n\n"
        f"Hello {buyer_name},\n\n"
        f"We have received your payment:\n"
        f"• Amount: KES {amount_kes:,.0f}\n"
        f"• Reference: {reference}\n"
        f"• Order ID: #{order_id}\n\n"
        f"Your order is now being prepared.\n\n"
        f"MarineCatch Africa 🐟"
    )
    return await send_text(phone, message)


async def notify_order_dispatched(
    phone:        str,
    buyer_name:   str,
    order_id:     int,
    species:      str,
    driver_name:  str,
    driver_phone: str,
    vehicle_reg:  str,
    estimated_delivery: str,
) -> dict:
    """Notify buyer when order is dispatched."""
    message = (
        f"🚚 *Order Dispatched — MarineCatch Africa*\n\n"
        f"Hello {buyer_name},\n\n"
        f"Your {species.title()} (Order #{order_id}) is on its way!\n\n"
        f"*Driver Details:*\n"
        f"• Name: {driver_name}\n"
        f"• Phone: {driver_phone}\n"
        f"• Vehicle: {vehicle_reg}\n"
        f"• Est. Delivery: {estimated_delivery}\n\n"
        f"Please ensure someone is available to receive the order.\n\n"
        f"MarineCatch Africa 🐟"
    )
    return await send_text(phone, message)


async def notify_fisher_payout(
    phone:        str,
    fisher_name:  str,
    amount_kes:   float,
    species:      str,
    quantity_kg:  float,
    reference:    str,
) -> dict:
    """Notify fisher when their payout is initiated."""
    message = (
        f"💚 *Payout Initiated — MarineCatch Africa*\n\n"
        f"Habari {fisher_name},\n\n"
        f"Malipo yako yametumwa:\n"
        f"• Kiasi: KES {amount_kes:,.0f}\n"
        f"• Samaki: {species.title()} ({quantity_kg}kg)\n"
        f"• Kumbukumbu: {reference}\n\n"
        f"Pesa itafika kwenye M-Pesa yako hivi karibuni.\n\n"
        f"Asante kwa kazi yako! 🐟\n"
        f"MarineCatch Africa"
    )
    return await send_text(phone, message)


async def notify_admin_alert(
    phone:   str,
    subject: str,
    details: str,
) -> dict:
    """Send operational alert to admin."""
    message = (
        f"🔔 *Admin Alert — MarineCatch Africa*\n\n"
        f"*{subject}*\n\n"
        f"{details}\n\n"
        f"— MarineCatch System"
    )
    return await send_text(phone, message)


async def notify_cold_chain_breach(
    phone:         str,
    shipment_ref:  str,
    temperature:   float,
    threshold:     float,
    driver_name:   str,
) -> dict:
    """Alert admin/driver of cold chain breach."""
    message = (
        f"🚨 *COLD CHAIN BREACH — MarineCatch Africa*\n\n"
        f"Shipment: {shipment_ref}\n"
        f"Temperature: {temperature}°C (Threshold: {threshold}°C)\n"
        f"Driver: {driver_name}\n\n"
        f"*Immediate action required.*\n"
        f"Check refrigeration unit and contact operations team.\n\n"
        f"MarineCatch Africa — Operations"
    )
    return await send_text(phone, message)


# ── INCOMING MESSAGE PARSER ───────────────────────────────────────

def parse_incoming_message(webhook_data: dict) -> dict:
    """
    Parse incoming WhatsApp webhook payload.
    Returns structured message data for routing.
    """
    try:
        entry   = webhook_data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value   = changes.get("value", {})

        messages = value.get("messages", [])
        if not messages:
            return {"type": "no_message"}

        msg     = messages[0]
        from_phone = msg.get("from", "")
        msg_type   = msg.get("type", "")
        msg_id     = msg.get("id", "")

        result = {
            "from_phone": from_phone,
            "msg_type":   msg_type,
            "msg_id":     msg_id,
            "text":       None,
            "button_id":  None,
            "list_id":    None,
        }

        if msg_type == "text":
            result["text"] = msg.get("text", {}).get("body", "").strip()

        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            itype = interactive.get("type", "")
            if itype == "button_reply":
                result["button_id"] = interactive.get("button_reply", {}).get("id")
                result["text"]      = interactive.get("button_reply", {}).get("title")
            elif itype == "list_reply":
                result["list_id"] = interactive.get("list_reply", {}).get("id")
                result["text"]    = interactive.get("list_reply", {}).get("title")

        return result

    except Exception as e:
        return {"type": "parse_error", "error": str(e)}