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
        self.strategies: Dict[int, BaseStrategy] = {}  # estratégias por user_id
        self.user_configs: Dict[int, AutotradeConfig] = {}  # configs por usuário
        self.tick_cache: Dict[str, deque] = {}  # cache de ticks por ativo
        self.tick_repository = tick_repository
        self.tick_cache_size = tick_cache_size
        self.signal_queue: Dict[int, List[Dict]] = {}  # sinais por usuário
        self.monitor_api = None  # será injetado
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
        logger.info("StrategyManager iniciado")

    async def stop(self):
        """Parar monitoramento"""
        self._running = False
        logger.info("StrategyManager parado")

    async def apply_config(self, user_id: int, config: AutotradeConfig):
        """Aplicar config de autotrade para usuário"""
        self.user_configs[user_id] = config

        # Carregar estratégia baseada em strategy_name
        if config.strategy_name == "scalping5s":
            self.strategies[user_id] = Scalping5sStrategy()
            logger.info(f"Estratégia scalping5s carregada para usuário {user_id}")
        else:
            logger.warning(f"Estratégia desconhecida: {config.strategy_name}")
            return

        # Inicializar fila de sinais
        self.signal_queue[user_id] = []

    async def remove_config(self, user_id: int):
        """Remover config de autotrade do usuário"""
        if user_id in self.strategies:
            del self.strategies[user_id]
        if user_id in self.user_configs:
            del self.user_configs[user_id]
        if user_id in self.signal_queue:
            del self.signal_queue[user_id]
        logger.info(f"Config removida para usuário {user_id}")

    async def on_tick(self, tick: Dict):
        """Processar novo tick (chamado pelo MonitorAPI)"""
        if not self._running:
            return

        asset = tick.get("asset")
        if not asset:
            return

        # Atualizar cache de ticks
        self._update_tick_cache(asset, tick)

        # Analisar ativo para todos os usuários com estratégias
        for user_id, strategy in self.strategies.items():
            config = self.user_configs.get(user_id)
            if not config:
                continue

            # Verificar se o ativo está sendo monitorado
            monitored_assets = self.get_monitored_assets()
            if asset not in monitored_assets:
                continue

            # Analisar ativo (sempre analisa, mesmo se is_active=False)
            signal = await self.analyze_asset(asset, user_id)

            # Se autotrade ativo, adicionar sinal à fila
            if config.is_active and signal and signal.get("signal") != "none":
                if user_id not in self.signal_queue:
                    self.signal_queue[user_id] = []
                self.signal_queue[user_id].append(signal)
                # Manter apenas últimos 10 sinais
                if len(self.signal_queue[user_id]) > 10:
                    self.signal_queue[user_id].pop(0)

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
