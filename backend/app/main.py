from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.routes import health, users, fish
from app.database.memory_store import seed


# Lifespan handler (modern FastAPI way)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    seed()
    yield
    # Shutdown logic (optional)
    print("Shutting down MarineCatch API")


app = FastAPI(
    title="MarineCatch Africa API",
    description="Seafood supply chain marketplace API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS setup
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


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "MarineCatch Africa API is running",
        "version": "0.1.0"
    }