"""Balance API"""

import asyncio
from typing import Optional
from models.market import Balance
from core.logger import get_logger
from core.exceptions import ConnectionError as OpenOBConnectionError


logger = get_logger(__name__)


class BalanceAPI:
    """API de saldo"""

    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
        self._balance: Optional[Balance] = None
        self._balance_updated = asyncio.Event()
        self._setup_handlers()


    def _setup_handlers(self):
        """Configurar handlers de eventos"""
        handlers = {
            "balance": self._on_balance,
            "balance_updated": self._on_balance,
            "successupdateBalance": self._on_balance,
            "balance_data": self._on_balance,
            "json_data": self._on_json_data,
        }
        for event, handler in handlers.items():
            self.ws_manager.add_event_handler(event, handler)


    def _parse_balance_data(self, data: dict) -> Optional[Balance]:
        """Parse dados de saldo de um dict"""
        try:
            amount = data.get("balance", 0)
            currency = data.get("currency", "USD")
            is_demo = data.get("isDemo", True)
            return Balance(amount=amount, currency=currency, is_demo=is_demo)
        except Exception as e:
            logger.error(f"Erro ao parsear dados de saldo: {e}")
            return None


    async def _on_balance(self, data):
        """Handler para receber dados de saldo"""
        if isinstance(data, dict):
            balance = self._parse_balance_data(data)
            if balance:
                self._balance = balance
                self._balance_updated.set()
                logger.debug(f"Saldo atualizado: {balance.amount} {balance.currency}")


    async def _on_json_data(self, data):
        """Handler para dados JSON"""
        if isinstance(data, dict) and "balance" in data:
            balance = self._parse_balance_data(data)
            if balance:
                self._balance = balance
                self._balance_updated.set()
                logger.debug(f"Saldo atualizado via JSON: {balance.amount} {balance.currency}")


    async def get_balance(self) -> Balance:
        """Obter saldo atual"""
        if not self.ws_manager.is_connected:
            raise OpenOBConnectionError("WebSocket não está conectado")

        try:
            logger.info("Solicitando saldo")
            await self.ws_manager.send_message('42["balance/get"]')

            try:
                await asyncio.wait_for(self._balance_updated.wait(), timeout=5.0)
                self._balance_updated.clear()
                if self._balance:
                    logger.info(f"Saldo obtido: {self._balance.amount} {self._balance.currency}")
                    return self._balance
                else:
                    raise OpenOBConnectionError("Não foi possível obter saldo")
            except asyncio.TimeoutError:
                logger.warning("Timeout aguardando saldo")
                raise OpenOBConnectionError("Timeout ao obter saldo")

        except OpenOBConnectionError:
            raise
        except Exception as e:
            logger.error(f"Erro ao obter saldo: {e}")
            raise OpenOBConnectionError(f"Falha ao obter saldo: {e}")
