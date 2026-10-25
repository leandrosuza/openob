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
        self._running = False

    def set_monitor_api(self, monitor_api):
        """Injetar referência ao MonitorAPI"""
        self.monitor_api = monitor_api

    def set_user_connection_manager(self, user_connection_manager):
        """Injetar referência ao UserConnectionManager"""
        self.user_connection_manager = user_connection_manager

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

        # Atualizar cache de ticks
        self._update_tick_cache(asset, tick)

        # Verificar se o ativo está sendo monitorado
        monitored_assets = self.get_monitored_assets()
        if asset not in monitored_assets:
            return

        # Analisar ativo globalmente
        signal = await self.analyze_asset(asset)
        if signal and signal.get("signal") != "none":
            # Adicionar sinal à fila global
            self.signal_queue.append(signal)
            # Manter apenas últimos 50 sinais
            if len(self.signal_queue) > 50:
                self.signal_queue.pop(0)

            logger.debug(f"Sinal global gerado: {signal.get('signal')} para {asset}")

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
        ticks = self.get_cached_ticks(asset, parameters.get("lookback_period", 50))

        if not ticks or len(ticks) < parameters.get("lookback_period", 50):
            return None

        # Analisar com a estratégia
        signal = await self.global_strategy.analyze(ticks, parameters)

        return signal

    def get_cached_ticks(self, asset: str, limit: int) -> List[Dict]:
        """Obter ticks do cache ou repository"""
        if asset in self.tick_cache and len(self.tick_cache[asset]) >= limit:
            return list(self.tick_cache[asset])[-limit:]
        else:
            # Fallback para repository
            import asyncio
            try:
                ticks = asyncio.run(self.tick_repository.get_recent(asset, limit))
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

    def _update_tick_cache(self, asset: str, tick: Dict):
        """Atualizar cache de ticks para um ativo"""
        if asset not in self.tick_cache:
            self.tick_cache[asset] = deque(maxlen=self.tick_cache_size)

        self.tick_cache[asset].append(tick)

    async def analyze_asset(self, asset: str, user_id: int) -> Optional[Dict]:
        """Analisar ativo específico para um usuário"""
        strategy = self.strategies.get(user_id)
        config = self.user_configs.get(user_id)

        if not strategy or not config:
            return None

        # Obter ticks do cache ou repository
        ticks = self.get_cached_ticks(asset, config.parameters.get("lookback_period", 50))

        if not ticks or len(ticks) < config.parameters.get("lookback_period", 50):
            return None

        # Analisar com a estratégia
        signal = await strategy.analyze(ticks, config.parameters)

        logger.debug(f"Sinal gerado para usuário {user_id}, ativo {asset}: {signal}")
        return signal

    def get_cached_ticks(self, asset: str, limit: int) -> List[Dict]:
        """Obter ticks do cache ou repository"""
        if asset in self.tick_cache and len(self.tick_cache[asset]) >= limit:
            return list(self.tick_cache[asset])[-limit:]
        else:
            # Fallback para repository
            import asyncio
            try:
                ticks = asyncio.run(self.tick_repository.get_recent(asset, limit))
                return ticks
            except Exception as e:
                logger.error(f"Erro ao obter ticks do repository: {e}")
                return []

    def get_monitored_assets(self) -> Set[str]:
        """Obter ativos monitorados do MonitorAPI"""
        if self.monitor_api:
            return self.monitor_api.monitored_assets
        return set()

    def get_signals_for_user(self, user_id: int) -> List[Dict]:
        """Obter sinais priorizados por confiança para usuário"""
        signals = self.signal_queue.get(user_id, [])

        # Ordenar por confiança (decrescente)
        signals_sorted = sorted(signals, key=lambda x: x.get("confidence", 0), reverse=True)

        return signals_sorted

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
