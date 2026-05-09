# app/main.py
#
# The front door of MarineCatch Africa API.
# All routers register here.
# Seed data loads on startup.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.routes import health, users, fish, orders
from app.database.memory_store import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting MarineCatch Africa API...")
    seed()
    print("Seed data loaded. API ready.")
    yield
    print("Shutting down MarineCatch API")


app = FastAPI(
    title="MarineCatch Africa API",
    description="Seafood supply chain marketplace for Kenya and East Africa",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ROUTES ────────────────────────────────────────────────────────
# Note: users router already has /api/v1/users prefix built in
# fish and orders get /api/v1 added here
app.include_router(health.router)
app.include_router(users.router)                        # /api/v1/users
app.include_router(fish.router,   prefix="/api/v1")    # /api/v1/fish
app.include_router(orders.router, prefix="/api/v1")    # /api/v1/orders

# ── ROOT ──────────────────────────────────────────────────────────
@app.get("/", tags=["System"])
def root():
    return {
        "service": "MarineCatch Africa API",
        "version": "0.1.0",
        "status":  "running",
        "docs":    "/docs",
        "endpoints": {
            "health":   "/health",
            "users":    "/api/v1/users",
            "fish":     "/api/v1/fish",
            "orders":   "/api/v1/orders"
        }
    }