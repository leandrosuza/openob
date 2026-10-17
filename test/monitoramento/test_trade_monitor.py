"""Teste de monitoramento de trade"""

import sys
import asyncio
import os


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from connection.websocket import WebSocketManager
from api.auth import AuthAPI
from api.balance import BalanceAPI
from api.trading import TradingAPI
from models.trading import OrderDirection


async def test_trade_monitor():
    """Testar monitoramento de trade"""
    print("=" * 60)
    print("TESTE DE MONITORAMENTO DE TRADE")
    print("=" * 60)

    ssid = '42["auth",{"session":"b89gptdrsbpla6f5eeh78a0bpm","isDemo":1,"uid":142474303,"platform":2,"isFastHistory":true,"isOptimized":true}]'

    ws_manager = WebSocketManager(region="DEMO")
    auth_api = AuthAPI(ws_manager, ssid)
    balance_api = BalanceAPI(ws_manager)
    trading_api = TradingAPI(ws_manager)

    try:
        print("\n[1/5] Conectando ao servidor...")
        connected = await ws_manager.connect()
        print(f"   Resultado: {connected}")

        if connected:
            print("\n[2/5] Autenticando...")
            authenticated = await auth_api.authenticate()
            print(f"   Resultado: {authenticated}")

            if authenticated:
                print("\n[3/5] Saldo inicial...")
                balance_initial = await balance_api.get_balance()
                print(f"   {balance_initial}")

                print("\n[4/5] Colocando ordem (EURUSD_otc, $10, CALL, 60s)...")
                result = await trading_api.place_order("EURUSD_otc", 10, OrderDirection.CALL, 60)
                print(f"   Ordem ID: {result.order_id}")
                print(f"   Status: {result.status}")

                print("\n[5/5] Monitorando por 70 segundos...")
                for i in range(14):
                    await asyncio.sleep(5)
                    elapsed = (i + 1) * 5
                    print(f"   [WAIT] {elapsed}s")

                    # Verificar status atualizado
                    current_result = trading_api._order_results.get(result.order_id, result)
                    if current_result.status.value != "pending":
                        print(f"   [UPDATE] Status: {current_result.status.value}")
                        print(f"   [UPDATE] Profit: ${current_result.profit}")
                        break

                print("\n[FINAL] Saldo final...")
                balance_final = await balance_api.get_balance()
                print(f"   {balance_final}")
            else:
                print("   [SKIP] Não foi possível autenticar")

    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nDesconectando...")
        await ws_manager.disconnect()
        print("[OK] Desconectado")


if __name__ == "__main__":
    asyncio.run(test_trade_monitor())
