"""Boot script - Inicia ambiente e mantém conexão payout + actives"""

import sys
import asyncio
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.monitor import MonitorAPI
from core.logger import get_logger, LoggerConfig
from config.settings import Settings

LoggerConfig.setup(level=Settings.get_log_level())
logger = get_logger(__name__)


def reset_logs():
    """Criar pasta logs/ e arquivos se não existirem, resetar apenas em modo DEBUG"""
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
        # Em modo DEBUG, resetar completamente
        if Settings.LOG_LEVEL.upper() == "DEBUG":
            if os.path.exists(logs_dir):
                shutil.rmtree(logs_dir)
                logger.info("Pasta logs/ removida")

            os.makedirs(ws_dir, exist_ok=True)

            for log_file in log_files:
                with open(log_file, "w", encoding="utf-8") as f:
                    pass

            logger.info("Arquivos de log recriados")
        else:
            # Em outros níveis, apenas garantir que os arquivos existem
            os.makedirs(ws_dir, exist_ok=True)
            for log_file in log_files:
                if not os.path.exists(log_file):
                    with open(log_file, "w", encoding="utf-8") as f:
                        pass
            logger.info("Logs não resetados (não está em modo DEBUG)")

    except Exception as e:
        logger.error(f"Erro ao configurar logs: {e}")




async def main():
    """Função principal - conecta payout e actives, permanece online"""
    print("="*60)
    print("OpenOB - Iniciando Ambiente")
    print("="*60)

    reset_logs()
    if Settings.LOG_LEVEL.upper() == "DEBUG":
        print("Logs resetados (modo DEBUG)")
    else:
        print(f"Logs mantidos (modo {Settings.LOG_LEVEL.upper()})")

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
