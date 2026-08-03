# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

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
    ussd,
    analytics,
    settlement,
    compliance,
    sales,
    logistics_orchestration,
    newsletter
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
# ── ADMIN PANEL ───────────────────────────────
import os
# Works both locally and in Docker
possible_paths = [
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "admin"),
    "/frontend/admin",
]
admin_dir = None
for path in possible_paths:
    if os.path.exists(os.path.abspath(path)):
        admin_dir = os.path.abspath(path)
        break

if admin_dir:
    app.mount("/admin/static", StaticFiles(directory=os.path.join(admin_dir, "static")), name="admin-static")
    app.mount("/admin/pages", StaticFiles(directory=os.path.join(admin_dir, "pages")), name="admin-pages")

    @app.get("/admin")
    @app.get("/admin/")
    def admin_redirect():
        return FileResponse(os.path.join(admin_dir, "pages", "login.html"))
        # Buyer portal
@app.get("/buyer")
def serve_buyer():
    buyer_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "buyer", "index.html"
    )
    return FileResponse(os.path.abspath(buyer_path))

# Fisher portal
@app.get("/fisher")
def serve_fisher():
    fisher_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "fisher", "index.html"
    )
    return FileResponse(os.path.abspath(fisher_path))
   # Landing page static files
landing_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "landing")
landing_dir = os.path.abspath(landing_dir)
if os.path.exists(landing_dir):
    app.mount("/landing", StaticFiles(directory=landing_dir), name="landing-static")     
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
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(settlement.router, prefix="/api/v1")
app.include_router(compliance.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(logistics_orchestration.router, prefix="/api/v1")
app.include_router(newsletter.router, prefix="/api/v1")
@app.get("/", tags=["System"])
def root():
    landing_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "index.html"
    )
    landing_path = os.path.abspath(landing_path)
    if os.path.exists(landing_path):
        return FileResponse(landing_path)
    return {
        "service": "MarineCatch Africa API",
        "version": "1.0.0",
        "status":  "running",
        "docs":    "/docs",
    }
@app.get("/logo.png")
def serve_logo():
    logo_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "logo.png"
    )
    return FileResponse(os.path.abspath(logo_path))

@app.get("/kenia.png")
def serve_kenia():
    return FileResponse(os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "kenia.png")))

@app.get("/sotehub.webp")
def serve_sotehub():
    return FileResponse(os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "sotehub.webp")))

@app.get("/mpesa.png")
def serve_mpesa():
    return FileResponse(os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "mpesa.png")))
@app.get("/privacy")
def serve_privacy():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "privacy.html"))
    return FileResponse(path)

@app.get("/terms")
def serve_terms():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "terms.html"))
    return FileResponse(path)    
@app.get("/insights")
def serve_insights():
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights.html"
    )
    return FileResponse(os.path.abspath(path))   
@app.get("/insights/traceability-certification")
def serve_traceability_article():
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights", "traceability-certification.html"
    )
    return FileResponse(os.path.abspath(path))
@app.get("/insights/financial-inclusion")
def serve_financial_inclusion_article():
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights", "financial-inclusion.html"
    )
    return FileResponse(os.path.abspath(path))
@app.get("/insights/ooc11-recap")
def serve_ooc11():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights", "ooc11-recap.html")
    return FileResponse(os.path.abspath(path))

@app.get("/insights/kibuyuni-bmu-data")
def serve_bmu_data():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights", "kibuyuni-bmu-data.html")
    return FileResponse(os.path.abspath(path))

@app.get("/insights/supply-chain-infrastructure")
def serve_supply_chain():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights", "supply-chain-infrastructure.html")
    return FileResponse(os.path.abspath(path))

@app.get("/insights/fisher-cluster-model")
def serve_fisher_cluster():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights", "fisher-cluster-model.html")
    return FileResponse(os.path.abspath(path))

@app.get("/insights/blue-economy-africa")
def serve_blue_economy():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights", "blue-economy-africa.html")
    return FileResponse(os.path.abspath(path))

@app.get("/insights/financial-inclusion")
def serve_financial_inclusion():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "landing", "insights", "financial-inclusion.html")
    return FileResponse(os.path.abspath(path))

@app.get("/track")
def serve_track_page():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "landing", "track.html"))
    return FileResponse(path)