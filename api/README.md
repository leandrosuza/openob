# API - Estrutura do Projeto

Este diretório contém as APIs do projeto OpenOB, organizadas em subpastas por tipo de comunicação.

## Estrutura

```
api/
├── pocketoption/        # WebSocket PocketOption
│   ├── auth.py          # Autenticação SSID
│   ├── balance.py       # Saldo
│   ├── market.py        # Mercado
│   └── trading.py       # Trading
└── rest/                # HTTP REST FastAPI
    ├── http_auth.py     # Router autenticação JWT
    ├── http_main.py     # App FastAPI
    ├── security.py      # Configurações JWT
    └── schemas.py       # Modelos Pydantic
```

## PocketOption API (WebSocket)

Comunicação em tempo real com PocketOption via WebSocket.

### Módulos

- **auth.py**: Autenticação usando SSID
- **balance.py**: Consulta de saldo
- **market.py**: Dados de mercado e candles
- **trade.py**: Execução de trades

### Uso

```python
from api.pocketoption.auth import AuthAPI
from api.pocketoption.balance import BalanceAPI
from api.pocketoption.trading import TradingAPI
```

## REST API (HTTP)

API HTTP REST para autenticação de usuários e gerenciamento.

### Módulos

- **http_auth.py**: Endpoints de autenticação JWT
- **http_main.py**: App FastAPI principal
- **security.py**: Configurações de segurança JWT
- **schemas.py**: Modelos Pydantic

### Endpoints

- `POST /api/auth/register` - Registro de usuário
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Renovar token
- `GET /api/auth/me` - Usuário atual
- `POST /api/auth/change-password` - Trocar senha
- `POST /api/auth/logout` - Logout

### Uso

```python
from api.rest.http_main import app
```

### Iniciar servidor

```bash
python api_server.py
```

Ou com uvicorn:

```bash
uvicorn api.rest.http_main:app --host 0.0.0.0 --port 8000 --reload
```

## Separação de Responsabilidades

| Sistema | Localização | Propósito |
|---------|-------------|-----------|
| WebSocket PocketOption | `api/pocketoption/` | Comunicação em tempo real |
| HTTP REST | `api/rest/` | Autenticação de usuários |
| Monitoramento | `boot.py` | Monitoramento de mercado |
| Servidor HTTP | `api_server.py` | Servidor FastAPI |
