# OpenOB

Sistema de monitoramento e trading PocketOption com WebSocket e API REST.

## 📋 Pré-requisitos

- Python 3.12+
- pip

## 🚀 Instalação

```bash
python depen.py
```

Para dependências de desenvolvimento:

```bash
python depen.py --dev
```

Para atualizar dependências existentes:

```bash
python depen.py --upgrade
```

## 🔧 Configuração

1. Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` com suas configurações:
   - Configure seu SSID do PocketOption
   - Defina uma chave JWT forte para produção
   - Configure origens CORS permitidas

## 📂 Estrutura do Projeto

```
openob/
├── api/                   # APIs do projeto
│   ├── pocketoption/      # WebSocket PocketOption
│   └── rest/              # HTTP REST FastAPI
├── config/                # Configurações centralizadas
├── core/                  # Funcionalidades core
├── models/                # Modelos de dados
├── repositories/          # Camada de persistência
├── boot.py                # Script unificado (monitoramento/API)
├── depen.py               # Script de instalação de dependências
└── .env                   # Configurações (não commitar)
```

## 🏃 Executar

O script `boot.py` unificado gerencia tanto o monitoramento WebSocket quanto o servidor API HTTP.

### Monitoramento WebSocket (padrão)

```bash
python boot.py
```

Ou explicitamente:

```bash
python boot.py monitor
```

### Servidor API HTTP

```bash
python boot.py api
```

Ou com uvicorn diretamente:

```bash
uvicorn api.rest.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

## 🔒 Segurança

A API REST implementa:
- Autenticação JWT com access/refresh tokens
- Rate limiting em endpoints sensíveis
- Headers de segurança HTTP (CSP, HSTS, X-Frame-Options)
- CORS restrito configurável via .env
- Logs de segurança dedicados em `logs/auth.txt`

## 📝 Configurações via .env

- `JWT_SECRET_KEY`: Chave secreta para assinatura de tokens
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Tempo de expiração do access token
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`: Tempo de expiração do refresh token
- `CORS_ORIGINS`: Origens permitidas separadas por vírgula
- `RATE_LIMIT_*`: Limites de requisições por endpoint
- `POCKETOPTION_MONITOR_SSID`: SSID para monitoramento
- `LOG_LEVEL`: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## 📚 Documentação

- [API](api/README.md) - Documentação das APIs
- [Codebase](codebase.md) - Regras de codificação
