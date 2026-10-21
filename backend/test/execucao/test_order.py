"""Teste de execução de ordem"""

import sys
import asyncio
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from connection.websocket import WebSocketManager
from api.pocketoption.auth import AuthAPI
from api.pocketoption.trading import TradingAPI
from models.trading import OrderDirection


async def test_order_execution():
    """Testar execução de ordem"""
    print("=" * 60)
    print("TESTE DE EXECUÇÃO DE ORDEM")
    print("=" * 60)

    ssid = '42["auth",{"session":"b89gptdrsbpla6f5eeh78a0bpm","isDemo":1,"uid":142474303,"platform":2,"isFastHistory":true,"isOptimized":true}]'

    ws_manager = WebSocketManager(region="DEMO")
    auth_api = AuthAPI(ws_manager, ssid)
    trading_api = TradingAPI(ws_manager)

    try:
        print("\n[1/3] Conectando ao servidor...")
        connected = await ws_manager.connect()
        print(f"   Resultado: {connected}")

        if connected:
            print("\n[2/3] Autenticando...")
            authenticated = await auth_api.authenticate()
            print(f"   Resultado: {authenticated}")

            if authenticated:
                print("\n[3/3] Colocando ordem (EURUSD_otc, $10, CALL, 5s)...")
                result = await trading_api.place_order("EURUSD_otc", 10, OrderDirection.CALL, 5)
                print(f"   Ordem ID: {result.order_id}")
                print(f"   Status: {result.status}")
                print(f"   Mensagem: {result.message}")
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
    asyncio.run(test_order_execution())
