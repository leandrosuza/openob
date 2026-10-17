"""Teste de autenticação"""

import sys
import asyncio
import os


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from connection.websocket import WebSocketManager
from api.auth import AuthAPI


async def test_auth():
    """Testar autenticação"""
    print("=" * 60)
    print("TESTE DE AUTENTICAÇÃO")
    print("=" * 60)

    ssid = '42["auth",{"session":"a:4:{s:10:\"session_id\";s:32:\"332272e5ad48dc84f8918f0988edd71a\";s:10:\"ip_address\";s:13:\"177.131.35.41\";s:10:\"user_agent\";s:80:\"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0\";s:13:\"last_activity\";i:1792108890;}def96e8ff9accc4ef624e2bb0ffbff40","isDemo":0,"uid":142476934,"platform":2,"isFastHistory":true,"isOptimized":true}]'

    ws_manager = WebSocketManager(region="api-eu")
    auth_api = AuthAPI(ws_manager, ssid)

    try:
        print("\n[1/2] Conectando ao servidor...")
        connected = await ws_manager.connect()
        print(f"   Resultado: {connected}")

        if connected:
            print("\n[2/2] Autenticando...")
            authenticated = await auth_api.authenticate()
            print(f"   Resultado: {authenticated}")

    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nDesconectando...")
        await ws_manager.disconnect()
        print("[OK] Desconectado")


if __name__ == "__main__":
    asyncio.run(test_auth())
