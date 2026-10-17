"""
Exemplo de uso do Sistema de Monitoramento

Este script demonstra como usar o MonitorAPI para:
1. Monitoramento de Saldo (reconecta periodicamente)
2. Monitoramento de Payout (reconecta a cada 5s)
"""

import asyncio
from core.monitor import MonitorAPI


async def main():
    """Exemplo de uso"""
    print("="*60)
    print("Sistema de Monitoramento - OpenOB")
    print("="*60)

    # Inicializar monitor
    monitor = MonitorAPI(region="DEMO")

    try:
        # Iniciar ambos os monitoramentos
        await monitor.start(balance_interval=10)

        print("\nSistema rodando. Pressione Ctrl+C para parar.")
        print("Logs sendo salvos em logs/ws/")

        # Manter rodando indefinidamente
        while True:
            await asyncio.sleep(10)

            # Exibir dados de saldo
            balance_data = monitor.get_balance_data()
            if balance_data:
                print(f"\n--- Saldo Atual ---")
                print(f"Valor: {balance_data.get('amount')} {balance_data.get('currency')}")
                print(f"Demo: {balance_data.get('is_demo')}")
                print(f"Timestamp: {balance_data.get('timestamp')}")

            # Exibir dados de payout
            payout_data = monitor.get_payout_data()
            if payout_data:
                print(f"\n--- Payout ---")
                print(f"Dados: {payout_data}")

    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")

    finally:
        # Parar monitoramentos
        await monitor.stop()
        print("\nSistema parado")


if __name__ == "__main__":
    asyncio.run(main())
