# MarineCatch Africa Platform

**Digital infrastructure for seafood sourcing, trading and supply-chain coordination in Africa.**

[Website](https://marinecatchafrica.com) | [Buyer Portal](https://marinecatchafrica.com/buyer) | [GitHub](https://github.com/marinecatch/marinecatch-platform)

## Overview

MarineCatch Africa is a Kenyan seafood sourcing, distribution and technology business connecting small-scale fishers, seafood suppliers and dealers with hotels, restaurants, wholesalers, retailers, processors and consumers.

We operate within the seafood value chain and are developing digital infrastructure to address practical challenges encountered in seafood procurement and distribution, including fragmented supply, limited inventory visibility, inconsistent supplier information, order coordination, payment tracking and fulfilment.

The MarineCatch platform was developed from our direct operating experience in the seafood trade. It supports our existing procurement and distribution activities while providing infrastructure for a broader marketplace connecting suppliers and buyers.

The platform has been live since July 2026.

## What the platform does

The application is designed around three primary user groups:

### 1. Buyers
- Browse available seafood inventory.
- View product and supplier information.
- Submit orders.
- Track order and payment status.
- Access digital purchasing workflows.

### 2. Fishers and suppliers
- Maintain supplier and compliance profiles.
- Submit catch and inventory information.
- List seafood for sale.
- Manage available quantities and product details.
- Participate in order fulfilment and settlement workflows.

### 3. Administrators and operations
- Manage users and supplier records.
- Review and coordinate inventory listings.
- Manage orders and fulfilment.
- Record quality inspections.
- Monitor payments, supplier settlements and receivables.
- Access operational and analytical information.

## Core functional modules

The backend is organised into modular application areas, including:

| Module | Purpose |
|---|---|
| User management | User accounts, profiles and role-based access |
| Fish and catch records | Seafood species and catch information |
| Inventory | Inventory lots, availability, quantities and product status |
| Orders | Buyer orders and order lifecycle management |
| Payments | Payment initiation, transaction records and callbacks |
| Reconciliation | Payment and transaction reconciliation |
| Payouts and settlements | Supplier payment and settlement workflows |
| Compliance | Supplier information and compliance records |
| Quality inspection | Product quality and inspection records |
| Logistics | Delivery and fulfilment coordination |
| Documents and LPOs | Procurement and transaction documentation |
| Analytics | Operational reporting and business intelligence |
| ESG | Environmental and social data structures |
| WhatsApp | Messaging, notifications and webhook workflows |
| USSD | Application-level integration for future feature-phone access |

The platform supports different inventory ownership and trading models, including:

- **Marketplace:** The supplier retains ownership while MarineCatch facilitates the transaction.
- **MarineCatch-owned inventory:** MarineCatch procures seafood and resells it to buyers.
- **Consignment:** Inventory is supplied for sale under an agreed arrangement.
- **Contract-reserved inventory:** Inventory is allocated to fulfil a specific buyer requirement.

These models reflect the different ways seafood is sourced and distributed in the operating business.

## Technology architecture

The application uses a modular backend architecture with web-based interfaces and external service integrations.

### Backend
- Python
- FastAPI
- REST API architecture
- SQLAlchemy ORM
- Pydantic for data validation

### Database
- PostgreSQL 15
- Relational data model
- Alembic database migrations

### Infrastructure and deployment
- Docker-based application deployment
- AWS cloud infrastructure
- AWS region: Africa (Cape Town), `af-south-1`
- Nginx reverse proxy
- SSL-enabled application access

### Frontend
The repository includes separate web interfaces for:
- Buyers
- Fishers and suppliers
- Administrators
- Public-facing website

### External integrations

**M-Pesa**

The application includes M-Pesa payment workflows, including:
- STK Push payment initiation.
- Payment callback handling.
- Transaction status updates.
- B2C payout workflows.

**WhatsApp Cloud API**

The application includes WhatsApp webhook and messaging workflows for:
- Incoming messages.
- Order notifications.
- Payment notifications.
- Dispatch notifications.
- Supplier payout notifications.
- Operational alerts.

**Africa's Talking USSD**

The application includes a USSD integration intended to extend access to fishers and suppliers using feature phones. This channel is not yet live in production and requires further implementation, testing and operating resources.

**KCB integration**

The codebase includes an integration structure for KCB banking services. Production activation is subject to the required banking partnership, credentials and testing.

## Catch and traceability data

The platform's inventory and catch records are designed to capture information relevant to seafood identification, sourcing and transaction traceability.

Core data fields include:
- Species.
- Product form.
- Catch or inventory weight.
- Available quantity.
- Product condition, including fresh, frozen, live and processed.
- Landing and sourcing information.
- Supplier or fisher identification.
- Quality grade and inspection information.
- Inventory lot and batch references.

Additional supplier and catch information can include:
- Fishing gear.
- Vessel name and registration reference.
- Crew size.
- Female crew participation.
- Landing temperature.
- Processing information.

The availability and completeness of these fields depend on supplier onboarding and the information recorded for each transaction. Not every optional field is currently mandatory or populated consistently.

The current system supports structured inventory and transaction records. Blockchain-based traceability is not deployed and remains outside the current production scope.

## Security and data ownership

MarineCatch Africa owns the application code and the intellectual property associated with its platform.

The application includes user authentication, role-based access workflows and protected API routes. External integrations use environment-based configuration for credentials and service settings.

Security hardening, independent architecture review, deployment configuration review and further testing remain part of the platform's ongoing technical development.

**Note:** The public repository is provided for technical transparency. Production credentials, private configuration files and sensitive operational data must not be committed to source control.

## Repository structure

The codebase is organised into backend application services and separate frontend interfaces.

```text
marinecatch-platform/
│
├── backend/
│   └── app/
│       ├── api/
│       │   └── v1/
│       │       └── routes/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       ├── database/
│       ├── config.py
│       └── main.py
│
├── frontend/
│   ├── buyer/
│   ├── fisher/
│   ├── admin/
│   └── landing/
│
├── Dockerfile
├── docker-compose.yml
└── README.md
```

*Directory names may evolve as the application is refactored.*

## Current development priorities

Our current priorities are:

1. Improve platform reliability and resolve issues identified through live operations.
2. Increase buyer, fisher and supplier onboarding.
3. Improve inventory accuracy and transaction completion workflows.
4. Strengthen payment reconciliation and supplier settlement processes.
5. Improve data completeness for catch, landing and quality information.
6. Expand operational analytics and management reporting.
7. Complete the USSD implementation and testing.
8. Conduct an independent technical and security review.
9. Strengthen the engineering team and technical documentation.

## Product roadmap

Future development will focus on improving the efficiency, transparency and resilience of seafood supply chains.

Areas under consideration include:
- More comprehensive digital catch documentation.
- Improved supplier verification and compliance workflows.
- Better cold-chain and quality monitoring.
- Expanded access through feature-phone channels.
- Financial services integrations supporting supplier payments and working-capital access.
- More advanced fisheries impact and sustainability indicators.

These are development priorities and potential future capabilities, not claims that all such services are currently deployed.

## About MarineCatch Africa

MarineCatch Africa Ltd is a Kenyan-registered fisheries and blue-economy enterprise.

We combine direct seafood sourcing and distribution with technology development to improve how seafood moves from fishers and suppliers to commercial and household buyers.

Our long-term objective is to build practical digital and commercial infrastructure that strengthens market access, supply-chain coordination and economic participation across African fisheries.

**Website:** https://marinecatchafrica.com

**Repository:** https://github.com/marinecatch/marinecatch-platform

**Contact:** info@marinecatchafrica.comure microservices — one FastAPI monolith, modular internally MarineCatch Africa Platform
