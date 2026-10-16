"""
Teste com PocketOptionAPI de referência usando o SSID fornecido
"""

import asyncio
import sys
sys.path.insert(0, r"C:\Users\Aluno\Documents\GitHub\PocketOptionAPI_ref")

from pocketoptionapi_async import AsyncPocketOptionClient

async def main():
    """Testar com SSID fornecido"""
    ssid = '42["auth",{"session":"65j1qjhmcrpsnso431359pqntr","isDemo":1,"uid":142476934,"platform":2,"isFastHistory":true,"isOptimized":true}]'

    print("Testando com PocketOptionAPI de referência...")
    print(f"SSID: {ssid[:50]}...")

    client = AsyncPocketOptionClient(ssid=ssid, is_demo=True, enable_logging=True)

    try:
        print("\nConectando...")
        connected = await client.connect()

        if connected:
            print("✅ Conectado com sucesso!")

            print("\nObtendo saldo...")
            balance = await client.get_balance()
            print(f"Saldo: {balance.balance} {balance.currency}")

        else:
            print("❌ Falha na conexão")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nDesconectando...")
        await client.disconnect()
        print("Desconectado")

if __name__ == "__main__":
    asyncio.run(main())
