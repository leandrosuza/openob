"""Trade Executor - Executa trades baseados em sinais da estratégia"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from config.settings import Settings

# Configurar logger específico para trade executor
trading_logger = logging.getLogger("trading.trade_executor")
trading_logger.setLevel(logging.DEBUG)

# Handler para arquivo em logs/trading/trading_manager.log
trading_log_dir = Path("logs/trading")
trading_log_dir.mkdir(parents=True, exist_ok=True)
trading_file_handler = logging.FileHandler(trading_log_dir / "trading_manager.log")
trading_file_handler.setLevel(logging.DEBUG)
trading_file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
trading_logger.addHandler(trading_file_handler)

logger = trading_logger


class TradeExecutor:
    """Executa trades baseados em sinais da estratégia"""

    def __init__(self, user_connection_manager, strategy_manager):
        self.user_connection_manager = user_connection_manager
        self.strategy_manager = strategy_manager
        
        # Lock por usuário para evitar trades simultâneos
        self.user_locks: Dict[int, asyncio.Lock] = {}
        
        # Estado de trades ativos por usuário
        self.active_trades: Dict[int, Dict[str, Any]] = {}
        
        # Timeout para ordens (1.5x o duration da estratégia)
        self.trade_timeout_multiplier = 1.5

    async def process_signal(self, signal: Dict[str, Any]):
        """Processa um sinal da estratégia e executa trades para usuários com autotrade ativo"""
        try:
            if Settings.LOG_LEVEL.upper() == "DEBUG":
                logger.info(f"[TRADE EXECUTOR] Processando sinal: {signal}")

            # Filtrar usuários com autotrade ativo
            active_users = await self._get_active_users()
            
            if not active_users:
                if Settings.LOG_LEVEL.upper() == "DEBUG":
                    logger.info("[TRADE EXECUTOR] Nenhum usuário com autotrade ativo")
                return

            # Executar trade para cada usuário ativo
            for user_id, config in active_users.items():
                await self._execute_trade_for_user(user_id, config, signal)

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao processar sinal: {e}")

    async def _get_active_users(self) -> Dict[int, Dict[str, Any]]:
        """Retorna usuários com autotrade ativo e suas configurações"""
        try:
            if not self.user_connection_manager:
                return {}

            # Obter repository de autotrade e usuário
            autotrade_repo = self.user_connection_manager.autotrade_repository
            user_repo = self.user_connection_manager.user_repository
            
            # Buscar todas as configs ativas
            active_configs = await autotrade_repo.get_active_strategies()
            
            if not active_configs:
                return {}

            # Converter para dict {user_id: config}
            result = {}
            for config in active_configs:
                user_id = config.user_id
                if user_id:
                    # Obter SSID do usuário
                    user = await user_repo.get_by_id(user_id)
                    ssid_demo = user.ssid_demo if user else None
                    ssid_real = user.ssid_real if user else None
                    
                    result[user_id] = {
                        "user_id": user_id,
                        "strategy_name": config.strategy_name,
                        "parameters": config.parameters,
                        "amount": config.amount,
                        "is_active": config.is_active,
                        "ssid_demo": ssid_demo,
                        "ssid_real": ssid_real
                    }

            if Settings.LOG_LEVEL.upper() == "DEBUG":
                logger.info(f"[TRADE EXECUTOR] Usuários com autotrade ativo: {list(result.keys())}")

            return result

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao buscar usuários ativos: {e}")
            return {}

    async def _execute_trade_for_user(self, user_id: int, config: Dict[str, Any], signal: Dict[str, Any]):
        """Executa trade para um usuário específico"""
        try:
            # 1. Validação de Configuração do Usuário
            if not await self._validate_user_config(user_id, config):
                return

            # 2. Validação do Sinal
            if not await self._validate_signal(signal):
                return

            # 3. Verificar se usuário já tem trade ativo
            if user_id in self.active_trades:
                logger.info(f"[TRADE EXECUTOR] Usuário {user_id} já tem trade ativo, ignorando")
                return

            # 4. Obter lock do usuário
            if user_id not in self.user_locks:
                self.user_locks[user_id] = asyncio.Lock()

            async with self.user_locks[user_id]:
                # 5. Verificar conexão WebSocket
                if not await self._check_user_connection(user_id):
                    logger.warning(f"[TRADE EXECUTOR] Usuário {user_id} não está conectado, trade não executado")
                    return

                # 6. Executar trade
                await self._execute_trade(user_id, config, signal)

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao executar trade para usuário {user_id}: {e}")

    async def _validate_user_config(self, user_id: int, config: Dict[str, Any]) -> bool:
        """Valida configuração do usuário"""
        try:
            # Verificar se is_active=True
            if not config.get("is_active", False):
                logger.info(f"[TRADE EXECUTOR] Usuário {user_id} não tem autotrade ativo")
                return False

            # Verificar se SSID está configurado
            ssid_demo = config.get("ssid_demo")
            ssid_real = config.get("ssid_real")
            
            if not ssid_demo and not ssid_real:
                logger.warning(f"[TRADE EXECUTOR] Usuário {user_id} não tem SSID configurado")
                return False

            # Verificar se estratégia existe
            strategy_name = config.get("strategy_name")
            if not strategy_name:
                logger.warning(f"[TRADE EXECUTOR] Usuário {user_id} não tem estratégia configurada")
                return False

            # Verificar amount
            amount = config.get("amount", 0)
            if amount <= 0:
                logger.warning(f"[TRADE EXECUTOR] Usuário {user_id} tem amount inválido: {amount}")
                return False

            if Settings.LOG_LEVEL.upper() == "DEBUG":
                logger.info(f"[TRADE EXECUTOR] Configuração do usuário {user_id} validada")

            return True

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao validar configuração do usuário {user_id}: {e}")
            return False

    async def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Valida o sinal da estratégia"""
        try:
            # Verificar se sinal é válido (CALL/PUT, não NONE)
            signal_type = signal.get("signal", "").lower()
            if signal_type not in ["call", "put"]:
                logger.info(f"[TRADE EXECUTOR] Sinal inválido: {signal_type}")
                return False

            # Verificar confiança
            confidence = signal.get("confidence", 0.0)
            min_confidence = 0.5  # TODO: Tornar configurável
            if confidence < min_confidence:
                logger.info(f"[TRADE EXECUTOR] Confiança abaixo do threshold: {confidence} < {min_confidence}")
                return False

            # Verificar payout
            payout = signal.get("payout", 0)
            if payout < 80:
                logger.info(f"[TRADE EXECUTOR] Payout abaixo do threshold: {payout}% < 80%")
                return False

            if Settings.LOG_LEVEL.upper() == "DEBUG":
                logger.info(f"[TRADE EXECUTOR] Sinal validado: {signal_type} (confiança: {confidence}, payout: {payout}%)")

            return True

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao validar sinal: {e}")
            return False

    async def _check_user_connection(self, user_id: int) -> bool:
        """Verifica se o usuário está conectado"""
        try:
            if not self.user_connection_manager:
                return False

            # Verificar se há conexão WebSocket ativa
            if user_id in self.user_connection_manager.connections:
                ws_manager = self.user_connection_manager.connections[user_id]
                if ws_manager and ws_manager.is_connected:
                    return True

            # Verificar flag is_connected no banco
            user_repo = self.user_connection_manager.user_repository
            user = await user_repo.get_by_id(user_id)
            if user and user.is_connected:
                return True

            return False

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao verificar conexão do usuário {user_id}: {e}")
            return False

    async def _execute_trade(self, user_id: int, config: Dict[str, Any], signal: Dict[str, Any]):
        """Executa o trade"""
        try:
            asset = signal.get("asset")
            direction = signal.get("signal").upper()
            amount = config.get("amount")
            duration = signal.get("duration", 5)
            
            # Calcular expiração
            expiration = await self._calculate_expiration(duration)
            
            if Settings.LOG_LEVEL.upper() == "DEBUG":
                logger.info(f"[TRADE EXECUTOR] Executando trade para usuário {user_id}:")
                logger.info(f"[TRADE EXECUTOR]   - Ativo: {asset}")
                logger.info(f"[TRADE EXECUTOR]   - Direção: {direction}")
                logger.info(f"[TRADE EXECUTOR]   - Amount: ${amount}")
                logger.info(f"[TRADE EXECUTOR]   - Duração: {duration}s")
                logger.info(f"[TRADE EXECUTOR]   - Expiração: {expiration}")

            # Enviar ordem via WebSocket
            order_result = await self._send_order(user_id, asset, direction, amount, expiration)
            
            if not order_result.get("success"):
                logger.error(f"[TRADE EXECUTOR] Falha ao enviar ordem: {order_result.get('error')}")
                if user_id in self.active_trades:
                    del self.active_trades[user_id]
                return

            order_id = order_result.get("order_id")

            # Registrar trade ativo
            self.active_trades[user_id] = {
                "asset": asset,
                "direction": direction,
                "amount": amount,
                "duration": duration,
                "expiration": expiration,
                "order_id": order_id,
                "start_time": time.time(),
                "status": "pending"
            }

            # Iniciar monitoramento do trade
            asyncio.create_task(self._monitor_trade(user_id))

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao executar trade para usuário {user_id}: {e}")
            if user_id in self.active_trades:
                del self.active_trades[user_id]

    async def _calculate_expiration(self, duration: int) -> int:
        """Calcula timestamp de expiração"""
        current_time = int(time.time())
        expiration = current_time + duration
        return expiration

    async def _send_order(self, user_id: int, asset: str, direction: str, amount: float, expiration: int) -> Dict[str, Any]:
        """Envia ordem via WebSocket"""
        try:
            if not self.user_connection_manager:
                return {"success": False, "error": "UserConnectionManager não disponível"}

            # Obter TradingAPI do usuário
            if user_id not in self.user_connection_manager.trading_apis:
                return {"success": False, "error": "TradingAPI não disponível para o usuário"}

            trading_api = self.user_connection_manager.trading_apis[user_id]

            if Settings.LOG_LEVEL.upper() == "DEBUG":
                logger.info(f"[TRADE EXECUTOR] Enviando ordem via TradingAPI para usuário {user_id}")

            # Importar OrderDirection
            from models.trading import OrderDirection

            # Converter direction string para enum
            direction_enum = OrderDirection.CALL if direction.upper() == "CALL" else OrderDirection.PUT

            # Enviar ordem usando TradingAPI.place_order
            result = await trading_api.place_order(
                asset=asset,
                amount=amount,
                direction=direction_enum,
                duration=5  # 5 segundos
            )

            if result and result.status:
                # Usar o requestId gerado pela TradingAPI como order_id
                order_id = result.request_id if hasattr(result, 'request_id') else result.order_id
                logger.info(f"[TRADE EXECUTOR] Ordem enviada com sucesso para usuário {user_id}: {order_id}")
                return {"success": True, "order_id": order_id}
            else:
                error_msg = result.message if result else "Sem resposta"
                logger.error(f"[TRADE EXECUTOR] Erro ao enviar ordem: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao enviar ordem: {e}")
            return {"success": False, "error": str(e)}

    async def _monitor_trade(self, user_id: int):
        """Monitora o status do trade"""
        try:
            if user_id not in self.active_trades:
                return

            trade = self.active_trades[user_id]
            duration = trade.get("duration", 5)
            timeout = duration * self.trade_timeout_multiplier
            order_id = trade.get("order_id")

            if Settings.LOG_LEVEL.upper() == "DEBUG":
                logger.info(f"[TRADE EXECUTOR] Monitorando trade do usuário {user_id} (timeout: {timeout}s)")

            # A TradingAPI já captura os eventos de resultado via handlers
            # O TradeExecutor apenas verifica o dicionário _order_results

            # Verificar resultado periodicamente
            elapsed = 0
            check_interval = 0.5  # verificar a cada 0.5s
            
            while elapsed < timeout:
                await asyncio.sleep(check_interval)
                elapsed += check_interval

                # Verificar se o trade já foi finalizado pelo callback
                if user_id not in self.active_trades:
                    return

                # Obter TradingAPI do usuário para verificar resultados
                if user_id in self.user_connection_manager.trading_apis:
                    trading_api = self.user_connection_manager.trading_apis[user_id]
                    # Verificar resultado no dicionário de resultados da TradingAPI
                    if hasattr(trading_api, '_order_results') and order_id in trading_api._order_results:
                        result = trading_api._order_results[order_id]
                        # Verificar se o status é terminal (WIN, LOSS, CLOSED, TIMEOUT)
                        from models.trading import OrderStatus
                        status_str = result.status.value if hasattr(result.status, 'value') else str(result.status)
                        
                        # Status não-terminal: continuar aguardando
                        if status_str in [OrderStatus.PENDING.value, OrderStatus.OPEN.value]:
                            continue
                        
                        # Status terminal: trade finalizado
                        profit = result.profit if hasattr(result, 'profit') else None
                        await self._log_trade_result(user_id, status_str, profit)
                        del self.active_trades[user_id]
                        return

            # Timeout
            if user_id in self.active_trades:
                logger.warning(f"[TRADE EXECUTOR] Trade do usuário {user_id} atingiu timeout")
                await self._log_trade_result(user_id, "timeout", None)
                del self.active_trades[user_id]

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao monitorar trade do usuário {user_id}: {e}")
            if user_id in self.active_trades:
                del self.active_trades[user_id]

    async def _log_trade_result(self, user_id: int, result: str, profit: Optional[float]):
        """Loga resultado do trade"""
        try:
            # Não logar status "pending" - aguardar resultado real
            if result == "pending":
                return

            timestamp = datetime.now().isoformat()
            
            # Log no trading_manager.log
            logger.info(f"[TRADE RESULT] Usuário: {user_id} | Resultado: {result} | Profit: {profit} | Timestamp: {timestamp}")

            # Log no arquivo específico do usuário (em logs/trading/)
            # TODO: Obter email do usuário
            user_email = f"user_{user_id}"
            user_log_path = Path("logs/trading") / f"{user_email}.log"
            
            with open(user_log_path, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} | Resultado: {result} | Profit: {profit}\n")

        except Exception as e:
            logger.error(f"[TRADE EXECUTOR] Erro ao logar resultado do trade: {e}")
