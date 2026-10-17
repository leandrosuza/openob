"""
Boot script - Inicia ambiente e mantém conexão payout + actives
"""

import sys
import asyncio
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.monitor import MonitorAPI
from core.logger import get_logger, LoggerConfig

LoggerConfig.setup(level="INFO")
logger = get_logger(__name__)


def reset_logs():
    """Limpar e recriar pasta logs/"""
    logs_dir = "logs"
    ws_dir = os.path.join(logs_dir, "ws")

    try:
        if os.path.exists(logs_dir):
            shutil.rmtree(logs_dir)
            logger.info("Pasta logs/ removida")

        os.makedirs(ws_dir, exist_ok=True)

        log_files = [
            os.path.join(logs_dir, "error.txt"),
            os.path.join(logs_dir, "info.txt"),
            os.path.join(logs_dir, "debug.txt"),
            os.path.join(logs_dir, "trading.txt"),
            os.path.join(ws_dir, "connection.txt"),
            os.path.join(ws_dir, "monitoring_payout.txt"),
            os.path.join(ws_dir, "monitoring_actives.txt"),
        ]

        for log_file in log_files:
            with open(log_file, "w", encoding="utf-8") as f:
                pass

        logger.info("Arquivos de log recriados")

    except Exception as e:
        logger.error(f"Erro ao resetar logs: {e}")


async def main():
    """Função principal - conecta payout e actives, permanece online"""
    print("="*60)
    print("OpenOB - Iniciando Ambiente")
    print("="*60)

    reset_logs()
    print("Logs resetados")

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

            payout_data = monitor.get_payout_data()
            if payout_data:
                print(f"\n--- Payout ---")
                print(f"Ativos disponíveis: {len(payout_data)}")

            monitored_assets = monitor.get_monitored_assets()
            if monitored_assets:
                print(f"\n--- Ativos Monitorados ---")
                print(f"Monitorando: {len(monitored_assets)} ativos")
                for asset in list(monitored_assets)[:5]:
                    payout = payout_data.get(asset, {}).get("payout", 0)
                    print(f"  {asset}: {payout}%")

            tick_data = monitor.get_tick_data()
            if tick_data:
                print(f"\n--- Ticks Recentes ---")
                for asset, price in list(tick_data.items())[:5]:
                    print(f"{asset}: {price}")

    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")

    finally:
        await monitor.stop()
        print("Sistema parado")


if __name__ == "__main__":
    asyncio.run(main())
