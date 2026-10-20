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
        print("✅ Todas as dependências estão instaladas.")


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


def reset_logs():
    """Gerenciar pasta logs/ conforme LOG_LEVEL"""
    logs_dir = "logs"
    ws_dir = os.path.join(logs_dir, "ws")
    plans_dir = os.path.join(logs_dir, "plans")

    # Criar diretórios sempre
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(ws_dir, exist_ok=True)
    os.makedirs(plans_dir, exist_ok=True)

    # Criar arquivo de segurança sempre (independente de LOG_LEVEL)
    auth_log = os.path.join(logs_dir, "auth.txt")
    if not os.path.exists(auth_log):
        with open(auth_log, 'w') as f:
            f.write("")  # Criar arquivo vazio

    # Criar arquivos de subscription, payment e security sempre
    subscription_log = os.path.join(plans_dir, "subscriptions.txt")
    payment_log = os.path.join(plans_dir, "payments.txt")
    security_log = os.path.join(logs_dir, "security.txt")
    
    for log_file in [subscription_log, payment_log, security_log]:
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write("")  # Criar arquivo vazio

    log_files = [
        os.path.join(logs_dir, "error.txt"),
        os.path.join(logs_dir, "info.txt"),
        os.path.join(logs_dir, "debug.txt"),
        os.path.join(logs_dir, "trading.txt"),
        os.path.join(ws_dir, "connection.txt"),
        os.path.join(ws_dir, "monitoring_payout.txt"),
        os.path.join(ws_dir, "monitoring_actives.txt"),
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




async def main():
    """Função principal - decide entre monitoramento ou API"""
    # Verificar argumentos
    mode = sys.argv[1] if len(sys.argv) > 1 else "monitor"

    if mode == "api":
        # Modo API
        start_api()
        return

    # Modo monitoramento (padrão)
    print("="*60)
    print("OpenOB - Iniciando Monitoramento")
    print("="*60)

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

    monitor = None
    subscription_manager = None

    try:
        # Verificar subscriptions expiradas no startup
        subscription_manager = SubscriptionManager()
        await subscription_manager.check_expired_on_startup()

        # Iniciar task de verificação periódica
        subscription_task = asyncio.create_task(subscription_manager.expiration_check_loop())

        monitor = MonitorAPI()

        payout_interval = Settings.MONITOR_PAYOUT_INTERVAL
        update_interval = Settings.MONITOR_ASSETS_UPDATE_INTERVAL
        await monitor.start(payout_interval=payout_interval, update_interval=update_interval)

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
