# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.routes import (
    health,
    users,
    fish,
    orders,
    inventory,
    payments,
    reconciliation,
    payouts,
    lpo, documents,
    logistics,
    esg,
    whatsapp,
    ussd
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting MarineCatch Africa API...")
    print("Connected to PostgreSQL. API ready.")
    yield
    print("Shutting down MarineCatch API")


app = FastAPI(
    title="MarineCatch Africa API",
    description="Seafood supply chain marketplace for Kenya and East Africa",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router)
app.include_router(users.router)
app.include_router(fish.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(reconciliation.router, prefix="/api/v1")
app.include_router(payouts.router, prefix="/api/v1")
app.include_router(lpo.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(logistics.router, prefix="/api/v1")
app.include_router(esg.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")
app.include_router(ussd.router, prefix="/api/v1")
@app.get("/", tags=["System"])
def root():
    return {
        "service": "MarineCatch Africa API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "users": "/api/v1/users",
            "fish": "/api/v1/fish",
            "orders": "/api/v1/orders",
            "inventory": "/api/v1/inventory",
            "payments":  "/api/v1/payments",
            "reconciliation": "/api/v1/reconciliation",
            "payouts": "/api/v1/payouts",
            "lpo": "/api/v1/lpo",
            "documents": "/api/v1/documents",
            "logistics":       "/api/v1/logistics",
            "esg":             "/api/v1/esg",
            "whatsapp":        "/api/v1/whatsapp",
            "ussd":            "/api/v1/ussd"
        }
    }