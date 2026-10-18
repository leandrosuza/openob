"""Trading API"""

import asyncio
from typing import Optional
from models.trading import OrderDirection, OrderResult, OrderStatus, Order
from core.constants import ASSETS, API_LIMITS
from core.logger import get_logger
from core.exceptions import ValidationError, TradingError, ConnectionError as OpenOBConnectionError


logger = get_logger(__name__)


class TradingAPI:
    """API de trading e ordens"""

    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
        self._order_results: dict = {}
        self._current_prices: dict = {}
        self._setup_handlers()


    def _setup_handlers(self):
        """Configurar handlers de eventos"""
        handlers = {
            "order": self._on_order,
            "order-placed": self._on_order,
            "order-won": self._on_order_result,
            "order-lost": self._on_order_result,
            "buy": self._on_order,
            "successbuy": self._on_order,
            "openOrder": self._on_order,
            "successopenOrder": self._on_success_open_order,
            "closeOrder": self._on_order,
            "successcloseOrder": self._on_success_close_order,
            "json_data": self._on_json_data,
            "order_opened": self._on_order,
            "order_closed": self._on_order,
            "stream_update": self._on_stream_update,
        }
        for event, handler in handlers.items():
            self.ws_manager.add_event_handler(event, handler)


    def _get_order_id(self, data: dict) -> Optional[str]:
        """Extrair order_id de dados"""
        return data.get("id") or data.get("requestId") or data.get("order_id")


    def _determine_order_status(self, profit: float) -> OrderStatus:
        """Determinar status da ordem baseado no profit"""
        if profit > 0:
            return OrderStatus.WIN
        elif profit < 0:
            return OrderStatus.LOSS
        return OrderStatus.CLOSED


    def _update_order_status(self, order_id: str, status: OrderStatus, profit: float = 0, message: str = ""):
        """Atualizar status de ordem por ID"""
        if order_id in self._order_results:
            self._order_results[order_id] = OrderResult(
                order_id=order_id,
                status=status,
                profit=profit,
                message=message
            )
            logger.info(f"Ordem {order_id}: {status.value} ({message})")


    async def _on_order(self, data):
        """Handler genérico para ordem (colocada/aberta/processada)"""
        if not isinstance(data, dict):
            return

        order_id = self._get_order_id(data)
        if order_id:
            self._update_order_status(order_id, OrderStatus.OPEN, 0, "Ordem processada")


    async def _on_order_result(self, data):
        """Handler para resultado de ordem (won/lost)"""
        if not isinstance(data, dict):
            return

        order_id = self._get_order_id(data)
        profit = data.get("profit", 0)
        if order_id:
            status = self._determine_order_status(profit)
            self._update_order_status(order_id, status, profit, f"Ordem {status.value}: ${profit}")


    async def _on_success_open_order(self, data):
        """Handler para ordem aberta com sucesso - atualizar ID se necessário"""
        if not isinstance(data, dict):
            return

        new_id = data.get("id")
        if new_id:
            logger.debug(f"Ordem aberta com ID: {new_id}")


    def _parse_order_result(self, data: dict) -> Optional[OrderResult]:
        """Parse resultado de ordem de dados"""
        profit = data.get("profit", 0)
        deals = data.get("deals", [])

        if not (deals and isinstance(deals, list) and len(deals) > 0):
            return None

        deal = deals[0]
        deal_id = deal.get("id")
        deal_profit = deal.get("profit", profit)
        status = self._determine_order_status(deal_profit)

        logger.info(f"Resultado: {status.value} | Profit: ${deal_profit}")

        return OrderResult(
            order_id=deal_id,
            status=status,
            profit=deal_profit,
            message=f"Ordem fechada: {status.value}"
        )


    async def _on_success_close_order(self, data):
        """Handler para ordem fechada com sucesso"""
        if not isinstance(data, dict):
            return

        result = self._parse_order_result(data)
        if result:
            self._order_results[result.order_id] = result


    async def _on_json_data(self, data):
        """Handler para dados JSON - parsing de resultado de ordem"""
        if not isinstance(data, dict):
            return

        if "profit" not in data or "deals" not in data:
            return

        result = self._parse_order_result(data)
        if result:
            self._order_results[result.order_id] = result


    async def _on_stream_update(self, data):
        """Handler para atualização de stream de preços"""
        if not isinstance(data, dict):
            return

        asset = data.get("asset")
        price = data.get("price") or data.get("close")
        if asset and price:
            self._current_prices[asset] = float(price)
            logger.debug(f"Preço atualizado {asset}: {price}")


    async def place_order(self, asset: str, amount: float, direction: OrderDirection, duration: int) -> OrderResult:
        """Colocar uma ordem de trading"""
        if not self.ws_manager.is_connected:
            raise OpenOBConnectionError("WebSocket não está conectado")

        self._validate_order_parameters(asset, amount, direction, duration)

        order = Order(
            asset=asset,
            amount=amount,
            direction=direction,
            duration=duration
        )

        direction_value = "call" if direction == OrderDirection.CALL else "put"
        order_message = self._format_order_message(
            asset=asset,
            amount=amount,
            direction=direction_value,
            duration=duration,
            request_id=order.request_id,
        )

        logger.info(f"Enviando ordem: {asset}, {amount}, {direction}, {duration}s")

        await self.ws_manager.send_message(order_message)

        result = OrderResult(
            order_id=order.request_id,
            status=OrderStatus.PENDING,
            profit=0,
            message="Ordem enviada"
        )

        self._order_results[order.request_id] = result

        return result


    def _validate_order_parameters(self, asset: str, amount: float, direction: OrderDirection, duration: int):
        """Validar parâmetros da ordem"""
        if asset not in ASSETS:
            raise ValidationError(f"Ativo inválido: {asset}")

        if amount < API_LIMITS["min_order_amount"] or amount > API_LIMITS["max_order_amount"]:
            raise ValidationError(f"Valor da ordem deve estar entre {API_LIMITS['min_order_amount']} e {API_LIMITS['max_order_amount']}")

        if duration < API_LIMITS["min_duration"] or duration > API_LIMITS["max_duration"]:
            raise ValidationError(f"Duração deve estar entre {API_LIMITS['min_duration']} e {API_LIMITS['max_duration']} segundos")


    def _format_order_message(self, asset: str, amount: float, direction: str, duration: int, request_id: str) -> str:
        """Formatar mensagem de ordem para WebSocket - formato openOrder"""
        return f'42["openOrder",{{"asset":"{asset}","amount":{amount},"action":"{direction}","isDemo":1,"requestId":"{request_id}","optionType":100,"time":{duration}}}]'


    def get_order_result(self, order_id: str) -> Optional[OrderResult]:
        """Obter resultado de uma ordem pelo ID"""
        return self._order_results.get(order_id)


    async def close_order(self, order_id: str) -> bool:
        """Fechar uma ordem aberta"""
        if not self.ws_manager.is_connected:
            raise OpenOBConnectionError("WebSocket não está conectado")

        message = f'42["closeOrder",{{"id":"{order_id}"}}]'
        await self.ws_manager.send_message(message)
        logger.info(f"Solicitação de fechamento enviada para ordem {order_id}")
        return True


    def get_open_orders(self) -> list:
        """Obter lista de ordens abertas"""
        return [
            result for result in self._order_results.values()
            if result.status in [OrderStatus.PENDING, OrderStatus.OPEN]
        ]


    def get_current_price(self, asset: str) -> Optional[float]:
        """Obter preço atual de um ativo"""
        return self._current_prices.get(asset)
