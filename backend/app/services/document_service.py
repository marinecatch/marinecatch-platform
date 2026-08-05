# app/services/document_service.py
#
# WHY THIS FILE EXISTS:
# Document generation infrastructure for MarineCatch Africa.
# Every commercial transaction produces documents.
#
# This is NOT just "invoice PDFs."
# This is the beginning of commercial documentation infrastructure:
#
# Today:
# - Invoice (buyer pays MarineCatch)
# - Receipt (payment confirmed)
# - Delivery note (goods received)
#
# Future:
# - Catch certificate (traceability)
# - Export documentation (KEBS/EU)
# - ESG compliance pack
# - Eco-label documentation
# - Fisher earnings statement
#
# Architecture:
# Each document is a structured JSON record.
# document_type + order_id + generated_at + content (JSON)
# PDF rendering comes in Phase 8 (dashboards).
#
# Document references follow the format:
# MC-INV-YYYYMMDD-XXXXX (invoice)
# MC-RCP-YYYYMMDD-XXXXX (receipt)
# MC-DLV-YYYYMMDD-XXXXX (delivery note)

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.models.order import Order, OrderStatus
from app.models.payment import PaymentTransaction, PaymentStatus
from app.models.user import User
from app.models.inventory_lot import InventoryLot


# ── DOCUMENT REFERENCE GENERATOR ─────────────────────────────────

def generate_document_reference(doc_type: str, db: Session) -> str:
    """
    Generate unique document reference.
    MC-INV-20260518-00001
    MC-RCP-20260518-00001
    MC-DLV-20260518-00001
    """
    today    = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix   = f"MC-{doc_type.upper()}-{today}"
    sequence = "00001"
    return f"{prefix}-{sequence}"


# ── INVOICE GENERATOR ─────────────────────────────────────────────

def generate_invoice(db: Session, order_id: int) -> dict:
    """
    Generate invoice for an order.
    Issued to institutional buyers after order confirmation.
    Contains full fee breakdown and payment terms.

    Real example:
    Neptune Hotels receives invoice MC-INV-20260518-00001
    for LPO-NEPTUNE-2026-0142, KES 56,675, Net 7 days.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}

    buyer  = db.query(User).filter(User.id == order.buyer_id).first()
    fisher = db.query(User).filter(User.id == order.fisherman_id).first()
    lot    = db.query(InventoryLot).filter(
        InventoryLot.id == order.lot_id
    ).first() if order.lot_id else None

    txn = db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id == order_id
    ).order_by(PaymentTransaction.created_at.desc()).first()

    now       = datetime.now(timezone.utc)
    reference = generate_document_reference("INV", db)

    # Payment due date
    payment_due = None
    if order.payment_terms_days:
        from datetime import timedelta
        payment_due = now + timedelta(days=order.payment_terms_days)

    invoice = {
        "document_type":      "invoice",
        "document_reference": reference,
        "generated_at":       now.isoformat(),
        "status":             "issued",
        "seller": {
            "name":           "MarineCatch Africa Limited",
            "email":          "sales@marinecatchafrica.com",
            "phone":          "+254 798 169 857",
            "address_line1":  "Diani Beach Road", 
            "address_line2":  "Msambweni BMU Offices,Kinondo",
            "po_box":         "P.O. Box 143-80401",
            "location":       "Diani, Kenya",
            "pin":            "P052235582J",
        },

        "buyer": {
            "id":             buyer.id if buyer else None,
            "name":           buyer.name if buyer else None,
            "email":          buyer.email if buyer else None,
            "phone":          buyer.phone if buyer else None,
            "location":       buyer.location if buyer else None,
            "business_name":  buyer.business_name if buyer else None,
        },
        "order": {
            "order_id":       order.id,
            "lpo_reference":  order.lpo_reference,
            "order_source":   order.order_source,
            "order_type":     order.order_type.value,
            "status":         order.status.value,
            "created_at":     order.created_at.isoformat() if order.created_at else None,
        },
        "line_items": [
            {
                "description":    f"{order.species.title()} — {order.quantity_kg}kg",
                "lot_number":     lot.lot_number if lot else None,
                "traceability":   lot.traceability_code if lot else None,
                "landing_site":   lot.landing_site if lot else None,
                "catch_date":     lot.catch_date if lot else None,
                "quantity_kg":    order.quantity_kg,
                "price_per_kg":   order.price_per_kg,
                "subtotal_kes":   round(order.quantity_kg * order.price_per_kg, 2),
            }
        ],
        "fees": {
            "platform_commission_kes": order.platform_fee_kes,
            "commission_rate":         order.commission_rate,
            "storage_fee_kes":         txn.storage_fee_amount if txn else 0,
            "handling_fee_kes":        txn.handling_fee_amount if txn else 0,
            "qa_fee_kes":              txn.qa_fee_amount if txn else 0,
            "logistics_fee_kes":       txn.logistics_fee_amount if txn else 0,
            "tax_kes":                 txn.tax_amount if txn else 0,
        },
        "totals": {
            "subtotal_kes":        round(order.quantity_kg * order.price_per_kg, 2),
            "total_fees_kes":      round(order.total_kes - (order.quantity_kg * order.price_per_kg), 2),
            "total_amount_kes":    order.total_kes,
            "currency":            "KES",
        },
        "payment": {
            "terms_days":          order.payment_terms_days,
            "due_date":            payment_due.isoformat() if payment_due else None,
            "method":              txn.payment_method.value if txn else None,
            "status":              txn.payment_status.value if txn else "pending",
            "reference":           txn.transaction_reference if txn else None,
            "mpesa_receipt":       txn.mpesa_receipt_number if txn else None,
            "paid_at":             txn.paid_at.isoformat() if txn and txn.paid_at else None,
        },
        "supply_chain": {
            "fisher_name":         fisher.name if fisher else None,
            "fisher_phone":        fisher.phone if fisher else None,
            "landing_site":        order.landing_site,
            "species":             order.species,
            "net_to_fisher_kes":   order.net_to_fisher_kes,
        },
        "notes": order.notes,
        "footer": (
            "This invoice is generated by MarineCatch Africa. "
            "For queries contact finance@marinecatch.co.ke. "
            "Payment terms as agreed. Late payments may attract charges."
        ),
    }

    return invoice


# ── RECEIPT GENERATOR ─────────────────────────────────────────────

def generate_receipt(db: Session, order_id: int) -> dict:
    """
    Generate payment receipt after payment is confirmed.
    Simpler than invoice — confirms money received.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}

    txn = db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id    == order_id,
        PaymentTransaction.payment_status == PaymentStatus.PAID,
    ).order_by(PaymentTransaction.created_at.desc()).first()

    if not txn:
        return {"error": "No confirmed payment found for this order"}

    buyer     = db.query(User).filter(User.id == order.buyer_id).first()
    reference = generate_document_reference("RCP", db)
    now       = datetime.now(timezone.utc)

    return {
        "document_type":      "receipt",
        "document_reference": reference,
        "generated_at":       now.isoformat(),
        "buyer_name":         buyer.name if buyer else None,
        "buyer_phone":        buyer.phone if buyer else None,
        "order_id":           order.id,
        "lpo_reference":      order.lpo_reference,
        "species":            order.species,
        "quantity_kg":        order.quantity_kg,
        "amount_paid_kes":    txn.total_amount,
        "payment_method":     txn.payment_method.value,
        "payment_reference":  txn.transaction_reference,
        "mpesa_receipt":      txn.mpesa_receipt_number,
        "paid_at":            txn.paid_at.isoformat() if txn.paid_at else None,
        "confirmed_by":       txn.confirmed_by,
        "message":            "Payment received. Thank you for your business.",
    }


# ── DELIVERY NOTE GENERATOR ───────────────────────────────────────

def generate_delivery_note(db: Session, order_id: int) -> dict:
    """
    Generate delivery note when order is dispatched.
    Travels with the fish — buyer signs on receipt.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": f"Order {order_id} not found"}

    buyer  = db.query(User).filter(User.id == order.buyer_id).first()
    fisher = db.query(User).filter(User.id == order.fisherman_id).first()
    lot    = db.query(InventoryLot).filter(
        InventoryLot.id == order.lot_id
    ).first() if order.lot_id else None

    reference = generate_document_reference("DLV", db)
    now       = datetime.now(timezone.utc)

    return {
        "document_type":      "delivery_note",
        "document_reference": reference,
        "generated_at":       now.isoformat(),
        "order_id":           order.id,
        "lpo_reference":      order.lpo_reference,
        "deliver_to": {
            "name":           buyer.name if buyer else None,
            "phone":          buyer.phone if buyer else None,
            "address":        order.delivery_address,
            "location":       buyer.location if buyer else None,
        },
        "dispatched_from": {
            "landing_site":   order.landing_site,
            "fisher_name":    fisher.name if fisher else None,
            "lot_number":     lot.lot_number if lot else None,
        },
        "goods": {
            "species":          order.species,
            "quantity_kg":      order.quantity_kg,
            "condition":        lot.condition.value if lot else None,
            "grade":            lot.grade.value if lot else None,
            "traceability_code": lot.traceability_code if lot else None,
            "catch_date":       lot.catch_date if lot else None,
            "estimated_expiry": lot.estimated_expiry.isoformat() if lot and lot.estimated_expiry else None,
        },
        "instructions": (
            "Please inspect goods on receipt. "
            "Sign and return copy to driver. "
            "Report any discrepancies within 2 hours of delivery."
        ),
        "receiver_signature": None,
        "received_at":        None,
    }