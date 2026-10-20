"""Boot script - Inicia ambiente e mantém conexão payout + actives"""

import sys
import asyncio
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.monitor import MonitorAPI
from core.logger import get_logger, LoggerConfig
from config.settings import Settings

# Configurar logger
LoggerConfig.setup(level=Settings.get_log_level())
logger = get_logger(__name__)


def reset_logs():
    """Gerenciar pasta logs/ conforme LOG_LEVEL"""
    logs_dir = "logs"
    ws_dir = os.path.join(logs_dir, "ws")

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
            # Em modo DEBUG, criar arquivos de log
            os.makedirs(ws_dir, exist_ok=True)

            for log_file in log_files:
                with open(log_file, "w", encoding="utf-8") as f:
                    pass

            logger.info("Arquivos de log criados (modo DEBUG)")
        else:
            # Em outros níveis, apagar todo o conteúdo da pasta logs/
            if os.path.exists(logs_dir):
                shutil.rmtree(logs_dir)
                logger.info("Pasta logs/ removida (não está em modo DEBUG)")

    except Exception as e:
        logger.error(f"Erro ao configurar logs: {e}")




async def main():
    """Função principal - conecta payout e actives, permanece online"""
    print("="*60)
    print("OpenOB - Iniciando Ambiente")
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

    try:
        monitor = MonitorAPI()

        await monitor.start(payout_interval=5, update_interval=30)

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
