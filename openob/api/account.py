"""
Account API
"""

import asyncio
from typing import Optional
from openob.models.market import Balance
from datetime import datetime


class AccountAPI:
    """API de conta e saldo"""

    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
        self._balance: Optional[Balance] = None
        self._balance_updated = asyncio.Event()
        self._setup_handlers()

    def _setup_handlers(self):
        """Configurar handlers de eventos"""
        self.ws_manager.add_event_handler("balance", self._on_balance)
        self.ws_manager.add_event_handler("balance_updated", self._on_balance)
        self.ws_manager.add_event_handler("successupdateBalance", self._on_balance)
        self.ws_manager.add_event_handler("balance_data", self._on_balance)
        self.ws_manager.add_event_handler("json_data", self._on_json_data)

    async def _on_balance(self, data):
        """Handler para receber dados de saldo"""
        try:
            if isinstance(data, dict):
                amount = data.get("balance", 0)
                currency = data.get("currency", "USD")
                is_demo = data.get("isDemo", True)
                self._balance = Balance(amount=amount, currency=currency, is_demo=is_demo)
                self._balance_updated.set()
        except Exception as e:
            pass

    async def _on_json_data(self, data):
        """Handler para dados JSON"""
        try:
            if isinstance(data, dict) and "balance" in data:
                amount = data.get("balance", 0)
                currency = data.get("currency", "USD")
                is_demo = data.get("isDemo", True)
                self._balance = Balance(amount=amount, currency=currency, is_demo=is_demo)
                self._balance_updated.set()
        except Exception as e:
            pass

    async def get_balance(self) -> Balance:
        """Obter saldo atual"""
        if not self.ws_manager.is_connected:
            raise Exception("WebSocket não está conectado")

        try:
            # Solicitar saldo
            await self.ws_manager.send_message('42["balance/get"]')

            # Aguardar resposta (com timeout)
            try:
                await asyncio.wait_for(self._balance_updated.wait(), timeout=5.0)
                self._balance_updated.clear()
            except asyncio.TimeoutError:
                print("Timeout aguardando saldo - não foi possível obter dados")
                if not self._balance:
                    self._balance = Balance(amount=0, currency="USD", is_demo=True)
                raise

            return self._balance

        except Exception as e:
            print(f"Erro ao obter saldo: {e}")
            raise
