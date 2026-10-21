# OpenOB - Plataforma de Trading Multi-Usuário

Sistema completo de trading multi-usuário com PocketOption, WebSocket connections, estratégias de autotrade e monitoramento em tempo real.

## 📁 Estrutura do Projeto

```
openob/
├── backend/          # FastAPI + Python
│   ├── api/         # Rotas REST
│   ├── core/        # Lógica de negócio (managers, estratégias)
│   ├── models/      # Pydantic models
│   ├── repositories/# PostgreSQL repositories
│   ├── config/      # Configurações
│   └── boot.py      # Entry point
├── frontend/        # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/   # Login, Register, Dashboard
│   │   ├── services/# API services
│   │   └── types/   # TypeScript types
│   └── package.json
└── README.md
```

## 🚀 Stack Tecnológico

### Backend
- **Framework**: FastAPI
- **Banco de Dados**: PostgreSQL
- **WebSocket**: PocketOption WebSocket API
- **Async**: asyncio + asyncpg
- **Autenticação**: JWT (python-jose)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **HTTP**: Axios

## 🔧 Instalação

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Configure o arquivo `.env`:
```env
DATABASE_TYPE=postgresql
POSTGRES_HOST=turntable.proxy.rlwy.net
POSTGRES_PORT=21912
POSTGRES_DB=railway
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

Rodar backend:
```bash
python boot.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

O frontend vai rodar em `http://localhost:3000`.

## 📋 Funcionalidades

### ✅ Implementado

- **Multi-usuário**: Suporte a múltiplos usuários simultâneos
- **Autenticação**: JWT com refresh tokens
- **WebSocket**: Conexões WebSocket por usuário (demo/real)
- **Autotrade**: Sistema de autotrade com estratégias configuráveis
- **Estratégias**: Estratégia scalping5s com indicadores (MA, RSI)
- **Monitoramento**: Monitor global de ativos com payout
- **Managers**: StrategyManager, TradingManager, UserConnectionManager
- **PostgreSQL**: LISTEN/NOTIFY para sincronização em tempo real
- **Frontend**: Tela de autenticação (login/register) flat e minimalista

### 🔄 Em Desenvolvimento

- Dashboard completo com gráficos
- Configuração de estratégias via UI
- Visualização de sinais em tempo real
- Histórico de trades
- Gerenciamento de planos/subscription

## 🔐 Segurança

- Senhas hash com bcrypt
- Tokens JWT com expiração
- SSIDs não expostos em logs
- Rate limiting nas rotas
- Validação de campos

## 📡 API Endpoints

### Autenticação
- `POST /api/auth/register` - Registrar usuário
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Renovar token
- `GET /api/auth/me` - Obter usuário atual
- `POST /api/auth/logout` - Logout

### Conexões de Usuário
- `POST /api/user-connection/connect` - Conectar usuário
- `POST /api/user-connection/disconnect` - Desconectar usuário
- `GET /api/user-connection/status` - Status da conexão

### Autotrade
- `GET /api/autotrade/config` - Obter configuração
- `POST /api/autotrade/config` - Atualizar configuração

## 📝 Licença

MIT License
