"""
Teste simples com PocketOptionAPI de referência usando o SSID fornecido
"""

import asyncio
import sys
sys.path.insert(0, r"C:\Users\Aluno\Documents\GitHub\PocketOptionAPI_ref")

from pocketoptionapi_async.websocket_client import AsyncWebSocketClient

async def main():
    """Testar conexão WebSocket direta com SSID"""
    ssid = '42["auth",{"session":"65j1qjhmcrpsnso431359pqntr","isDemo":1,"uid":142476934,"platform":2,"isFastHistory":true,"isOptimized":true}]'

    print("Testando WebSocket direto com PocketOptionAPI...")
    print(f"SSID: {ssid[:50]}...")

    ws_client = AsyncWebSocketClient()

    try:
        print("\nConectando...")
        urls = ["wss://demo-api-eu.po.market/socket.io/?EIO=4&transport=websocket"]
        connected = await ws_client.connect(urls, ssid)

        if connected:
            print("✅ Conectado com sucesso!")
            await asyncio.sleep(5)
        else:
            print("❌ Falha na conexão")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nDesconectando...")
        await ws_client.disconnect()
        print("Desconectado")

if __name__ == "__main__":
    asyncio.run(main())
