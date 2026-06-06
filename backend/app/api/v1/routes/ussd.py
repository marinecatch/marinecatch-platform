# app/api/v1/routes/ussd.py
#
# WHY THIS FILE EXISTS:
# USSD webhook handler for Africa's Talking integration.
# Receives POST requests from AT servers on every keypress.
# Returns CON (continue) or END (terminate) plain text responses.
#
# Africa's Talking sends:
# sessionId, serviceCode, phoneNumber, text
#
# We respond with plain text:
# CON <message> → keep session open
# END <message> → close session

from fastapi import APIRouter, Form, Response
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database.connection import get_db
from app.services.ussd_service import handle_ussd

router = APIRouter(prefix="/ussd", tags=["USSD"])


@router.post("/")
async def ussd_handler(
    sessionId:   str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text:        str = Form(default=""),
    db: Session      = Depends(get_db),
):
    """
    Africa's Talking USSD callback endpoint.
    Called on every user interaction.
    Must respond within 5 seconds.
    Response must be plain text starting with CON or END.
    """
    response_text = handle_ussd(
        db=           db,
        session_id=   sessionId,
        phone_number= phoneNumber,
        text=         text,
    )

    # AT requires plain text response — not JSON
    return Response(
        content=response_text,
        media_type="text/plain"
    )