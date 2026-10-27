"""UserConnectionManager - Gerenciador de conexões WebSocket por usuário"""

import asyncio
import os
from typing import Dict, Optional
from datetime import datetime
from connection.websocket import WebSocketManager
from api.pocketoption.trading import TradingAPI
from core.constants import WEBSOCKET_ENDPOINTS
from core.logger import get_logger


logger = get_logger(__name__)


class UserConnectionManager:
    """Gerenciador de múltiplas conexões WebSocket por usuário"""

    def __init__(self, user_repository, strategy_manager, autotrade_repository=None):
        self.connections: Dict[int, WebSocketManager] = {}  # conexões por user_id
        self.trading_apis: Dict[int, TradingAPI] = {}  # TradingAPI por usuário
        self.user_repository = user_repository
        self.strategy_manager = strategy_manager
        self.autotrade_repository = autotrade_repository
        self._running = False
        self._listen_task = None
        self._polling_task = None
        self.connection_times: Dict[int, datetime] = {}  # timestamps de conexão

    def _log_user_event(self, user_id: int, event: str, details: str = ""):
        """Registrar evento específico do usuário em logs/users/{email}/user.log"""
        from config.settings import Settings

        if Settings.LOG_LEVEL.upper() != "DEBUG":
            return

        try:
            asyncio.create_task(self._log_user_event_async(user_id, event, details))
        except Exception as e:
            logger.error(f"Erro ao registrar log de usuário: {e}")

    async def _log_user_event_async(self, user_id: int, event: str, details: str = ""):
        """Registrar evento específico do usuário (async)"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return

            # Sanitizar email para usar como nome de arquivo
            safe_email = user.email.replace("@", "_at_").replace(".", "_dot_")
            user_log_file = f"logs/users/{safe_email}.log"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] Event: {event} | {details}\n"

            with open(user_log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

        except Exception as e:
            logger.error(f"Erro ao escrever log de usuário: {e}")

    async def _log_connection_event(self, user_id: int, event_type: str, reason: str = "", error: str = ""):
        """Registrar evento de conexão/desconexão com formato estruturado"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return

            # Sanitizar email para usar como nome de arquivo
            safe_email = user.email.replace("@", "_at_").replace(".", "_dot_")
            user_log_file = f"logs/users/{safe_email}.log"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if event_type == "CONNECT":
                # Conexão iniciada
                self.connection_times[user_id] = datetime.now()
                log_entry = f"[{timestamp}] CONEXÃO INICIADA | Usuário: {user.username} | Endpoint: DEMO\n"
            elif event_type == "CONNECTED":
                # Conexão estabelecida com sucesso
                log_entry = f"[{timestamp}] CONEXÃO ESTABELECIDA | Usuário: {user.username} | Status: Connected\n"
            elif event_type == "DISCONNECT":
                # Desconexão
                connection_time = ""
                if user_id in self.connection_times:
                    duration = datetime.now() - self.connection_times[user_id]
                    connection_time = f"Tempo conectado: {duration.total_seconds():.2f}s"
                    del self.connection_times[user_id]

                log_entry = f"[{timestamp}] DESCONECTADO | Usuário: {user.username} | Motivo: {reason} | {connection_time}\n"
                if error:
                    log_entry = log_entry.rstrip() + f" | Erro: {error}\n"

            with open(user_log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

        except Exception as e:
            logger.error(f"Erro ao escrever log de conexão: {e}")

    async def start_monitoring(self):
        """Iniciar monitoramento em tempo real"""
        self._running = True

        # Configurar injeções de dependências
        self.strategy_manager.set_user_connection_manager(self)

        # Usar polling diretamente (LISTEN/NOTIFY requer configuração complexa)
        logger.info("Usando polling para monitoramento de usuários")
        self._polling_task = asyncio.create_task(self.monitor_loop_polling())

        logger.info("UserConnectionManager iniciado")

    async def stop_monitoring(self):
        """Parar monitoramento"""
        self._running = False

        if self._listen_task:
            self._listen_task.cancel()

        if self._polling_task:
            self._polling_task.cancel()

        # Desconectar todos os usuários
        for user_id in list(self.connections.keys()):
            await self.disconnect_user(user_id, reason="system_shutdown")

        logger.info("UserConnectionManager parado")

    async def setup_database_notifications(self):
        """Configurar LISTEN/NOTIFY no PostgreSQL"""
        # Implementação será feita no boot.py com TRIGGERs
        # Aqui apenas placeholder para a lógica de LISTEN
        logger.info("LISTEN/NOTIFY setup será configurado no boot.py")

    async def monitor_loop_polling(self):
        """Fallback: polling a cada 1s"""
        while self._running:
            try:
                # Verificar usuários com autotrade ativo (is_active=True na config)
                active_autotrade_users = set()
                if self.autotrade_repository:
                    try:
                        all_configs = await self.autotrade_repository.get_all_configs()
                        active_autotrade_users = {config.user_id for config in all_configs if config.is_active}
                    except Exception as e:
                        logger.error(f"Erro ao obter configs de autotrade: {e}")

                # Verificar usuários ativos no sistema
                active_users = await self.user_repository.get_active_users()

                for user in active_users:
                    # Conectar apenas se autotrade config is_active=True
                    should_connect = user.id in active_autotrade_users

                    if should_connect and user.id not in self.connections:
                        await self.connect_user(user.id)
                    elif not should_connect and user.id in self.connections:
                        await self.disconnect_user(user.id, reason="autotrade_deactivated")

                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Erro no polling: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)

    async def connect_user(self, user_id: int):
        """Conectar usuário ao WebSocket com 3 tentativas de reconexão"""
        max_attempts = 3
        retry_delay = 5  # segundos

        # Log de início de conexão
        await self._log_connection_event(user_id, "CONNECT")

        for attempt in range(1, max_attempts + 1):
            try:
                user = await self.user_repository.get_by_id(user_id)
                if not user:
                    logger.error(f"Usuário {user_id} não encontrado")
                    await self._log_connection_event(user_id, "DISCONNECT", reason="user_not_found")
                    return

                # Obter config de autotrade
                config = None
                if self.autotrade_repository:
                    try:
                        config = await self.autotrade_repository.get_by_user(user_id)
                    except Exception as e:
                        logger.error(f"Erro ao obter config de autotrade: {e}")

                # Verificar SSID
                if user.mode == "demo":
                    ssid = user.ssid_demo
                    region = "DEMO"
                else:
                    ssid = user.ssid_real
                    region = await self.detect_best_endpoint()

                if not ssid:
                    logger.error(f"SSID vazio para usuário {user_id} em modo {user.mode}")
                    # Atualizar status no banco
                    user.is_connected = False
                    user.connection_status = "disconnected"
                    user.disconnect_reason = "missing_ssid"
                    await self.user_repository.update(user)
                    await self._log_connection_event(user_id, "DISCONNECT", reason="missing_ssid")
                    return

                # Criar conexão WebSocket
                ws_manager = WebSocketManager(region=region, name=f"User_{user_id}")
                await ws_manager.connect(ssid=ssid, auto_reconnect=False)  # Nós controlamos reconexão

                # Criar TradingAPI
                trading_api = TradingAPI(ws_manager)

                # Configurar handlers de eventos
                self._setup_event_handlers(trading_api, user_id)

                # Armazenar conexões
                self.connections[user_id] = ws_manager
                self.trading_apis[user_id] = trading_api

                # Atualizar status no banco
                user.is_connected = True
                user.connection_status = "connected"
                user.disconnect_reason = None
                await self.user_repository.update(user)

                masked_ssid = ssid[:20] + "..." if len(ssid) > 20 else ssid
                logger.info(f"Usuário {user_id} conectado com sucesso (SSID: {masked_ssid}, Região: {region})")
                self._log_user_event(user_id, "connect", f"SSID: {masked_ssid}, Endpoint: {region}, Status: connected")
                await self._log_connection_event(user_id, "CONNECTED")
                return  # Sucesso, sair do loop

            except Exception as e:
                logger.error(f"Tentativa {attempt}/{max_attempts} falhou para usuário {user_id}: {e}")
                self._log_user_event(user_id, "reconnect_attempt", f"Attempt: {attempt}/{max_attempts}, Error: {str(e)}")

                if attempt < max_attempts:
                    logger.info(f"Aguardando {retry_delay}s antes da próxima tentativa...")
                    await asyncio.sleep(retry_delay)
                else:
                    # Falhou todas as tentativas
                    logger.error(f"Não foi possível conectar usuário {user_id} após {max_attempts} tentativas")
                    await self._log_connection_event(user_id, "DISCONNECT", reason="max_attempts_reached", error=str(e))
                    user = await self.user_repository.get_by_id(user_id)
                    if user:
                        user.is_connected = False
                        user.connection_status = "disconnected"
                        user.disconnect_reason = "error"
                        await self.user_repository.update(user)
                        self._log_user_event(user_id, "error", f"Connection failed after {max_attempts} attempts: {str(e)}")

    async def disconnect_user(self, user_id: int, reason: str):
        """Desconectar usuário com motivo"""
        try:
            if user_id in self.connections:
                ws_manager = self.connections[user_id]
                await ws_manager.disconnect()
                del self.connections[user_id]

            if user_id in self.trading_apis:
                del self.trading_apis[user_id]

            # Atualizar status no banco
            user = await self.user_repository.get_by_id(user_id)
            if user:
                user.is_connected = False
                user.connection_status = "disconnected"
                user.disconnect_reason = reason
                await self.user_repository.update(user)

            logger.info(f"Usuário {user_id} desconectado: {reason}")
            await self._log_connection_event(user_id, "DISCONNECT", reason=reason)
            self._log_user_event(user_id, "disconnect", f"Reason: {reason}, Status: disconnected")

        except Exception as e:
            logger.error(f"Erro ao desconectar usuário {user_id}: {e}")

    async def detect_best_endpoint(self):
        """Auto-detectar melhor endpoint regional"""
        endpoints = [v for k, v in WEBSOCKET_ENDPOINTS.items() if k != "DEMO"]

        for endpoint in endpoints:
            try:
                # Simular teste de conectividade
                logger.debug(f"Testando endpoint: {endpoint}")
                # Na implementação real, testar conectividade aqui
                return endpoint
            except Exception:
                continue

        return "api-eu"  # Default

    def _setup_event_handlers(self, trading_api: TradingAPI, user_id: int):
        """Configurar handlers de eventos do WebSocket"""
        # Handler para balance update
        async def on_balance(data):
            self._log_user_event(user_id, "balance_update", f"Data: {data}")
            await self.trading_manager.on_balance_update(user_id, data)

        # Handler para todos os eventos (logging detalhado)
        async def on_all_events(event: str, data):
            self._log_user_event(user_id, f"ws_event_{event}", f"Data: {data}")

        # Adicionar handlers
        trading_api.ws_manager.add_event_handler("balance", on_balance)

        # Interceptador global para logging (desativado temporariamente para testar handlers da TradingAPI)
        # original_emit = trading_api.ws_manager._emit_event
        # async def patched_emit(event: str, data):
        #     await on_all_events(event, data)
        #     logger.debug(f"[USER CONNECTION MANAGER] Evento emitido: {event} para usuário {user_id}")
        #     return await original_emit(event, data)
        # trading_api.ws_manager._emit_event = patched_emit



    def get_user_status(self, user_id: int) -> Optional[Dict]:
        """Obter status da conexão do usuário"""
        if user_id in self.connections:
            return {
                "user_id": user_id,
                "is_connected": True,
                "connection_status": "connected"
            }
        return {
            "user_id": user_id,
            "is_connected": False,
            "connection_status": "disconnected"
        }

    def get_all_connections_status(self) -> Dict[int, Dict]:
        """Obter status de todas as conexões"""
        status = {}
        for user_id in self.connections:
            status[user_id] = self.get_user_status(user_id)
        return status
