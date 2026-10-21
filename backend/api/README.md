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
    ├── main.py          # App FastAPI principal
    ├── auth_router.py   # Router autenticação JWT
    ├── security.py      # Configurações JWT
    └── schemas.py       # Modelos Pydantic
```

## PocketOption API (WebSocket)

Comunicação em tempo real com PocketOption via WebSocket.

### Módulos

- **auth.py**: Autenticação usando SSID
- **balance.py**: Consulta de saldo
- **market.py**: Dados de mercado e candles
- **trading.py**: Execução de trades

### Uso

```python
from api.pocketoption.auth import AuthAPI
from api.pocketoption.balance import BalanceAPI
from api.pocketoption.trading import TradingAPI
```

## REST API (HTTP)

API HTTP REST para autenticação de usuários e gerenciamento.

### Módulos

- **main.py**: App FastAPI principal
- **auth_router.py**: Endpoints de autenticação JWT
- **security.py**: Configurações de segurança JWT
- **schemas.py**: Modelos Pydantic

### Endpoints

- `POST /api/auth/register` - Registro de usuário
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Renovar token
- `GET /api/auth/me` - Usuário atual
- `POST /api/auth/change-password` - Trocar senha
- `POST /api/auth/logout` - Logout

### Segurança

Configurações gerenciadas via `.env`:

- **JWT_SECRET_KEY**: Chave secreta para assinatura de tokens (MUDAR EM PRODUÇÃO)
- **JWT_ACCESS_TOKEN_EXPIRE_MINUTES**: Tempo de expiração do access token (padrão: 15)
- **JWT_REFRESH_TOKEN_EXPIRE_DAYS**: Tempo de expiração do refresh token (padrão: 7)
- **CORS_ORIGINS**: Origens permitidas separadas por vírgula
- **RATE_LIMIT_REGISTER**: Limite de requisições para registro (padrão: 5/minute)
- **RATE_LIMIT_LOGIN**: Limite de requisições para login (padrão: 10/minute)
- **RATE_LIMIT_REFRESH**: Limite de requisições para refresh (padrão: 20/minute)
- **RATE_LIMIT_HEALTH**: Limite de requisições para health check (padrão: 100/minute)

Medidas de segurança implementadas:
- Headers de segurança HTTP (CSP, HSTS, X-Frame-Options, etc.)
- CORS restrito a origens configuradas
- Rate limiting em endpoints sensíveis
- Logs de segurança dedicados em `logs/auth.txt`
- Validação de configurações no startup

### Uso

```python
from api.rest.main import app
```

### Iniciar servidor

```bash
python boot.py api
```

Ou com uvicorn:

```bash
uvicorn api.rest.main:app --host 0.0.0.0 --port 8000 --reload
```

## Separação de Responsabilidades

| Sistema | Localização | Propósito |
|---------|-------------|-----------|
| WebSocket PocketOption | `api/pocketoption/` | Comunicação em tempo real |
| HTTP REST | `api/rest/` | Autenticação de usuários |
| Monitoramento | `boot.py` | Monitoramento de mercado |
