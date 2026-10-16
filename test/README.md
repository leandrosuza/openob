# Testes - openob

Estrutura de testes organizada por funcionalidade.

## Estrutura

```
test/
├── teste/              # Teste geral
│   └── run_all_tests.py  # Executa todos os testes
├── conexao/            # Testes de conexão
│   ├── test_connection.py  # Teste básico de conexão
│   └── test_auth.py        # Teste de autenticação
├── balance/            # Testes de saldo
│   └── test_balance.py     # Teste de obtenção de saldo
├── eventos/            # Testes de eventos/market
│   └── test_candles.py     # Teste de candles
├── execucao/           # Testes de execução
│   └── test_order.py       # Teste de ordem
├── monitoramento/      # Testes de monitoramento
│   └── test_trade_monitor.py  # Teste de monitoramento de trade
└── mensagens/          # Testes de mensagens
    └── test_messages.py    # Teste de monitoramento de mensagens
```

## Como Usar

### Executar todos os testes
```bash
cd openob
python test/teste/run_all_tests.py
```

### Executar testes individuais

#### Teste de conexão
```bash
python test/conexao/test_connection.py
```

#### Teste de autenticação
```bash
python test/conexao/test_auth.py
```

#### Teste de saldo
```bash
python test/balance/test_balance.py
```

#### Teste de candles
```bash
python test/eventos/test_candles.py
```

#### Teste de ordem
```bash
python test/execucao/test_order.py
```

#### Teste de monitoramento de trade
```bash
python test/monitoramento/test_trade_monitor.py
```

#### Teste de mensagens
```bash
python test/mensagens/test_messages.py
```

## Nota sobre SSID

Os testes requerem um SSID válido. Atualize o SSID nos arquivos de teste se necessário:

```python
ssid = '["auth",{"session":"SEU_SSID_AQUI","isDemo":1,"uid":SEU_UID,"platform":2,...}]'
```

Para obter um SSID novo:
1. Acesse pocketoption.com no navegador
2. Faça login
3. Abra DevTools (F12)
4. Vá para Application > Local Storage
5. Copie o valor de `ssid`
