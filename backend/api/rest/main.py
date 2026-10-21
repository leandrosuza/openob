"""API FastAPI principal para OpenOB"""

import os
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from core.logger import get_logger, LoggerConfig
from api.rest import auth_router, plan_router, subscription_router, transaction_router, user_connection_router, autotrade_router
from config.settings import Settings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


logger = get_logger(__name__)
security_logger = LoggerConfig.get_security_logger()


# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager para startup/shutdown"""
    logger.info("API HTTP iniciando...")
    
    # Validar configurações de segurança
    errors = Settings.validate()
    if errors:
        logger.warning(f"Configurações de segurança com avisos: {errors}")
    
    yield
    logger.info("API HTTP encerrada...")


app = FastAPI(
    title="OpenOB API",
    description="API para monitoramento e trading PocketOption",
    version="1.0.0",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS - Configurado via .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
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


# Include routers
app.include_router(auth_router.router)
app.include_router(plan_router.router)
app.include_router(subscription_router.router)
app.include_router(transaction_router.router)
app.include_router(user_connection_router.router)
app.include_router(autotrade_router.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpenOB API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
@limiter.limit(Settings.RATE_LIMIT_HEALTH)
async def health_check(request: Request):
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
