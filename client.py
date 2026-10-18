"""PocketOption Client - Facade principal"""

from connection.websocket import WebSocketManager
from api.auth import AuthAPI
from api.balance import BalanceAPI
from api.trading import TradingAPI
from core.logger import get_logger, LoggerConfig
from config.settings import Settings

logger = get_logger(__name__)


class PocketOptionClient:
    """Cliente principal para PocketOption"""

    def __init__(self, ssid: str, is_demo: bool = True, region: str = None, log_level: str = None):
        self.ssid = ssid
        self.is_demo = is_demo
        self.region = region

        # Configurar logging
        if log_level:
            LoggerConfig.setup(level=getattr(__import__("logging"), log_level.upper()))
        else:
            LoggerConfig.setup(level=Settings.get_log_level())

        self.ws_manager = WebSocketManager(region=region if region else "DEMO")

        self.auth = AuthAPI(self.ws_manager, ssid)
        self.balance = BalanceAPI(self.ws_manager)
        self.trading = TradingAPI(self.ws_manager)

        logger.info(f"PocketOptionClient inicializado (region: {region if region else 'DEMO'})")


    async def connect(self) -> bool:
        """Conectar ao servidor"""
        logger.info("Iniciando conexão")
        return await self.ws_manager.connect(ssid=self.ssid)




    async def disconnect(self):
        """Desconectar do servidor"""
        logger.info("Desconectando")
        await self.ws_manager.disconnect()




    async def authenticate(self) -> bool:
        """Autenticar com SSID"""
        return await self.auth.authenticate()




    def is_authenticated(self) -> bool:
        """Verificar se está autenticado"""
        return self.auth.is_authenticated()




    async def get_balance(self):
        """Obter saldo atual"""
        return await self.balance.get_balance()


    async def place_order(self, asset: str, amount: float, direction, duration: int):
        """Colocar uma ordem"""
        return await self.trading.place_order(asset, amount, direction, duration)




    async def get_order_result(self, order_id: str):
        """Obter resultado de uma ordem específica"""
        return self.trading.get_order_result(order_id)




    async def close_order(self, order_id: str) -> bool:
        """Fechar uma ordem aberta"""
        return await self.trading.close_order(order_id)




    def get_open_orders(self) -> list:
        """Obter lista de ordens abertas"""
        return self.trading.get_open_orders()


    def get_current_price(self, asset: str):
        """Obter preço atual de um ativo"""
        return self.trading.get_current_price(asset)
