# app/services/kcb_service.py
#
# WHY THIS FILE EXISTS:
# KCB Buni API integration for bank transfer payments.
# Complements M-Pesa for large B2B transactions — processors
# and exporters paying KES 500K+ typically prefer bank transfer
# over STK Push limits.
#
# This is a skeleton — no live credentials yet.
# Architecture mirrors mpesa_service.py so the pattern is
# consistent across payment providers.
#
# KCB Buni API docs: https://buni.kcbgroup.com
#
# Endpoints this will support once credentials are issued:
# - Account balance query
# - Bank transfer / EFT payment initiation
# - Payment status query
# - Webhook callback for payment confirmation

import httpx
import base64
from datetime import datetime
from app.config import settings


# ── ENVIRONMENT ────────────────────────────────────────────────────
# Sandbox base URL: https://uat.buni.kcbgroup.com
# Production base URL: https://api.buni.kcbgroup.com

def get_base_url() -> str:
    if settings.KCB_ENVIRONMENT == "production":
        return "https://api.buni.kcbgroup.com"
    return "https://uat.buni.kcbgroup.com"


# ── AUTHENTICATION ───────────────────────────────────────────────

async def get_access_token() -> str:
    """
    Get OAuth access token from KCB Buni API.
    Uses Basic Auth (consumer_key:consumer_secret) with
    client_credentials grant — per KCB spec.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/token?grant_type=client_credentials",
            auth=(settings.KCB_CONSUMER_KEY, settings.KCB_CONSUMER_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()["access_token"]


# ── ACCOUNT BALANCE ───────────────────────────────────────────────

async def check_account_balance() -> dict:
    """
    Query MarineCatch's KCB account balance.
    Used before initiating large payouts to confirm funds available.
    """
    token = await get_access_token()

    payload = {
        "accountNumber": settings.KCB_ACCOUNT_NUMBER,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/mm/api/v1/balance",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()


# ── BANK TRANSFER / EFT ───────────────────────────────────────────

async def initiate_stk_push(
    phone_number: str,
    amount: float,
    invoice_number: str,
    transaction_description: str = "MarineCatch seafood order",
) -> dict:
    """
    Initiate M-Pesa Express (STK Push) via KCB paybill 522533.

    invoice_number format required by KCB: KCBTILLNO-YOURACCREF
    e.g. "522533-MC-INV-20260724-0001"
    """
    token = await get_access_token()

    payload = {
        "phoneNumber": phone_number,
        "amount": str(amount),
        "invoiceNumber": invoice_number,
        "sharedShortCode": True,
        "orgShortCode": "",
        "orgPassKey": "",
        "callbackUrl": settings.KCB_CONFIRM_URL,
        "transactionDescription": transaction_description,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/mm/api/request/1.0.0/stkpush",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "accept": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()


# ── PAYBILL / C2B — KCB PAYBILL FOR BUYERS ────────────────────────

async def register_paybill_urls() -> dict:
    """
    Register validation and confirmation URLs for KCB Paybill.
    One-time setup — allows buyers to pay via KCB Paybill
    instead of M-Pesa.
    """
    token = await get_access_token()

    payload = {
        "shortCode":       settings.KCB_PAYBILL_NUMBER,
        "validationUrl":   settings.KCB_VALIDATION_URL,
        "confirmationUrl": settings.KCB_CONFIRMATION_URL,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/mm/api/v1/paybill/register",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()


# ── PAYMENT STATUS QUERY ──────────────────────────────────────────

async def query_transaction_status(reference: str) -> dict:
    """Check the status of a previously initiated transfer."""
    token = await get_access_token()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{get_base_url()}/mm/api/v1/transaction/{reference}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


# ── WEBHOOK HANDLER HELPER ────────────────────────────────────────

def parse_kcb_callback(payload: dict) -> dict:
    """
    Parse the real KCB M-Pesa Express STK callback payload.

    Success structure:
    {
      "Body": {"stkCallback": {
        "MerchantRequestID", "CheckoutRequestID",
        "ResultCode": 0, "ResultDesc",
        "CallbackMetadata": {"Item": [
          {"Name": "Amount", "Value": 1.00},
          {"Name": "MpesaReceiptNumber", "Value": "ABCDE12345"},
          {"Name": "TransactionDate", "Value": 20230721153232},
          {"Name": "PhoneNumber", "Value": 254700000000}
        ]}
      }}
    }

    Failure structure omits CallbackMetadata, ResultCode != 0.
    """
    stk = payload.get("Body", {}).get("stkCallback", {})
    result_code = stk.get("ResultCode")
    result_desc = stk.get("ResultDesc")

    parsed = {
        "merchant_request_id": stk.get("MerchantRequestID"),
        "checkout_request_id": stk.get("CheckoutRequestID"),
        "success": result_code == 0,
        "result_code": result_code,
        "result_desc": result_desc,
        "amount": None,
        "mpesa_receipt": None,
        "transaction_date": None,
        "phone_number": None,
    }

    if result_code == 0:
        items = stk.get("CallbackMetadata", {}).get("Item", [])
        for item in items:
            name = item.get("Name")
            value = item.get("Value")
            if name == "Amount":
                parsed["amount"] = value
            elif name == "MpesaReceiptNumber":
                parsed["mpesa_receipt"] = value
            elif name == "TransactionDate":
                parsed["transaction_date"] = value
            elif name == "PhoneNumber":
                parsed["phone_number"] = value

    return parsed