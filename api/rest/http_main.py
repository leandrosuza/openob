"""API FastAPI principal para OpenOB (HTTP REST)

Este módulo implementa a API HTTP REST para autenticação de usuários,
separada da comunicação WebSocket com PocketOption (api/pocketoption/).

Sistemas separados:
- api/rest/http_auth.py: Autenticação HTTP com JWT (usuários, login, refresh tokens)
- api/pocketoption/auth.py: Autenticação WebSocket com PocketOption (SSID)
- boot.py: Monitoramento WebSocket PocketOption (payout, ticks)
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.logger import get_logger
from api.rest.http_auth import router as auth_router


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager para startup/shutdown"""
    logger.info("API HTTP iniciando...")
    yield
    logger.info("API HTTP encerrada...")


app = FastAPI(
    title="OpenOB API",
    description="API para monitoramento e trading PocketOption",
    version="1.0.0",
    lifespan=lifespan
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Adicionar headers de segurança"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Include routers
app.include_router(auth_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpenOB API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
