"""
PocketOption Client - Facade principal
"""

import asyncio
from openob.connection.websocket import WebSocketManager
from openob.api.auth import AuthAPI
from openob.api.balance import BalanceAPI
from openob.api.market import MarketAPI
from openob.api.trading import TradingAPI
from openob.core.constants import REGIONS


class PocketOptionClient:
    """Cliente principal para PocketOption"""

    def __init__(self, ssid: str, is_demo: bool = True, region: str = None):
        self.ssid = ssid
        self.is_demo = is_demo
        self.region = region

        self.ws_manager = WebSocketManager(region=region if region else "DEMO")

        self.auth = AuthAPI(self.ws_manager, ssid)
        self.balance = BalanceAPI(self.ws_manager)
        self.market = MarketAPI(self.ws_manager)
        self.trading = TradingAPI(self.ws_manager)





    async def connect(self) -> bool:
        """Conectar ao servidor"""
        return await self.ws_manager.connect(ssid=self.ssid)





    async def disconnect(self):
        """Desconectar do servidor"""
        await self.ws_manager.disconnect()





    async def reconnect(self) -> bool:
        """Reconectar ao servidor"""
        return await self.ws_manager.reconnect(ssid=self.ssid)





    async def get_balance(self):
        """Obter saldo atual"""
        return await self.balance.get_balance()





    async def get_candles(self, asset: str, timeframe: str, count: int = 100):
        """Obter candles históricos"""
        return await self.market.get_candles(asset, timeframe, count)





    async def place_order(self, asset: str, amount: float, direction, duration: int):
        """Colocar uma ordem"""
        return await self.trading.place_order(asset, amount, direction, duration)





    async def authenticate(self) -> bool:
        """Autenticar com SSID"""
        return await self.auth.authenticate()





    def is_authenticated(self) -> bool:
        """Verificar se está autenticado"""
        return self.auth.is_authenticated()





    async def get_order_result(self, order_id: str):
        """Obter resultado de uma ordem específica"""
        return self.trading.get_order_result(order_id)





    async def close_order(self, order_id: str) -> bool:
        """Fechar uma ordem aberta"""
        return await self.trading.close_order(order_id)





    def get_open_orders(self) -> list:
        """Obter lista de ordens abertas"""
        return self.trading.get_open_orders()





    def get_available_assets(self) -> dict:
        """Obter lista de ativos disponíveis"""
        return self.market.get_available_assets()





    def get_available_timeframes(self) -> dict:
        """Obter lista de timeframes disponíveis"""
        return self.market.get_available_timeframes()





    def get_current_price(self, asset: str):
        """Obter preço atual de um ativo"""
        return self.trading.get_current_price(asset)
