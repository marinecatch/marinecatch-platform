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
    Uses client credentials grant.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/token?grant_type=client_credentials",
            auth=(settings.KCB_CONSUMER_KEY, settings.KCB_CONSUMER_SECRET),
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

async def initiate_bank_transfer(
    amount:            float,
    destination_account: str,
    destination_bank_code: str,
    reference:         str,
    narrative:         str,
) -> dict:
    """
    Initiate a bank transfer for large B2B payments.

    Use case: Processor or exporter pays MarineCatch KES 500K+
    for a bulk seafood order — too large for M-Pesa STK Push.

    Use case: MarineCatch pays a large supplier (like Shimoni
    aggregator) via bank transfer instead of M-Pesa B2C.
    """
    token = await get_access_token()

    payload = {
        "sourceAccount":      settings.KCB_ACCOUNT_NUMBER,
        "destinationAccount": destination_account,
        "destinationBankCode": destination_bank_code,
        "amount":             amount,
        "currency":           "KES",
        "reference":          reference,
        "narrative":          narrative,
        "callbackUrl":        settings.KCB_CALLBACK_URL,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{get_base_url()}/mm/api/v1/transfer",
            headers={"Authorization": f"Bearer {token}"},
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
    Parse incoming KCB payment confirmation webhook.
    Called from the payments route when KCB confirms a transfer.
    """
    return {
        "reference":     payload.get("reference"),
        "amount":        payload.get("amount"),
        "status":        payload.get("status"),
        "transaction_id": payload.get("transactionId"),
        "timestamp":     payload.get("timestamp", datetime.now().isoformat()),
    }