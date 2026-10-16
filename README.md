# OpenOB - PocketOption API Client

Cliente simplificado e modular para interagir com a API PocketOption.

## Estrutura do Projeto

```
openob/
├── openob/                      # Pacote principal
│   ├── __init__.py             # Pacote
│   ├── client.py               # Facade principal (PocketOptionClient)
│   ├── boot.py                 # Arquivo de boot/inicialização
│   ├── api/                    # Módulos de API
│   │   ├── __init__.py
│   │   ├── auth.py             # Autenticação
│   │   ├── trading.py          # Operações de trading
│   │   ├── market.py           # Dados de mercado
│   │   └── account.py          # Conta e saldo
│   ├── connection/             # Gerenciamento de conexão
│   │   ├── __init__.py
│   │   └── websocket.py        # WebSocket Manager
│   ├── models/                 # Modelos de dados
│   │   ├── __init__.py
│   │   ├── trading.py          # Order, OrderDirection, OrderResult
│   │   └── market.py           # Candle, Balance
│   └── core/                   # Constantes e configurações
│       ├── __init__.py
│       └── constants.py        # ASSETS, REGIONS, TIMEFRAMES
├── pyproject.toml              # Configuração do pacote
└── README.md                   # Este arquivo
```

## Instalação

```bash
pip install -e .
```

## Uso Básico

### Via boot.py (recomendado)

```bash
cd openob
python openob/boot.py
```

### Via código

```python
import asyncio
from openob.client import PocketOptionClient
from openob.models.trading import OrderDirection

async def main():
    # Criar cliente
    client = PocketOptionClient(
        ssid="your_ssid_here",
        is_demo=True,
        auto_reconnect=True
    )

    try:
        # Conectar
        connected = await client.connect()
        print(f"Conectado: {connected}")

        if connected:
            # Obter saldo
            balance = await client.get_balance()
            print(f"Saldo: {balance}")

            # Obter candles
            candles = await client.get_candles("EURUSD_otc", "1m", 100)
            print(f"Candles: {len(candles)}")

            # Colocar ordem
            result = await client.place_order(
                asset="EURUSD_otc",
                amount=10,
                direction=OrderDirection.CALL,
                duration=60
            )
            print(f"Ordem: {result}")

    finally:
        # Desconectar
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Exemplo de Execução

```bash
cd openob
python -c "import sys, asyncio; sys.path.insert(0, '.'); from openob.example import main; asyncio.run(main())"
```

## Status Atual

✅ Estrutura modular criada
✅ Imports funcionando
✅ WebSocketManager implementado com websockets
✅ AuthAPI implementado com handshake SSID (funcionando)
✅ TradingAPI implementado com validação Pydantic e envio de ordens (funcionando)
✅ MarketAPI implementado com solicitação de candles (funcionando com timeframe 5s)
✅ AccountAPI implementado com solicitação de saldo e validação Pydantic (funcionando)
✅ Models Pydantic com validação robusta (implementado)
✅ Processamento de respostas do servidor (funcionando)
✅ Candles recebidos com sucesso (formato changeSymbol + updateHistoryNewFast)
⏳ Testes unitários (TODO)
⏳ Documentação completa (TODO)

## Requisitos

```bash
pip install websockets pydantic
```

## SSID

Para usar a API, você precisa de um SSID válido. Você pode obter um SSID:
- Acessando o navegador e extraindo do localStorage/sessionStorage
- Usando ferramentas de automação web (Selenium, Playwright)

## Notas Importantes

- A conexão WebSocket está implementada e funcional
- A autenticação via SSID está implementada e funcional
- O saldo é recebido em tempo real via eventos do servidor
- Candles são recebidos via `changeSymbol` e `updateHistoryNewFast`
- O envio de ordens está funcionando
- O tracking de resultados (WIN/LOSS) ainda precisa ser implementado processando eventos `successcloseOrder` ou `updateClosedDeals`

## Scripts de Teste

### Script de Monitoramento de Trade

Para testar um trade com monitoramento até o resultado:

```bash
cd openob
python openob/trade_monitor.py
```

Este script:
1. Conecta ao servidor demo
2. Autentica com SSID
3. Obtém saldo inicial
4. Coloca uma ordem de $10 em EURUSD_otc (CALL, 60s)
5. Monitora a ordem por até 2 minutos
6. Exibe saldo final

**Nota**: Substitua o SSID no script com seu SSID válido.

## Próximos Passos

1. Implementar tracking real de resultados de ordens (processar eventos `successcloseOrder`/`updateClosedDeals`)
2. Adicionar testes unitários
3. Adicionar documentação completa
4. Implementar reconexão automática
5. Adicionar tratamento de erros robusto

## Referência

A implementação foi feita do zero, seguindo padrões modernos de Python async/await.
