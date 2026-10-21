"""Boot script - Inicia ambiente (monitoramento ou API)

Uso:
    python boot.py              # Inicia monitoramento WebSocket (padrão)
    python boot.py monitor      # Inicia monitoramento WebSocket
    python boot.py api          # Inicia servidor API HTTP
"""

import sys
import asyncio
import os
import shutil
import subprocess

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
        "aiosqlite": "aiosqlite",
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

# Configurar logger
LoggerConfig.setup(level=Settings.get_log_level())
logger = get_logger(__name__)

# Configurar loggers específicos
LoggerConfig.setup_subscription_logger()
LoggerConfig.setup_payment_logger()
LoggerConfig.setup_security_logger()
LoggerConfig.setup_database_logger()


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

    log_files = [
        os.path.join(logs_dir, "error.txt"),
        os.path.join(logs_dir, "info.txt"),
        os.path.join(logs_dir, "debug.txt"),
        os.path.join(ws_dir, "connection.txt"),
        os.path.join(ws_dir, "monitoring_payout.txt"),
        os.path.join(ws_dir, "monitoring_actives.txt"),
        os.path.join(plans_dir, "subscriptions.txt"),
        os.path.join(plans_dir, "payments.txt"),
        os.path.join(logs_dir, "security.txt"),
    ]

    try:
        if Settings.LOG_LEVEL.upper() == "DEBUG":
            # Em modo DEBUG, criar/limpar arquivos de log
            for log_file in log_files:
                with open(log_file, "w", encoding="utf-8") as f:
                    pass  # Limpar arquivo

            logger.info("Arquivos de log criados (modo DEBUG)")
        else:
            # Em outros níveis, manter apenas auth.txt, subscriptions.txt, payments.txt, security.txt
            for log_file in log_files:
                if os.path.exists(log_file):
                    os.remove(log_file)
            logger.info(f"Logs detalhados desativados (modo {Settings.LOG_LEVEL.upper()})")

    except Exception as e:
        logger.error(f"Erro ao configurar logs: {e}")


def start_api():
    """Iniciar servidor API HTTP"""
    import uvicorn
    from api.rest.main import app

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
        port=8000,
        reload=True
    )




async def init_database():
    """Inicializar banco de dados PostgreSQL e criar tabelas"""
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


async def init_managers():
    """Inicializar managers de trading"""
    from repositories.repository_factory import RepositoryFactory
    from core.strategy_manager import StrategyManager
    from core.trading_manager import TradingManager
    from core.user_connection_manager import UserConnectionManager

    config = Settings.to_dict()

    # Criar repositórios
    user_repo = RepositoryFactory.create_user_repository(config)
    tick_repo = RepositoryFactory.create_tick_repository(config)
    autotrade_repo = RepositoryFactory.create_autotrade_repository(config)

    # Inicializar managers
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
        trading_manager=trading_manager
    )

    # Iniciar monitoramento
    await user_connection_manager.start_monitoring()

    logger.info("Managers inicializados com sucesso")

    return user_connection_manager, strategy_manager, trading_manager


async def main():
    """Função principal - inicia servidor API"""
    # Inicializar banco de dados antes de tudo
    await init_database()

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

    # Inicializar subscriptions
    subscription_manager = SubscriptionManager()
    await subscription_manager.check_expired_on_startup()
    asyncio.create_task(subscription_manager.expiration_check_loop())

    # Inicializar managers de trading
    user_connection_manager, strategy_manager, trading_manager = await init_managers()

    monitor = MonitorAPI()
    strategy_manager.set_monitor_api(monitor)

    # Iniciar monitoramento
    payout_interval = Settings.MONITOR_PAYOUT_INTERVAL
    update_interval = Settings.MONITOR_ASSETS_UPDATE_INTERVAL
    await monitor.start(payout_interval=payout_interval, update_interval=update_interval)

    print("\n" + "="*60)
    print("OpenOB - API + Monitoramento Iniciados")
    print("="*60)

    # Iniciar servidor API
    start_api()

    try:
        print("\n" + "="*60)
        print("Sistema Online - Mantendo conexão")
        print("Pressione Ctrl+C para encerrar")
        print("="*60)

        await asyncio.sleep(3)

        while True:
            await asyncio.sleep(10)

    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")

    finally:
        # Desconectar todos os usuários ao encerrar
        if user_connection_manager:
            try:
                await user_connection_manager.stop_monitoring()
            except Exception as e:
                logger.error(f"Erro ao parar user connection manager: {e}")

        if subscription_manager:
            try:
                await subscription_manager.stop()
            except Exception as e:
                logger.error(f"Erro ao parar subscription manager: {e}")

        if monitor:
            try:
                await monitor.stop()
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Erro ao parar monitor: {e}")
            print("Sistema parado")


if __name__ == "__main__":
    asyncio.run(main())
