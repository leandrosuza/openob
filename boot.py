"""
Boot script para testar a API PocketOption
"""

import sys
import asyncio
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openob.client import PocketOptionClient
from openob.models.trading import OrderDirection


async def main():
    """Função principal de teste"""
    print("Iniciando main()...")

    # SSID do usuário (demo)
    ssid = '42["auth",{"session":"i4l5kgudu28vqeppbeios7op3f","isDemo":1,"uid":142541678,"platform":2,"isFastHistory":true,"isOptimized":true}]'

    # Criar cliente
    print("Criando cliente...")
    client = PocketOptionClient(ssid=ssid, is_demo=True, region="DEMO")
    print("Cliente criado")

    try:
        # Conectar
        print("Conectando...")
        connected = await client.connect()
        print(f"Conectado: {connected}")

        if connected:
            print("Conexão estabelecida com sucesso!")
            print("Aguardando autenticação e dados iniciais...")
            await asyncio.sleep(3)

            # Obter saldo
            print("\nObtendo saldo...")
            balance = await client.get_balance()
            print(f"Saldo: {balance}")

            # Obter candles
            print("\nObtendo candles (EURUSD_otc, 5s)...")
            candles = await client.get_candles("EURUSD_otc", "5s", 10)
            print(f"Candles recebidos: {len(candles)}")

            # Colocar ordem
            print("\nColocando ordem de teste (EURUSD_otc, $10, CALL, 5s)...")
            result = await client.place_order("EURUSD_otc", 10, OrderDirection.CALL, 5)
            print(f"Ordem enviada: {result.order_id}")
            print(f"Status inicial: {result.status}")

            # Aguardar resultado
            print("\nAguardando resultado da ordem...")
            await asyncio.sleep(7)

            # Verificar resultado final
            final_result = client.trading._order_results.get(result.order_id, result)
            print(f"Resultado final: {final_result.status}")
            print(f"Profit: ${final_result.profit}")

            # Saldo final
            print("\nSaldo final...")
            balance_final = await client.get_balance()
            print(f"Saldo: {balance_final}")

            print("\nTeste concluído")

    finally:
        # Desconectar
        print("Desconectando...")
        await client.disconnect()
        print("Desconectado")


if __name__ == "__main__":
    asyncio.run(main())
