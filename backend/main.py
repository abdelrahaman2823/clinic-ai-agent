# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, chat, doctors, appointments, patients, sync

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered clinic management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router,         prefix="/api/v1")
app.include_router(chat.router,         prefix="/api/v1")
app.include_router(doctors.router,      prefix="/api/v1")
app.include_router(appointments.router, prefix="/api/v1")
app.include_router(patients.router,     prefix="/api/v1")
app.include_router(sync.router,         prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Clinic AI Agent API is running ✅", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}