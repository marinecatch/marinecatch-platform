from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import health, users

app = FastAPI(
    title="MarineCatch Africa API",
    description="Seafood supply chain marketplace API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {
        "message": "MarineCatch Africa API is running",
        "version": "0.1.0"
    }