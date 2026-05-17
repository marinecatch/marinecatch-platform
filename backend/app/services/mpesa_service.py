# app/services/mpesa_service.py
#
# WHY THIS FILE EXISTS:
# All M-Pesa API calls live here.
# Routes and services call these functions.
# Never put M-Pesa logic directly in routes.
#
# Supports:
# - STK Push (buyer pays from their phone)
# - B2C (MarineCatch pays fisher)
# - Token generation (OAuth)
#
# Sandbox base URL: https://sandbox.safaricom.co.ke
# Production base URL: https://api.safaricom.co.ke

import httpx
import base64
from datetime import datetime, timezone
from app.config import settings

# ── BASE URL ──────────────────────────────────────────────────────
def get_base_url() -> str:
    if settings.MPESA_ENVIRONMENT == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"

# ── TOKEN CACHE ───────────────────────────────────────────────────
# Cache token to avoid calling Safaricom on every request
_token_cache = {"token": None, "expires_at": None}

async def get_access_token() -> str:
    """
    Get OAuth access token from Safaricom.
    Token valid for 1 hour — cached to avoid repeated calls.
    """
    now = datetime.now(timezone.utc).timestamp()

    # Return cached token if still valid
    if _token_cache["token"] and _token_cache["expires_at"]:
        if now < _token_cache["expires_at"] - 60:
            return _token_cache["token"]

    # Generate new token
    credentials = base64.b64encode(
        f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{get_base_url()}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"},
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()

    _token_cache["token"]      = data["access_token"]
    _token_cache["expires_at"] = now + int(data.get("expires_in", 3600))

    return _token_cache["token"]

# ── STK PUSH ──────────────────────────────────────────────────────
async def stk_push(
    phone_number: str,
    amount: float,
    transaction_reference: str,
    description: str
) -> dict:
    """
    Send STK Push to buyer's phone.
    Buyer sees a payment prompt and enters their M-Pesa PIN.

    phone_number: format 254XXXXXXXXX (no + sign)
    amount: in KES (rounded to integer)
    transaction_reference: your internal reference e.g. MC-PAY-20260514-001
    description: short description shown on buyer's phone

    Returns Safaricom's response with CheckoutRequestID.
    Store CheckoutRequestID — you need it to check payment status.
    """
    token     = await get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Password = base64(shortcode + passkey + timestamp)
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password     = base64.b64encode(password_str.encode()).decode()

    # Clean phone number
    phone = phone_number.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            int(round(amount)),
        "PartyA":            phone,
        "PartyB":            settings.MPESA_SHORTCODE,
        "PhoneNumber":       phone,
        "CallBackURL":       settings.MPESA_CALLBACK_URL,
        "AccountReference":  transaction_reference[:12],
        "TransactionDesc":   description[:13],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

# ── STK QUERY ─────────────────────────────────────────────────────
async def stk_query(checkout_request_id: str) -> dict:
    """
    Check the status of an STK Push request.
    Call this if callback doesn't arrive within 30 seconds.
    """
    token     = await get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password     = base64.b64encode(password_str.encode()).decode()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/mpesa/stkpushquery/v1/query",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
# ── B2C PAYOUT ────────────────────────────────────────────────────
async def b2c_payment(
    phone_number: str,
    amount: float,
    transaction_reference: str,
    remarks: str = "Fisher payout"
) -> dict:
    """
    Send money from MarineCatch to fisher's M-Pesa.
    Called after order is delivered and buyer payment confirmed.
    Uses B2C (Business to Customer) API.
    """
    token = await get_access_token()

    phone = phone_number.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    payload = {
        "InitiatorName":      settings.MPESA_INITIATOR_NAME,
        "SecurityCredential": settings.MPESA_SECURITY_CREDENTIAL,
        "CommandID":          "BusinessPayment",
        "Amount":             int(round(amount)),
        "PartyA":             settings.MPESA_B2C_SHORTCODE,
        "PartyB":             phone,
        "Remarks":            remarks[:100],
        "QueueTimeOutURL":    settings.MPESA_CALLBACK_URL + "/b2c/timeout",
        "ResultURL":          settings.MPESA_CALLBACK_URL + "/b2c/result",
        "Occasion":           transaction_reference[:40],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/mpesa/b2c/v1/paymentrequest",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()