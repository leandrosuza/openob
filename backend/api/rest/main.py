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

    # Inicializar banco de dados
    from repositories.repository_factory import RepositoryFactory
    config = Settings.to_dict()

    # Inicializar plan repository (cria tabela e planos padrão)
    plan_repo = RepositoryFactory.create_plan_repository(config)
    await plan_repo._initialize_db()
    logger.info("Banco de dados PostgreSQL inicializado com sucesso")

    # Criar tabela autotrade_configs
    autotrade_repo = RepositoryFactory.create_autotrade_repository(config)
    await autotrade_repo._initialize_db()
    logger.info("Tabela autotrade_configs criada")

    # Criar TRIGGERs para LISTEN/NOTIFY
    await _create_postgresql_triggers()

    yield
    logger.info("API HTTP encerrada...")


async def _create_postgresql_triggers():
    """Criar TRIGGERs para LISTEN/NOTIFY no PostgreSQL"""
    from repositories.repository_factory import RepositoryFactory
    config = Settings.to_dict()
    from asyncpg import connect

    try:
        conn = await connect(
            host=config.get("POSTGRES_HOST", "localhost"),
            port=config.get("POSTGRES_PORT", 5432),
            database=config.get("POSTGRES_DB", "openob"),
            user=config.get("POSTGRES_USER", "openob_user"),
            password=config.get("POSTGRES_PASSWORD", "")
        )

        # TRIGGER para users
        await conn.execute("""
            CREATE OR REPLACE FUNCTION notify_user_changes()
            RETURNS TRIGGER AS $$
            BEGIN
              PERFORM pg_notify('user_changes', NEW.id::text);
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        try:
            await conn.execute("DROP TRIGGER IF EXISTS user_is_active_trigger ON users")
        except:
            pass

        await conn.execute("""
            CREATE TRIGGER user_is_active_trigger
            AFTER UPDATE OF is_active ON users
            FOR EACH ROW EXECUTE FUNCTION notify_user_changes();
        """)

        try:
            await conn.execute("DROP TRIGGER IF EXISTS user_mode_trigger ON users")
        except:
            pass

        await conn.execute("""
            CREATE TRIGGER user_mode_trigger
            AFTER UPDATE OF mode ON users
            FOR EACH ROW EXECUTE FUNCTION notify_user_changes();
        """)

        # TRIGGER para autotrade_configs
        await conn.execute("""
            CREATE OR REPLACE FUNCTION notify_autotrade_changes()
            RETURNS TRIGGER AS $$
            BEGIN
              PERFORM pg_notify('autotrade_changes', NEW.user_id::text);
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        try:
            await conn.execute("DROP TRIGGER IF EXISTS autotrade_config_trigger ON autotrade_configs")
        except:
            pass

        await conn.execute("""
            CREATE TRIGGER autotrade_config_trigger
            AFTER INSERT OR UPDATE ON autotrade_configs
            FOR EACH ROW EXECUTE FUNCTION notify_autotrade_changes();
        """)

        await conn.close()
        logger.info("TRIGGERs PostgreSQL criados com sucesso")

    except Exception as e:
        logger.error(f"Erro ao criar TRIGGERs PostgreSQL: {e}")


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
