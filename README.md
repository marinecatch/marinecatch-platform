#markdown
# MarineCatch Africa — Backend Platform

Seafood supply chain and traceability infrastructure for Kenya and the Western Indian Ocean.

## What This Is

MarineCatch Africa is not a marketplace. It is multi-channel seafood infrastructure connecting:

- Small-scale fishers at landing sites (Kibuyuni, Shimoni, Vanga, Gazi, Kinondo)
- Aggregators and suppliers
- Hotels, restaurants, and wholesalers
- Processors and exporters (Sea Harvest, Alpha Seafood)
- Regulators and ESG stakeholders

## Business Modes

**Mode 1 — Marketplace**: Fisher lists catch, buyer orders, MarineCatch earns commission.

**Mode 2 — Direct Procurement**: MarineCatch buys fish outright and resells at margin.

**Mode 3 — Fulfillment Contracts**: Hotels and processors place recurring orders,
MarineCatch aggregates supply from multiple fishers.

## Tech Stack

- FastAPI + Python 3.11+
- PostgreSQL (local dev) → AWS RDS (production)
- SQLAlchemy + Alembic
- JWT authentication
- M-Pesa STK Push (Phase 2)

## Project Structure
backend/
├── app/
│   ├── api/v1/routes/     # HTTP endpoints
│   │   ├── users.py
│   │   ├── inventory.py
│   │   ├── orders.py
│   │   └── fish.py
│   ├── models/            # SQLAlchemy models
│   │   ├── user.py
│   │   ├── inventory_lot.py
│   │   ├── cold_storage.py
│   │   └── order.py
│   ├── services/          # Business logic
│   │   ├── user_service.py
│   │   ├── inventory_service.py
│   │   └── order_service.py
│   └── main.py
├── alembic/               # Database migrations
└── requirements.txt

## Running Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

API docs: http://localhost:8080/docs
Health check: http://localhost:8080/health

## Database

PostgreSQL. All migrations managed with Alembic.

Run migrations: `alembic upgrade head`

Check history: `alembic history`

## Current Status — Phase 1 Complete (Day 20)

### Completed
- User registration and JWT authentication
- InventoryLot model — full lifecycle with ESG fields
- ColdStorage model
- Inventory service — create, reserve, release, deduct, fee calculation
- Inventory routes — browse, create, reserve, release, quote
- Order model — full status lifecycle (pending_payment → completed)
- Order service — atomic placement, cancellation, confirmation, status transitions
- Order routes — place, cancel, confirm, status update
- End-to-end test — Neptune Hotels ordered 20kg tuna from Bakari Usi, KES 15,990

### Roadmap
- Phase 2 (Days 21–30): M-Pesa STK Push + B2C payouts
- Phase 3 (Days 31–38): Logistics and cold chain movement
- Phase 4 (Days 39–46): ESG reporting and traceability
- Phase 5 (Days 47–52): WhatsApp integration
- Phase 6 (Days 53–58): USSD for remote fishers
- Phase 7 (Days 59–65): AWS deployment
- Phase 8 (Days 66–72): React dashboards
- Launch: 24 July 2026

## Architectural Rules

1. One backend, many interfaces — WhatsApp, USSD, web, mobile all hit the same API
2. InventoryLot is the backbone — every piece of seafood flows through it
3. ownership_type drives money flow — marketplace vs MarineCatch-owned changes everything
4. Status over booleans — never `is_sold = True`, always `status = "sold"`
5. Build now, surface later — ESG data captured in every transaction
6. No premature microservices — one FastAPI monolith, modular internally MarineCatch Africa Platform
