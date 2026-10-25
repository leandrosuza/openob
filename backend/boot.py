"""Boot script - Ponto de entrada único do OpenOB

Uso:
    python boot.py              # Inicia servidor API HTTP e WebSocket monitoramento
"""

import sys
import asyncio
import os
import shutil
import subprocess
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    # Mapeamento: nome de importação -> nome do pacote pip
    required_modules = {
        "dotenv": "python-dotenv",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "websockets": "websockets",
        "pydantic": "pydantic",
        "jose": "python-jose",
        "slowapi": "slowapi",
        "passlib": "passlib",
    }

    missing = []
    for import_name, pip_name in required_modules.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("="*60)
        print("⚠️  Dependências faltando:")
        for module in missing:
            print(f"  - {module}")
        print("="*60)
        print("\n📦 Instalando dependências automaticamente...")
        print("="*60)

        try:
            result = subprocess.run([sys.executable, "depen.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print(result.stderr)
                print("\n❌ Erro ao instalar dependências automaticamente")
                print("Execute manualmente: python depen.py")
                sys.exit(1)
            
            print("\n✅ Dependências instaladas com sucesso!")
            print("🔄 Reiniciando...")
            # Reiniciar o script com os mesmos argumentos
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"\n❌ Erro ao instalar dependências: {e}")
            print("Execute manualmente: python depen.py")
            sys.exit(1)
    else:
        print("[OK] Todas as dependencias estao instaladas.")


check_dependencies()

from core.monitor import MonitorAPI
from core.logger import get_logger, LoggerConfig
from config.settings import Settings
from core.subscription_manager import SubscriptionManager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.rest import auth_router, plan_router, subscription_router, transaction_router, user_connection_router, autotrade_router

# Variável global para monitoramento
monitor_api: MonitorAPI = None
user_connection_manager = None

# Configurar logger
LoggerConfig.setup(level=Settings.get_log_level())
logger = get_logger(__name__)
security_logger = LoggerConfig.get_security_logger()

# Configurar loggers específicos
LoggerConfig.setup_subscription_logger()
LoggerConfig.setup_payment_logger()
LoggerConfig.setup_security_logger()
LoggerConfig.setup_database_logger()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager para startup/shutdown"""
    global monitor_api, user_connection_manager
    logger.info("API HTTP iniciando...")

    # Validar configurações de segurança
    errors = Settings.validate()
    if errors:
        logger.warning(f"Configurações de segurança com avisos: {errors}")

    # Inicializar banco de dados
    from repositories.repository_factory import RepositoryFactory
    from core.strategy_manager import StrategyManager
    from core.trading_manager import TradingManager
    from core.user_connection_manager import UserConnectionManager
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

    # Inicializar managers de trading
    user_repo = RepositoryFactory.create_user_repository(config)
    tick_repo = RepositoryFactory.create_tick_repository(config)

    strategy_manager = StrategyManager(
        tick_repository=tick_repo,
        tick_cache_size=Settings.TICK_CACHE_SIZE
    )
    await strategy_manager.start()

    trading_manager = TradingManager()
    await trading_manager.start()

    user_connection_manager = UserConnectionManager(
        user_repository=user_repo,
        strategy_manager=strategy_manager,
        trading_manager=trading_manager,
        autotrade_repository=autotrade_repo
    )
    await user_connection_manager.start_monitoring()
    logger.info("UserConnectionManager iniciado com sucesso")

    # Iniciar monitoramento WebSocket
    try:
        logger.info("Iniciando monitoramento WebSocket...")
        monitor_api = MonitorAPI()
        await monitor_api.start(
            payout_interval=Settings.MONITOR_PAYOUT_INTERVAL,
            update_interval=Settings.MONITOR_ASSETS_UPDATE_INTERVAL
        )
        logger.info("Monitoramento WebSocket iniciado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao iniciar monitoramento WebSocket: {e}")
        logger.warning("API continuará sem monitoramento WebSocket")

    yield

    # Parar monitoramento WebSocket
    if monitor_api:
        logger.info("Parando monitoramento WebSocket...")
        await monitor_api.stop()
        logger.info("Monitoramento WebSocket parado")

    # Parar UserConnectionManager
    if user_connection_manager:
        logger.info("Parando UserConnectionManager...")
        await user_connection_manager.stop_monitoring()
        logger.info("UserConnectionManager parado")

    # Parar managers
    await strategy_manager.stop()
    await trading_manager.stop()

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


# Criar app FastAPI
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
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


def reset_logs():
    """Gerenciar pasta logs/ conforme LOG_LEVEL"""
    logs_dir = "logs"
    ws_dir = os.path.join(logs_dir, "ws")
    plans_dir = os.path.join(logs_dir, "plans")
    trading_dir = os.path.join(logs_dir, "trading")
    strategy_dir = os.path.join(logs_dir, "strategy")
    users_dir = os.path.join(logs_dir, "users")

    # Criar diretórios sempre
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(ws_dir, exist_ok=True)
    os.makedirs(plans_dir, exist_ok=True)
    os.makedirs(trading_dir, exist_ok=True)
    os.makedirs(strategy_dir, exist_ok=True)
    os.makedirs(users_dir, exist_ok=True)

    # Criar arquivo de segurança sempre (independente de LOG_LEVEL)
    auth_log = os.path.join(logs_dir, "auth.txt")
    if not os.path.exists(auth_log):
        with open(auth_log, 'w') as f:
            f.write("")  # Criar arquivo vazio

    # Criar arquivo de database sempre
    database_log = os.path.join(logs_dir, "database.txt")
    if not os.path.exists(database_log):
        with open(database_log, 'w') as f:
            f.write("")  # Criar arquivo vazio

    # Criar diretório e arquivos de plans
    plans_dir = os.path.join(logs_dir, "plans")
    os.makedirs(plans_dir, exist_ok=True)

    # Lista de todos os arquivos .txt em todas as pastas
    all_txt_files = []
    for root, dirs, files in os.walk(logs_dir):
        for file in files:
            if file.endswith('.txt'):
                all_txt_files.append(os.path.join(root, file))

    try:
        if Settings.LOG_LEVEL.upper() == "DEBUG":
            # Em modo DEBUG, limpar todos os arquivos .txt
            for txt_file in all_txt_files:
                with open(txt_file, "w", encoding="utf-8") as f:
                    pass  # Limpar arquivo

            logger.info("Todos os arquivos .txt limpos (modo DEBUG)")
        else:
            # Em outros níveis, remover todos os arquivos .txt
            for txt_file in all_txt_files:
                if os.path.exists(txt_file):
                    os.remove(txt_file)

            logger.info(f"Todos os arquivos .txt removidos (modo {Settings.LOG_LEVEL.upper()})")

    except Exception as e:
        logger.error(f"Erro ao configurar logs: {e}")


def main():
    """Função principal - inicia servidor API"""
    # Validar configurações
    errors = Settings.validate()
    if errors:
        print("ERROS DE CONFIGURAÇÃO:")
        for error in errors:
            print(f"  - {error}")
        print("\nCorrija o arquivo .env antes de continuar")
        sys.exit(1)

    reset_logs()
    if Settings.LOG_LEVEL.upper() == "DEBUG":
        print("Logs ativados (modo DEBUG)")
    else:
        print(f"Logs desativados (modo {Settings.LOG_LEVEL.upper()})")

    # Iniciar servidor API
    import uvicorn

    print("=" * 60)
    print("OpenOB API HTTP Server")
    print("=" * 60)
    print("Iniciando servidor em http://0.0.0.0:8000")
    print("Documentação: http://localhost:8000/docs")
    print("Pressione Ctrl+C para encerrar")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )


if __name__ == "__main__":
    main()
