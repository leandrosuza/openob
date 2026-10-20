"""API FastAPI principal para OpenOB (HTTP REST)

Este módulo implementa a API HTTP REST para autenticação de usuários,
separada da comunicação WebSocket com PocketOption (api/pocketoption/).

Sistemas separados:
- api/rest/http_auth.py: Autenticação HTTP com JWT (usuários, login, refresh tokens)
- api/pocketoption/auth.py: Autenticação WebSocket com PocketOption (SSID)
- boot.py: Monitoramento WebSocket PocketOption (payout, ticks)

Segurança implementada:
- Headers de segurança HTTP
- CORS restrito
- Rate limiting
- Logs de segurança dedicados
- Versionamento de API (/v1/)
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.logger import get_logger
from api.rest.http_auth import router as auth_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config.settings import Settings
import os
import logging


logger = get_logger(__name__)


# Configurar logger de segurança dedicado
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)
security_handler = logging.FileHandler("logs/auth.txt")
security_handler.setFormatter(logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s'))
security_logger.addHandler(security_handler)


# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="OpenOB API",
    description="API para monitoramento e trading PocketOption",
    version="1.0.0",
    lifespan=None  # Simplificado
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager para startup/shutdown"""
    logger.info("API HTTP iniciando...")
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    yield
    logger.info("API HTTP encerrada...")


app.router.lifespan_context = lifespan


# CORS - Restrito a domínios específicos
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        # Adicionar domínios de produção aqui
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Métodos restritos
    allow_headers=["Content-Type", "Authorization"],  # Headers restritos
)


# Security headers - Melhorados
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Adicionar headers de segurança"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# Log de segurança para todas as requisições
@app.middleware("http")
async def log_security_requests(request: Request, call_next):
    """Log de segurança para requisições"""
    response = await call_next(request)
    
    # Log de segurança (sem dados sensíveis)
    security_logger.info(
        f"{request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"IP: {request.client.host if request.client else 'unknown'}"
    )
    
    return response


# Include routers com versionamento
app.include_router(auth_router, prefix="/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpenOB API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_version": "v1"
    }


@app.get("/health")
@limiter.limit(Settings.RATE_LIMIT_HEALTH)  # Rate limit configurável via ENV
async def health_check(request: Request):
    """Health check endpoint"""
    return {"status": "healthy"}
