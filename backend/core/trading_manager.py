"""TradingManager Global - Gerenciador de execução de trades"""

import asyncio
from typing import Dict, Optional
from models.trading import Order, OrderDirection
from core.logger import get_logger


logger = get_logger(__name__)


class TradingManager:
    """Gerenciador único global para trading de todos os usuários"""

    def __init__(self):
        self.active_trades: Dict[int, Dict] = {}  # trades em andamento por user_id
        self.user_connection_manager = None  # será injetado
        self.strategy_manager = None  # será injetado
        self._running = False

    def set_user_connection_manager(self, user_connection_manager):
        """Injetar referência ao UserConnectionManager"""
        self.user_connection_manager = user_connection_manager

    def set_strategy_manager(self, strategy_manager):
        """Injetar referência ao StrategyManager"""
        self.strategy_manager = strategy_manager

    async def start(self):
        """Iniciar TradingManager"""
        self._running = True
        logger.info("TradingManager iniciado")

    async def stop(self):
        """Parar TradingManager"""
        self._running = False
        logger.info("TradingManager parado")

    async def execute_trade(self, user_id: int, signal: Dict):
        """Executar trade baseado em sinal"""
        if not self._running:
            logger.warning(f"TradingManager não está rodando, ignorando trade para usuário {user_id}")
            return

        # Verificar se há trade em andamento
        if self.is_trade_in_progress(user_id):
            logger.debug(f"Trade em andamento para usuário {user_id}, aguardando finalização")
            return

        # Obter config do usuário
        if not self.strategy_manager:
            logger.error("StrategyManager não configurado")
            return

        config = self.strategy_manager.user_configs.get(user_id)
        if not config:
            logger.warning(f"Config não encontrada para usuário {user_id}")
            return

        # Criar ordem
        direction = OrderDirection.CALL if signal.get("signal") == "call" else OrderDirection.PUT
        duration = signal.get("duration", 5)
        amount = config.amount

        # Escolher melhor ativo com melhor pontuação
        asset = self.get_best_asset(user_id, [signal])
        if not asset:
            logger.warning(f"Nenhum ativo disponível para usuário {user_id}")
            return

        order = Order(
            asset=asset,
            amount=amount,
            direction=direction,
            duration=duration
        )

        logger.info(f"Executando trade para usuário {user_id}: {asset}, {direction}, ${amount}, {duration}s")

        # Enviar ordem
        await self.send_order(user_id, order)

        # Marcar trade como em andamento
        self.active_trades[user_id] = {
            "order_id": order.request_id,
            "asset": asset,
            "amount": amount,
            "direction": direction,
            "duration": duration,
            "started_at": asyncio.get_event_loop().time()
        }

    async def send_order(self, user_id: int, order: Order):
        """Enviar ordem via WebSocket do usuário (usar TradingAPI)"""
        if not self.user_connection_manager:
            logger.error("UserConnectionManager não configurado")
            return

        # Obter TradingAPI do usuário
        trading_api = self.user_connection_manager.trading_apis.get(user_id)
        if not trading_api:
            logger.warning(f"TradingAPI não encontrada para usuário {user_id}")
            return

        # Enviar ordem via TradingAPI
        try:
            result = await trading_api.place_order(
                asset=order.asset,
                amount=order.amount,
                direction=order.direction,
                duration=order.duration
            )
            logger.info(f"Ordem enviada para usuário {user_id}: {result.order_id}")
        except Exception as e:
            logger.error(f"Erro ao enviar ordem para usuário {user_id}: {e}")

    async def on_trade_result(self, user_id: int, result: Dict):
        """Processar resultado de trade via evento WebSocket"""
        if user_id not in self.active_trades:
            return

        logger.info(f"Trade finalizado para usuário {user_id}: {result}")

        # Remover trade da lista de ativos
        del self.active_trades[user_id]

    async def on_balance_update(self, user_id: int, balance: Dict):
        """Processar atualização de saldo via evento WebSocket"""
        logger.debug(f"Saldo atualizado para usuário {user_id}: {balance}")

    def is_trade_in_progress(self, user_id: int) -> bool:
        """Verificar se há trade em andamento para usuário"""
        return user_id in self.active_trades

    def get_best_signal(self, user_id: int, signals: list) -> Optional[Dict]:
        """Escolher sinal com maior confiança"""
        if not signals:
            return None

        # Ordenar por confiança (decrescente)
        signals_sorted = sorted(signals, key=lambda x: x.get("confidence", 0), reverse=True)
        return signals_sorted[0]

    def get_best_asset(self, user_id: int, signals: list) -> Optional[str]:
        """Escolher ativo com melhor pontuação"""
        if not signals or not self.strategy_manager:
            return None

        # Obter sinais com confiança > 0
        valid_signals = [s for s in signals if s.get("confidence", 0) > 0]
        if not valid_signals:
            return None

        # Calcular pontuação média dos ativos monitorados
        monitored_assets = self.strategy_manager.get_monitored_assets()
        if not monitored_assets:
            return None

        # Calcular pontuação de cada ativo
        asset_scores = {}
        for asset in monitored_assets:
            score = self.strategy_manager.calculate_asset_score(asset)
            asset_scores[asset] = score

        # Calcular média
        if not asset_scores:
            return None

        avg_score = sum(asset_scores.values()) / len(asset_scores)

        # Filtrar ativos acima da média
        good_assets = [asset for asset, score in asset_scores.items() if score > avg_score]

        if not good_assets:
            # Se nenhum acima da média, usar o melhor
            best_asset = max(asset_scores, key=asset_scores.get)
            return best_asset

        # Escolher o melhor entre os bons
        best_asset = max(good_assets, key=lambda x: asset_scores[x])
        return best_asset

    async def await_trade_completion(self, user_id: int):
        """Aguardar evento de finalização de trade"""
        while self.is_trade_in_progress(user_id):
            await asyncio.sleep(0.5)
