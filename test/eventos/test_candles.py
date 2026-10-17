"""
Teste de candles/market
"""

import sys
import asyncio
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from connection.websocket import WebSocketManager
from api.auth import AuthAPI
from api.market import MarketAPI


async def test_candles():
    """Testar obtenção de candles"""
    print("=" * 60)
    print("TESTE DE CANDLES/MARKET")
    print("=" * 60)

    ssid = '42["auth",{"session":"b89gptdrsbpla6f5eeh78a0bpm","isDemo":1,"uid":142474303,"platform":2,"isFastHistory":true,"isOptimized":true}]'

    ws_manager = WebSocketManager(region="DEMO")
    auth_api = AuthAPI(ws_manager, ssid)
    market_api = MarketAPI(ws_manager)

    try:
        print("\n[1/3] Conectando ao servidor...")
        connected = await ws_manager.connect()
        print(f"   Resultado: {connected}")

        if connected:
            print("\n[2/3] Autenticando...")
            authenticated = await auth_api.authenticate()
            print(f"   Resultado: {authenticated}")

            if authenticated:
                print("\n[3/3] Obtendo candles (EURUSD_otc, 5s)...")
                candles = await market_api.get_candles("EURUSD_otc", "5s", 10)
                print(f"   Candles recebidos: {len(candles)}")
                if candles:
                    print(f"   Primeiro candle: {candles[0]}")
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
    asyncio.run(test_candles())
