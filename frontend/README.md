# OpenOB Frontend

Frontend React + TypeScript + Vite para a plataforma de trading OpenOB.

## Estrutura Flat e Minimalista

- Design limpo e moderno
- Cores: Primary (azul), Secondary (cinza), Dark (navy), Light (branco)
- Componentes reutilizáveis
- Tipagem TypeScript completa

## Instalação

```bash
cd frontend
npm install
```

## Desenvolvimento

```bash
npm run dev
```

O frontend vai rodar em `http://localhost:3000` com proxy para o backend em `http://localhost:8000`.

## Build

```bash
npm run build
```

## Telas Implementadas

1. **Login** (`/login`)
   - Formulário de autenticação
   - Tratamento de erros
   - Redirecionamento para dashboard

2. **Register** (`/register`)
   - Formulário de cadastro
   - Campos: username, email, password, ssid_demo, ssid_real (opcional)
   - Validação de campos

3. **Dashboard** (`/dashboard`)
   - Exibe informações do usuário
   - Saldo, status, plano
   - Botões para funcionalidades futuras

## Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router v6
- Axios

## Integração com Backend

O frontend se conecta ao backend FastAPI através da API REST:
- `/api/auth/login` - Login
- `/api/auth/register` - Registro
- `/api/auth/me` - Obter usuário atual
- `/api/auth/logout` - Logout

Tokens JWT são armazenados no localStorage e enviados automaticamente em cada requisição.
