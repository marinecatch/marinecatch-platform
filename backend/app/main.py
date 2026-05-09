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


# Runs once on startup, once on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — load real fisher and buyer data
    print("Starting MarineCatch Africa API...")
    seed()
    print("Seed data loaded. API ready.")
    yield
    # Shutdown
    print("Shutting down MarineCatch API")


app = FastAPI(
    title="MarineCatch Africa API",
    description="Seafood supply chain marketplace for Kenya and East Africa",
    version="0.1.0",
    lifespan=lifespan
)

# CORS — allows frontend to talk to this API later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ROUTES ────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(users.router)
app.include_router(fish.router,   prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")

# ── ROOT ──────────────────────────────────────────────────────────
@app.get("/", tags=["System"])
def root():
    return {
        "service":  "MarineCatch Africa API",
        "version":  "0.1.0",
        "status":   "running",
        "docs":     "/docs",
        "endpoints": {
            "health":   "/health",
            "users":    "/api/v1/users",
            "fish":     "/api/v1/fish",
            "orders":   "/api/v1/orders"
        }
    }