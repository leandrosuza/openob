"""
PocketOption Client - Facade principal
"""

import asyncio
from openob.connection.websocket import WebSocketManager
from openob.api.auth import AuthAPI
from openob.api.account import AccountAPI
from openob.api.market import MarketAPI
from openob.api.trading import TradingAPI
from openob.core.constants import REGIONS


class PocketOptionClient:
    """Cliente principal para PocketOption"""

    def __init__(self, ssid: str, is_demo: bool = True, region: str = None):
        self.ssid = ssid
        self.is_demo = is_demo
        self.region = region

        # WebSocket Manager
        self.ws_manager = WebSocketManager(region=region if region else "DEMO")

        # APIs
        self.auth = AuthAPI(self.ws_manager, ssid)
        self.account = AccountAPI(self.ws_manager)
        self.market = MarketAPI(self.ws_manager)
        self.trading = TradingAPI(self.ws_manager)

    async def connect(self) -> bool:
        """Conectar ao servidor"""
        return await self.ws_manager.connect(ssid=self.ssid)

    async def disconnect(self):
        """Desconectar do servidor"""
        await self.ws_manager.disconnect()

    async def get_balance(self):
        """Obter saldo atual"""
        return await self.account.get_balance()

    async def get_candles(self, asset: str, timeframe: str, count: int = 100):
        """Obter candles históricos"""
        return await self.market.get_candles(asset, timeframe, count)

    async def place_order(self, asset: str, amount: float, direction, duration: int):
        """Colocar uma ordem"""
        return await self.trading.place_order(asset, amount, direction, duration)
