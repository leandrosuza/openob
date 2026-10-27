"""StrategyManager Global - Gerenciador de estratégias de trading"""

import asyncio
from typing import Dict, List, Optional, Set
from collections import deque
from core.strategy import BaseStrategy
from core.strategy.scalping5s import Scalping5sStrategy
from models.autotrade import AutotradeConfig
from core.logger import get_logger


logger = get_logger(__name__)


class StrategyManager:
    """Gerenciador único global para todas as estratégias"""

    def __init__(self, tick_repository, tick_cache_size: int = 1000):
        self.global_strategy: Optional[BaseStrategy] = None  # estratégia global
        self.tick_cache: Dict[str, deque] = {}  # cache de ticks por ativo
        self.tick_repository = tick_repository
        self.tick_cache_size = tick_cache_size
        self.signal_queue: List[Dict] = []  # sinais globais
        self.monitor_api = None  # será injetado
        self.user_connection_manager = None  # será injetado
        self.trade_executor = None  # será injetado
        self._running = False
        self.monitored_assets: Set[str] = set()  # ativos sendo monitorados atualmente
        from core.logger import LoggerConfig
        self.signal_logger = LoggerConfig.get_strategy_logger()  # logger para sinais finais

    def set_monitor_api(self, monitor_api):
        """Injetar referência ao MonitorAPI"""
        self.monitor_api = monitor_api

    def set_user_connection_manager(self, user_connection_manager):
        """Injetar referência ao UserConnectionManager"""
        self.user_connection_manager = user_connection_manager

    def set_trade_executor(self, trade_executor):
        """Injetar referência ao TradeExecutor"""
        self.trade_executor = trade_executor

    async def start(self):
        """Iniciar monitoramento de ticks"""
        self._running = True
        # Carregar estratégia global (scalping5s como padrão)
        self.global_strategy = Scalping5sStrategy()
        logger.info("StrategyManager iniciado com estratégia global scalping5s")

    async def stop(self):
        """Parar monitoramento"""
        self._running = False
        logger.info("StrategyManager parado")

    async def on_tick(self, tick: Dict):
        """Processar novo tick (chamado pelo MonitorAPI)"""
        if not self._running or not self.global_strategy:
            return

        asset = tick.get("asset")
        if not asset:
            return

        # Obter payout do tick
        payout = tick.get("payout", 0)

        # Atualizar rastreamento de ativos monitorados
        current_monitored = self.get_monitored_assets()
        if current_monitored != self.monitored_assets:
            logger.info(f"Ativos monitorados alterados: {self.monitored_assets} -> {current_monitored}")
            # Limpar cache de ativos que não estão mais sendo monitorados
            for old_asset in self.monitored_assets - current_monitored:
                if old_asset in self.tick_cache:
                    del self.tick_cache[old_asset]
                    logger.info(f"Cache limpo para ativo removido: {old_asset}")
            self.monitored_assets = current_monitored

        # Atualizar cache de ticks
        self._update_tick_cache(asset, tick)

        # Analisar ativo globalmente (sempre analisa todos os ativos monitorados)
        signal = await self.analyze_asset(asset)
        if signal and signal.get("signal") != "none":
            # Adicionar payout ao sinal
            signal["payout"] = payout
            
            # Adicionar sinal à fila global
            self.signal_queue.append(signal)
            # Manter apenas últimos 50 sinais
            if len(self.signal_queue) > 50:
                self.signal_queue.pop(0)

            # Logar sinal final no strategy.log
            self.signal_logger.info(
                f"SINAL FINAL | Estratégia: {self.global_strategy.get_name()} | "
                f"Ativo: {asset} | Direção: {signal.get('signal').upper()} | "
                f"Confiança: {signal.get('confidence', 0):.2f} | "
                f"Timestamp: {signal.get('timestamp')} | "
                f"Parâmetros: {signal.get('parameters', {})}"
            )

            # Notificar TradeExecutor para processar o sinal
            if self.trade_executor:
                asyncio.create_task(self.trade_executor.process_signal(signal))

    def _update_tick_cache(self, asset: str, tick: Dict):
        """Atualizar cache de ticks para um ativo"""
        if asset not in self.tick_cache:
            self.tick_cache[asset] = deque(maxlen=self.tick_cache_size)

        self.tick_cache[asset].append(tick)

    async def analyze_asset(self, asset: str) -> Optional[Dict]:
        """Analisar ativo específico com a estratégia global"""
        if not self.global_strategy:
            return None

        # Parâmetros padrão da estratégia
        parameters = {
            "lookback_period": 50,
            "ma_period": 20,
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        }

        # Obter ticks do cache ou repository
        ticks = await self.get_cached_ticks(asset, parameters.get("lookback_period", 50))

        if not ticks or len(ticks) < parameters.get("lookback_period", 50):
            logger.info(f"Ticks insuficientes para {asset}: {len(ticks) if ticks else 0} < {parameters.get('lookback_period', 50)}")
            return None

        logger.info(f"Analisando {asset} com {len(ticks)} ticks")

        # Analisar com a estratégia
        signal = await self.global_strategy.analyze(ticks, parameters)

        # Adicionar metadados ao sinal
        if signal:
            signal["asset"] = asset
            # Usar timestamp do último tick ou timestamp atual
            from datetime import datetime
            signal["timestamp"] = ticks[-1].get("timestamp") if ticks else datetime.now().isoformat()
            signal["parameters"] = parameters
            signal["strategy_name"] = self.global_strategy.get_name()

        return signal

    async def get_cached_ticks(self, asset: str, limit: int) -> List[Dict]:
        """Obter ticks do cache ou repository"""
        if asset in self.tick_cache and len(self.tick_cache[asset]) >= limit:
            return list(self.tick_cache[asset])[-limit:]
        else:
            # Fallback para repository
            try:
                ticks = await self.tick_repository.get_recent(asset, limit)
                return ticks
            except Exception as e:
                logger.error(f"Erro ao obter ticks do repository: {e}")
                return []

    def get_monitored_assets(self) -> Set[str]:
        """Obter ativos monitorados do MonitorAPI"""
        if self.monitor_api:
            return self.monitor_api.monitored_assets
        return set()

    def get_signals(self) -> List[Dict]:
        """Obter sinais globais"""
        return self.signal_queue.copy()

    def calculate_asset_score(self, asset: str) -> float:
        """Calcular pontuação do ativo baseada em amplitude de preço"""
        if asset not in self.tick_cache or len(self.tick_cache[asset]) < 50:
            return 0.0

        ticks = list(self.tick_cache[asset])[-50:]
        prices = [float(tick.get("price", 0)) for tick in ticks if tick.get("price")]

        if len(prices) < 2:
            return 0.0

        # Calcular amplitude (max - min)
        amplitude = max(prices) - min(prices)

        return amplitude
