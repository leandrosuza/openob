"""Teste de monitoramento de mensagens"""

import sys
import asyncio
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from connection.websocket import WebSocketManager


async def test_messages():
    """Testar monitoramento de mensagens"""
    print("=" * 60)
    print("TESTE DE MONITORAMENTO DE MENSAGENS")
    print("=" * 60)

    ws_manager = WebSocketManager(region="DEMO")

    # Adicionar handler para todas as mensagens
    all_messages = []

    async def message_handler(event, data):
        """Handler para capturar todas as mensagens"""
        all_messages.append({"event": event, "data": str(data)[:100]})
        print(f"[MSG] Evento: {event}, Data: {str(data)[:80]}...")

    ws_manager.add_event_handler("json_data", lambda d: message_handler("json_data", d))
    ws_manager.add_event_handler("balance", lambda d: message_handler("balance", d))
    ws_manager.add_event_handler("candles", lambda d: message_handler("candles", d))
    ws_manager.add_event_handler("authenticated", lambda d: message_handler("authenticated", d))
    ws_manager.add_event_handler("successauth", lambda d: message_handler("successauth", d))

    try:
        print("\n[1/2] Conectando ao servidor...")
        connected = await ws_manager.connect()
        print(f"   Resultado: {connected}")

        if connected:
            print("\n[2/2] Monitorando mensagens por 10 segundos...")
            await asyncio.sleep(10)

            print(f"\n[RESUMO] Total de mensagens capturadas: {len(all_messages)}")
            for i, msg in enumerate(all_messages[:10], 1):
                print(f"   {i}. Evento: {msg['event']}, Data: {msg['data']}")

    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nDesconectando...")
        await ws_manager.disconnect()
        print("[OK] Desconectado")

if __name__ == "__main__":
    asyncio.run(test_messages())
