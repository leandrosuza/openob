# Implementar Sistema de Gerenciamento de Conexões e Estratégias de Trading

Implementar sistema de gerenciamento de conexões WebSocket por usuário com is_active, monitoramento em tempo real, auto-aplicação de configs, sistema de estratégias em core/strategy/, estratégia scalping5s analisa histórico de ticks, logs em console/logs/ e desconexão diferenciada.

## Objetivo
Implementar sistema de gerenciamento de conexões WebSocket por usuário usando `is_active` para controle, monitoramento em tempo real via PostgreSQL LISTEN/NOTIFY (users + autotrade_configs), auto-aplicação de configs, auto-detect de região, desconexão diferenciada, logs em console (INFO) ou logs/ (DEBUG), e sistema de estratégias de trading com análise de histórico de ticks.

## Respostas do Usuário - Requisitos Finais
1. **Fallback LISTEN/NOTIFY** - Logar erro em console, fazer polling a cada 1s
2. **Região real** - Auto-detectar sempre a região funcional, sem usuário escolher
3. **SSID ausente** - Não conectar, logar erro
4. **Monitoramento configs** - Monitorar tanto `is_active` quanto `autotrade_configs` em tempo real
5. **Aplicação configs** - Auto-aplicar mudanças de configs em tempo real
6. **Logs produção** - INFO: apenas console, pasta logs/ fica vazia
7. **Limite reconexão** - Sem limite global de reconexões simultâneas
8. **Estratégias** - Implementar sistema de estratégias em `core/strategy/`
9. **Estratégia scalping 5s** - Criar `core/strategy/scalping5s.py` que analisa histórico de ticks
10. **Tabela autotrade_configs** - Adicionar campos necessários para estratégias
11. **TradingManager separado** - Criar TradingManager para executar trades
12. **Sem limite de trades** - Aguardar finalização do trade para executar próximo
13. **Estratégia analisa todos os ativos** - Gerar sinais individuais para cada ativo
14. **StrategyManager** - Criar para gerenciar análises de múltiplos ativos

## Requisitos Atualizados
1. **Gerenciar conexões por usuário** - Cada usuário tem sua própria conexão WebSocket
2. **Controlar via is_active** - Usar coluna `is_active` (True/False) para conectar/desconectar
3. **Monitoramento em tempo real** - LISTEN/NOTIFY em users e autotrade_configs
4. **Auto-aplicar configs** - Quando autotrade_configs mudar, aplicar automaticamente
5. **Modo de conexão** - Usar coluna `mode` (real ou demo) para determinar endpoint
6. **SSID correto** - Usar `ssid_demo` ou `ssid_real` dependendo do modo
7. **Tabela autotrade_configs** - Incluir `strategy_name` e campos necessários para estratégias
8. **Sistema de estratégias** - Implementar estrutura em `core/strategy/`
9. **Estratégia scalping 5s** - Analisar histórico de ticks para sinais de compra/venda
10. **StrategyManager** - Gerenciar análises de múltiplos ativos por usuário
11. **TradingManager** - Gerenciar execução de trades separado de conexões
12. **Logs em console** - Em INFO, apenas console. Em DEBUG, pasta logs/ usada
13. **Monitoramento via polling** - Fallback de 1s se LISTEN/NOTIFY falhar
14. **Auto-detect região** - Sempre detectar automaticamente região funcional para modo real
15. **Reconexão** - 3 tentativas com 5s delay, sem limite global

## Análise do Código Atual
- `WebSocketManager` - Gerencia uma única conexão WebSocket
- `MonitorAPI` - Gerencia duas conexões para monitoramento global
- `User` model - Tem `ssid_demo` e `ssid_real`, is_active, mas não tem `mode`
- `constants.py` - Tem endpoints para DEMO e regiões reais (api-eu, api-c, etc.)
- `models/trading.py` - Já tem `Order`, `OrderStatus`, `OrderResult` models
- `repositories/tick_repository` - Já tem `get_recent` para obter histórico de ticks

## Implementação

### 1. Atualizar Model User
**Arquivo:** `models/user.py`

Adicionar campos:
- `mode: str = "demo"` - "demo" ou "real"
- `is_connected: bool = False` - status da conexão
- `connection_status: Optional[str] = None` - detalhes do status (connected, disconnected, error, disconnected_by_system, disconnected_by_user)
- `disconnect_reason: Optional[str] = None` - motivo da desconexão

### 2. Criar Model AutotradeConfig
**Arquivo:** `models/autotrade.py` (novo)

Criar modelo para configs de trading:
- `id`, `user_id`, `strategy_name`, `parameters` (JSON), `is_active`

### 3. Criar Model Trade/Order
**Arquivo:** `models/trading.py` (já existe, ajustar se necessário)

Adicionar `Trade` para registrar operações:
- `id`, `user_id`, `asset`, `amount`, `direction`, `duration`, `status`, `profit`, `created_at`, `closed_at`

### 4. Atualizar Repositório User
**Arquivo:** `repositories/sqlite/sqlite_user_repository.py` e `repositories/postgresql/postgres_user_repository.py`

- Adicionar colunas `mode`, `is_connected`, `connection_status`, `disconnect_reason` na tabela users
- Atualizar métodos `create` e `update` para incluir novos campos
- Adicionar método `get_active_users()` - retorna usuários com is_active=True
- Adicionar método `get_all_users()` - retorna todos os usuários para monitoramento

### 5. Criar Repositório AutotradeConfig
**Arquivo:** `repositories/interfaces/autotrade_repository_interface.py`, `repositories/sqlite/sqlite_autotrade_repository.py`, `repositories/postgresql/postgres_autotrade_repository.py`

Interface:
- `create(config: AutotradeConfig) -> AutotradeConfig`
- `get_by_user(user_id: int) -> Optional[AutotradeConfig]`
- `update(config: AutotradeConfig) -> AutotradeConfig`
- `delete(user_id: int) -> bool`

### 6. Criar Repositório Trade
**Arquivo:** `repositories/interfaces/trade_repository_interface.py`, `repositories/sqlite/sqlite_trade_repository.py`, `repositories/postgresql/postgres_trade_repository.py`

Interface:
- `create(trade: Trade) -> Trade`
- `get_by_user(user_id: int) -> List[Trade]`
- `get_by_id(trade_id: int) -> Optional[Trade]`
- `update_status(trade_id: int, status: str) -> Trade`

### 7. Criar Estrutura de Estratégias
**Arquivo:** `core/strategy/__init__.py` (novo)

- BaseStrategy classe abstrata
- Métodos: `analyze()`, `get_signal()`, `get_parameters()`

### 8. Criar Estratégia Scalping 5s
**Arquivo:** `core/strategy/scalping5s.py` (novo)

Responsabilidades:
- Analisar histórico de ticks (últimos N ticks)
- Identificar padrões de compra/venda
- Calcular sinais baseados em indicadores (média móvel, RSI, etc.)
- Retornar direção (call/put) ou nenhum sinal
- Parâmetros configuráveis (lookback_period, threshold, etc.)

Métodos:
- `__init__(parameters: dict)` - Inicializar com parâmetros da estratégia
- `async def analyze(ticks: List[Dict]) -> Dict` - Analisar ticks e retornar sinal
- `get_required_parameters() -> List[str]` - Retornar parâmetros necessários

### 9. Criar StrategyManager
**Arquivo:** `core/strategy_manager.py` (novo)

Responsabilidades:
- Gerenciar estratégias por usuário
- Analisar múltiplos ativos simultaneamente
- Gerar sinais individuais para cada ativo
- Enviar sinais para TradingManager
- Usar tick_repository para obter histórico

Métodos:
- `async def start_strategy(user_id: int, strategy_name: str, parameters: dict)` - Iniciar estratégia
- `async def stop_strategy(user_id: int)` - Parar estratégia
- `async def analyze_all_assets(user_id: int)` - Analisar todos os ativos monitorados
- `async def apply_config(user_id: int, config: AutotradeConfig)` - Aplicar config de autotrade

### 10. Criar TradingManager
**Arquivo:** `core/trading_manager.py` (novo)

Responsabilidades:
- Gerenciar execução de trades
- Receber sinais do StrategyManager
- Aguardar finalização do trade antes de executar próximo
- Enviar ordens via WebSocket do usuário
- Registrar trades no banco

Métodos:
- `async def execute_trade(user_id: int, signal: dict)` - Executar trade baseado em sinal
- `async def send_order(user_id: int, order: Order)` - Enviar ordem via WebSocket
- `async def monitor_trade(user_id: int, trade_id: int)` - Monitorar resultado do trade
- `is_trade_in_progress(user_id: int) -> bool` - Verificar se há trade em andamento

### 11. Criar UserConnectionManager
**Arquivo:** `core/user_connection_manager.py`

Responsabilidades:
- Gerenciar múltiplas conexões WebSocket por usuário
- **Monitorar em tempo real** mudanças em `is_active` e `autotrade_configs` usando PostgreSQL LISTEN/NOTIFY
- **Auto-aplicar configs** - Quando autotrade_configs mudar, atualizar estratégia em tempo real via StrategyManager
- Conectar/desconectar automaticamente baseado em `is_active`
- Reconexão automática (3 tentativas, 5s delay)
- Diferenciar desconexão por queda vs solicitada
- **Logs em console** - Em INFO, apenas console. Em DEBUG, usar pasta logs/

Métodos principais:
- `async def connect_user(user_id: int)` - Conectar usuário ao WebSocket
- `async def disconnect_user(user_id: int, reason: str)` - Desconectar usuário com motivo
- `async def setup_database_notifications()` - Configurar LISTEN/NOTIFY no PostgreSQL
- `async def monitor_loop_polling()` - Fallback: polling a cada 1s
- `async def apply_autotrade_config(user_id: int, config: AutotradeConfig)` - Aplicar configs via StrategyManager
- `async def start_monitoring()` - Iniciar monitoramento em tempo real
- `async def stop_monitoring()` - Parar monitoramento
- `get_user_status(user_id: int)` - Obter status da conexão do usuário
- `get_all_connections_status()` - Obter status de todas as conexões

### 12. Monitoramento em Tempo Real com PostgreSQL
**Arquivo:** `core/user_connection_manager.py`

Usar PostgreSQL LISTEN/NOTIFY:
- **TRIGGER na tabela users** - Dispara notificação quando `is_active` ou `mode` muda
- **TRIGGER na tabela autotrade_configs** - Dispara notificação quando configs mudam
- `UserConnectionManager` faz LISTEN nos canais `user_changes` e `autotrade_changes`
- Quando notificação chega, verifica qual tabela mudou e processa
- **Fallback**: Se LISTEN/NOTIFY falhar, usar polling a cada 1s logando erro em console

```sql
-- TRIGGER para users
CREATE OR REPLACE FUNCTION notify_user_changes()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('user_changes', NEW.id::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_is_active_trigger
AFTER UPDATE OF is_active ON users
FOR EACH ROW EXECUTE FUNCTION notify_user_changes();

CREATE TRIGGER user_mode_trigger
AFTER UPDATE OF mode ON users
FOR EACH ROW EXECUTE FUNCTION notify_user_changes();

-- TRIGGER para autotrade_configs
CREATE OR REPLACE FUNCTION notify_autotrade_changes()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('autotrade_changes', NEW.user_id::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER autotrade_config_trigger
AFTER INSERT OR UPDATE ON autotrade_configs
FOR EACH ROW EXECUTE FUNCTION notify_autotrade_changes();
```

### 13. Auto-detect Endpoint Regional
**Arquivo:** `core/user_connection_manager.py`

Função:
- `async def detect_best_endpoint()` - Testar conectividade e escolher endpoint mais rápido
- Tentar endpoints em ordem: api-eu, api-c, api-fin, api-us4, etc.
- Usar o primeiro que responder com sucesso em menos de 2s
- Sempre executar auto-detect para modo real, sem escolha do usuário

### 14. Atualizar boot.py
**Arquivo:** `boot.py`

- Inicializar `UserConnectionManager` no startup
- Inicializar `StrategyManager` no startup
- Inicializar `TradingManager` no startup
- Chamar `start_monitoring()` para iniciar monitoramento em tempo real
- Chamar `sync_all_users()` - conectar todos os usuários com is_active=True no startup
- Adicionar handler para desconectar todos ao encerrar o sistema
- Inicializar tabelas `autotrade_configs` e `trades` se não existirem
- Criar TRIGGERs para LISTEN/NOTIFY se não existirem

### 15. Criar Router de User Connections
**Arquivo:** `api/rest/user_connection_router.py`

Endpoints:
- `POST /users/{user_id}/connect` - Conectar usuário manualmente
- `POST /users/{user_id}/disconnect` - Desconectar usuário manualmente
- `GET /users/{user_id}/status` - Obter status da conexão
- `GET /users/connections` - Listar todas as conexões ativas
- `PUT /users/{user_id}/mode` - Atualizar modo (demo/real) - dispara reconexão
- `PUT /users/{user_id}/activate` - Ativar usuário (is_active=True) - dispara conexão
- `PUT /users/{user_id}/deactivate` - Desativar usuário (is_active=False) - dispara desconexão

### 16. Criar Router de AutotradeConfigs
**Arquivo:** `api/rest/autotrade_router.py` (novo)

Endpoints:
- `POST /autotrade/configs` - Criar config de trading
- `GET /autotrade/configs/{user_id}` - Obter config do usuário
- `PUT /autotrade/configs/{user_id}` - Atualizar config (auto-aplicado em tempo real)
- `DELETE /autotrade/configs/{user_id}` - Deletar config
- `GET /strategies` - Listar estratégias disponíveis
- `GET /strategies/{name}/parameters` - Obter parâmetros necessários de uma estratégia

### 17. Criar Router de Trades
**Arquivo:** `api/rest/trade_router.py` (novo)

Endpoints:
- `GET /trades/user/{user_id}` - Listar trades do usuário
- `GET /trades/{trade_id}` - Obter detalhes de um trade
- `POST /trades/manual` - Executar trade manualmente
- `GET /trades/active` - Listar trades em andamento

### 18. Atualizar boot.py - Logs
**Arquivo:** `boot.py` - função `reset_logs()`

- Em INFO: não criar arquivos em logs/, apenas console
- Em DEBUG: criar arquivos em logs/ws/, logs/plans/, logs/users/
- logs/users/{email}/user.txt apenas em DEBUG

### 19. Migração do Banco de Dados
**Arquivo:** `boot.py` - função `init_database()`

- Adicionar colunas `mode`, `is_connected`, `connection_status`, `disconnect_reason` na tabela users se não existirem
- Criar tabela `autotrade_configs` se não existir
- Criar tabela `trades` se não existir
- Criar TRIGGERs para LISTEN/NOTIFY se não existirem
- Valor padrão: mode="demo", is_connected=False

## Fluxo de Conexão e Monitoramento

### Monitoramento em Tempo Real (LISTEN/NOTIFY)
1. **UserConnectionManager inicia**:
   - Conecta ao PostgreSQL
   - Executa `LISTEN user_changes, autotrade_changes`
   - Loop espera notificações

2. **Quando notificação de user_changes chega**:
   - Pegar user_id da notificação
   - Consultar estado atual do usuário
   - Se `is_active=True` e `not is_connected` → conectar
   - Se `is_active=False` e `is_connected` → desconectar (reason="deactivated")
   - Se `mode` mudou → desconectar e reconectar com novo endpoint

3. **Quando notificação de autotrade_changes chega**:
   - Pegar user_id da notificação
   - Obter config atual de autotrade_configs
   - Chamar `apply_autotrade_config(user_id, config)`:
     - Chamar StrategyManager para aplicar config
     - StrategyManager carrega estratégia baseada em `strategy_name`
     - Inicia análise de ticks para todos os ativos

4. **Fallback Polling**:
   - Se LISTEN/NOTIFY falhar, logar erro em console
   - Iniciar polling a cada 1s
   - Verificar todos os usuários e configs manualmente
   - Tentar reconectar LISTEN/NOTIFY periodicamente

### Fluxo de Análise de Estratégia
1. **Config mudou** (autotrade_configs):
   - StrategyManager recebe config
   - Obter `strategy_name` do config
   - Importar classe de estratégia de `core/strategy/`
   - Ex: `from core.strategy.scalping5s import Scalping5sStrategy`
   - Instanciar estratégia com `parameters` do config
   - Registrar estratégia para o usuário

2. **Análise de ticks**:
   - StrategyManager chama `tick_repo.get_recent(asset, limit=N)` para obter histórico
   - Estratégia analisa ticks e retorna sinal (call/put/nenhum)
   - Se sinal, enviar para TradingManager
   - TradingManager verifica se há trade em andamento
   - Se não houver, executa trade
   - Se houver, aguarda finalização

### Fluxo de Execução de Trade
1. **Sinal recebido** (StrategyManager → TradingManager):
   - TradingManager recebe sinal (asset, direction, amount, duration)
   - Verifica se há trade em andamento para o usuário
   - Se sim, descarta sinal (aguarda finalização)
   - Se não, cria ordem

2. **Executar ordem**:
   - TradingManager obtém WebSocket do usuário
   - Envia ordem via WebSocket
   - Cria registro na tabela trades (status="pending")
   - Inicia monitoramento do trade

3. **Monitorar resultado**:
   - TradingManager aguarda resposta do WebSocket
   - Atualiza status para "open" quando aberto
   - Atualiza status para "win/loss/timeout" quando finalizado
   - Atualiza profit
   - Marca trade como finalizado
   - Próximo sinal pode ser executado

### Fluxo de Conexão Individual
1. **Verificar SSID:**
   - Se `mode == "demo"` → usar `ssid_demo`
   - Se `mode == "real"` → usar `ssid_real`
   - Se SSID estiver vazio → logar erro em console, não conectar, manter is_connected=False

2. **Determinar endpoint:**
   - Se `mode == "demo"` → usar endpoint `DEMO`
   - Se `mode == "real"` → auto-detectar melhor endpoint regional (sempre)

3. **Criar conexão WebSocket:**
   - Instanciar `WebSocketManager` com região correta
   - Chamar `connect(ssid, auto_reconnect=True)`
   - Atualizar `is_connected=True`, `connection_status="connected"` no banco
   - Em DEBUG: logar em `logs/users/{email}/user.txt`
   - Em INFO: logar apenas em console

4. **Reconexão automática:**
   - Se conexão cair, tentar reconectar 3 vezes com delay de 5s
   - Em DEBUG: logar cada tentativa em `logs/users/{email}/user.txt`
   - Em INFO: logar apenas em console
   - Após 3 falhas consecutivas, marcar `connection_status="error"` e desistir
   - Monitoramento em tempo real tentará reconectar quando `is_active` mudar

5. **Desconexão:**
   - Chamar `disconnect()` no WebSocketManager
   - Atualizar `is_connected=False`, `connection_status="disconnected"`, `disconnect_reason` no banco
   - Em DEBUG: logar desconexão com motivo em `logs/users/{email}/user.txt`
   - Em INFO: logar apenas em console

## Logs

**Em INFO:**
- Apenas console
- Pasta logs/ fica vazia

**Em DEBUG:**
- Console + pasta logs/
- Estrutura:
```
logs/
  users/
    {email}/
      user.txt  - Logs de conexão WebSocket, desconexões, erros, SSID, etc.
  ws/
    monitoring_payout.txt
    monitoring_actives.txt
  plans/
    subscriptions.txt
    payments.txt
  database.txt
  security.txt
  auth.txt
```

**Conteúdo (DEBUG):**
- Timestamp
- Evento (connect, disconnect, error, reconnect, mode_changed, is_active_changed, config_changed, strategy_loaded, signal_detected, trade_executed)
- SSID usado (ou "EMPTY" se vazio)
- Endpoint usado
- Status da conexão
- Motivo da desconexão (deactivated, manual, error, mode_changed)
- Tentativas de reconexão (1/3, 2/3, 3/3)
- Erros detalhados
- Sinais de trading (call/put/nenhum)
- Parâmetros da estratégia
- Detalhes de trades executados

## Tabelas do Banco de Dados

### Tabela autotrade_configs
```sql
CREATE TABLE autotrade_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    strategy_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Parâmetros exemplo para scalping5s:**
```json
{
  "lookback_period": 100,
  "threshold": 0.7,
  "min_ticks": 20,
  "risk_per_trade": 0.02
}
```

### Tabela trades
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    asset VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- call ou put
    duration INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, open, win, loss, timeout
    profit DECIMAL(10, 2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE
);
```

## Estrutura de Estratégias

**Arquivo:** `core/strategy/__init__.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseStrategy(ABC):
    """Classe base para estratégias de trading"""

    @abstractmethod
    def get_name(self) -> str:
        """Retornar nome da estratégia"""
        pass

    @abstractmethod
    def get_required_parameters(self) -> List[str]:
        """Retornar lista de parâmetros necessários"""
        pass

    @abstractmethod
    async def analyze(self, ticks: List[Dict], parameters: Dict[str, Any]) -> Dict:
        """Analisar ticks e retornar sinal"""
        pass
```

## Estratégia Scalping 5s

**Arquivo:** `core/strategy/scalping5s.py`

Responsabilidades:
- Analisar últimos N ticks (configurável via `lookback_period`)
- Calcular indicadores:
  - Média móvel curta (ex: 5 ticks)
  - Direção do último tick
  - Volatilidade
- Gerar sinal quando:
  - Média móvel cruza em direção oposta (sinal de reversão)
  - Padrão de ticks indica entrada
- Retornar sinal: `{ "signal": "call/put/none", "confidence": 0.0-1.0, "reason": "..." }`

## Segurança

- Validação de ownership - usuário só pode gerenciar sua própria conexão
- Rate limiting em endpoints de conexão
- Validação de mode (apenas "demo" ou "real")
- Validação de strategy_name (deve existir em core/strategy/)
- Validação de parâmetros (usar get_required_parameters())
- Não expor SSID em logs ou respostas (mascarar se necessário)
- Logs de segurança para tentativas não autorizadas

## Testes

- Testar LISTEN/NOTIFY do PostgreSQL
- Testar fallback polling a cada 1s
- Testar conexão em modo demo
- Testar conexão em modo real com auto-detect
- Testar mudança de is_active de False para True (deve conectar)
- Testar mudança de is_active de True para False (deve desconectar)
- Testar mudança de mode (demo→real deve reconectar)
- Testar SSID vazio (deve logar erro e não conectar)
- Testar 3 tentativas de reconexão com delay de 5s
- Testar auto-aplicação de configs de trading
- Testar carregamento de estratégia scalping5s
- Testar análise de ticks com scalping5s
- Testar StrategyManager analisando múltiplos ativos
- Testar TradingManager executando trades
- Testar aguardo de finalização de trade antes de próximo
- Verificar logs em DEBUG vs INFO
- Testar múltiplos usuários conectados simultaneamente
- Testar desconexão diferenciada (por queda vs solicitada)

## Arquivos a Modificar
1. `models/user.py` - Adicionar campos mode, is_connected, connection_status, disconnect_reason
2. `models/trading.py` - Adicionar model Trade
3. `repositories/sqlite/sqlite_user_repository.py` - Adicionar colunas na tabela
4. `repositories/postgresql/postgres_user_repository.py` - Adicionar colunas na tabela
5. `core/logger.py` - Adicionar setup_user_logger()
6. `boot.py` - Inicializar UserConnectionManager, StrategyManager, TradingManager, migrar colunas, criar tabelas, criar TRIGGER, ajustar reset_logs()
7. `api/rest/user_router.py` - Remover endpoints de mode/activate (movidos para user_connection_router)
8. `api/rest/main.py` - Incluir user_connection_router, autotrade_router e trade_router
9. `config/settings.py` - Adicionar MONITOR_POLL_INTERVAL (fallback)

## Arquivos a Criar
1. `models/autotrade.py` - Model AutotradeConfig
2. `core/strategy/__init__.py` - BaseStrategy e estrutura de estratégias
3. `core/strategy/scalping5s.py` - Estratégia scalping 5s
4. `core/strategy_manager.py` - Gerenciador de estratégias por usuário
5. `core/trading_manager.py` - Gerenciador de execução de trades
6. `repositories/interfaces/autotrade_repository_interface.py` - Interface de autotrade
7. `repositories/sqlite/sqlite_autotrade_repository.py` - Repositório SQLite de autotrade
8. `repositories/postgresql/postgres_autotrade_repository.py` - Repositório PostgreSQL de autotrade
9. `repositories/interfaces/trade_repository_interface.py` - Interface de trades
10. `repositories/sqlite/sqlite_trade_repository.py` - Repositório SQLite de trades
11. `repositories/postgresql/postgres_trade_repository.py` - Repositório PostgreSQL de trades
12. `core/user_connection_manager.py` - Gerenciador de conexões com LISTEN/NOTIFY, fallback polling, auto-detect
13. `api/rest/user_connection_router.py` - Router para gerenciar conexões
14. `api/rest/autotrade_router.py` - Router para configs de trading e estratégias
15. `api/rest/trade_router.py` - Router para trades

## Riscos e Considerações
- **LISTEN/NOTIFY no PostgreSQL** - Funciona apenas com PostgreSQL. Fallback para polling rápido (1s) com log em console.
- **Múltiplas conexões simultâneas** - PostgreSQL já resolveu este problema
- **Loop de monitoramento** - LISTEN/NOTIFY é eficiente, mas precisa de TRIGGER no banco
- **SSID inválido/vazio** - Tratar erro, logar em console, marcar como connection_status="error"
- **Endpoint real indisponível** - Auto-detect deve tentar múltiplos endpoints
- **Longevidade** - Implementar heartbeat e reconexão agressiva
- **Race condition** - LISTEN/NOTIFY sincroniza mudanças em tempo real
- **Auto-aplicação configs** - Precisa ser thread-safe para não conflitar com trading
- **Análise de ticks** - Precisa ser eficiente para não afetar performance
- **Backtesting** - Estratégia scalping5s deve ser testada com histórico real antes de usar em produção
- **Execução de trades** - TradingManager deve garantir que não haja trades simultâneos por usuário
- **StrategyManager** - Deve gerenciar múltiplos ativos sem sobrecarregar o sistema
- **Coordenação** - UserConnectionManager, StrategyManager e TradingManager devem coordenar corretamente
