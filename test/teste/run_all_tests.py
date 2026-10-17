"""Teste geral - executa todos os testes"""

import sys
import asyncio
import os


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test.conexao.test_connection import test_connection
from test.conexao.test_auth import test_auth
from test.balance.test_balance import test_balance
from test.eventos.test_candles import test_candles
from test.execucao.test_order import test_order_execution
from test.monitoramento.test_trade_monitor import test_trade_monitor
from test.mensagens.test_messages import test_messages


async def run_all_tests():
    """Executar todos os testes"""
    print("=" * 60)
    print("SUITE DE TESTES - OPENOB")
    print("=" * 60)

    tests = [
        ("Conexão", test_connection),
        ("Autenticação", test_auth),
        ("Mensagens", test_messages),
        ("Saldo", test_balance),
        ("Candles", test_candles),
        ("Execução de Ordem", test_order_execution),
        ("Monitoramento de Trade", test_trade_monitor),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n\n{'=' * 60}")
        print(f"EXECUTANDO: {test_name}")
        print(f"{'=' * 60}")

        try:
            await test_func()
            results.append((test_name, "OK"))
            print(f"\n[OK] {test_name} passou")
        except Exception as e:
            results.append((test_name, "FALHOU"))
            print(f"\n[FALHOU] {test_name}: {e}")

    print("\n\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    for test_name, result in results:
        status = "✅" if result == "OK" else "❌"
        print(f"{status} {test_name}: {result}")

    passed = sum(1 for _, r in results if r == "OK")
    total = len(results)
    print(f"\nTotal: {passed}/{total} testes passaram")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
