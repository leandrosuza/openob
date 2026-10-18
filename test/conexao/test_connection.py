"""Teste de conexão WebSocket"""

import sys
import asyncio
import os

# Adicionar diretório raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from connection.websocket import WebSocketManager


async def test_connection():
    """Testar conexão WebSocket"""
    print("=" * 60)
    print("TESTE DE CONEXÃO")
    print("=" * 60)

    ws_manager = WebSocketManager(region="DEMO")

    try:
        print("\n[1/2] Conectando ao servidor...")
        connected = await ws_manager.connect()
        print(f"   Resultado: {connected}")

        if connected:
            print("\n[2/2] Aguardando 5 segundos...")
            await asyncio.sleep(5)
            print("   Conexão estável")

    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nDesconectando...")
        await ws_manager.disconnect()
        print("[OK] Desconectado")

if __name__ == "__main__":
    asyncio.run(test_connection())
