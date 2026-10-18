"""Trading API"""

import uuid
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
        self._order_id_mapping: dict = {}
        self._current_prices: dict = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """Configurar handlers de eventos"""
        handlers = {
            "order": self._on_order,
            "order-placed": self._on_order_placed,
            "order-won": self._on_order_won,
            "order-lost": self._on_order_lost,
            "buy": self._on_buy,
            "successbuy": self._on_success_buy,
            "openOrder": self._on_open_order,
            "successopenOrder": self._on_success_open_order,
            "closeOrder": self._on_close_order,
            "successcloseOrder": self._on_success_close_order,
            "json_data": self._on_json_data,
            "order_opened": self._on_order_opened,
            "order_closed": self._on_order_closed,
            "stream_update": self._on_stream_update,
        }
        for event, handler in handlers.items():
            self.ws_manager.add_event_handler(event, handler)

    def _update_order_status(self, order_id: str, status: OrderStatus, profit: float = 0, message: str = ""):
        """Helper para atualizar status de ordem"""
        for local_id, result in list(self._order_results.items()):
            if result.status in [OrderStatus.PENDING, OrderStatus.OPEN]:
                self._order_results[local_id] = OrderResult(
                    order_id=local_id,
                    status=status,
                    profit=profit,
                    message=message
                )
                logger.info(f"Ordem {local_id}: {status.value} ({message})")
                return local_id
        return None

    async def _on_order(self, data):
        """Handler para ordem"""
        try:
            if isinstance(data, dict):
                order_id = data.get("id") or data.get("requestId")
                status = data.get("status")
                if order_id and status:
                    self._update_order_status(order_id, OrderStatus.OPEN, 0, f"Ordem atualizada: {status}")
        except Exception as e:
            logger.error(f"Erro ao processar ordem: {e}")

    async def _on_order_placed(self, data):
        """Handler para ordem colocada"""
        try:
            if isinstance(data, dict):
                order_id = data.get("id") or data.get("requestId")
                if order_id:
                    self._update_order_status(order_id, OrderStatus.OPEN, 0, "Ordem colocada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao processar ordem colocada: {e}")

    async def _on_order_won(self, data):
        """Handler para ordem ganha"""
        try:
            if isinstance(data, dict):
                order_id = data.get("id") or data.get("order_id")
                profit = data.get("profit", 0)
                if order_id:
                    self._update_order_status(order_id, OrderStatus.WIN, profit, f"Ordem ganha: ${profit}")
        except Exception as e:
            logger.error(f"Erro ao processar ordem ganha: {e}")

    async def _on_order_lost(self, data):
        """Handler para ordem perdida"""
        try:
            if isinstance(data, dict):
                order_id = data.get("id") or data.get("order_id")
                profit = data.get("profit", 0)
                if order_id:
                    self._update_order_status(order_id, OrderStatus.LOSS, profit, f"Ordem perdida: ${profit}")
        except Exception as e:
            logger.error(f"Erro ao processar ordem perdida: {e}")

    async def _on_buy(self, data):
        """Handler para resposta de compra"""
        try:
            if isinstance(data, dict):
                order_id = data.get("id") or data.get("requestId")
                if order_id:
                    self._update_order_status(order_id, OrderStatus.OPEN, 0, "Ordem de compra processada")
        except Exception as e:
            logger.error(f"Erro ao processar compra: {e}")

    async def _on_success_buy(self, data):
        """Handler para compra bem-sucedida"""
        try:
            if isinstance(data, dict):
                order_id = data.get("id") or data.get("requestId")
                if order_id:
                    self._update_order_status(order_id, OrderStatus.OPEN, 0, "Compra realizada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao processar sucesso da compra: {e}")

    async def _on_open_order(self, data):
        """Handler para ordem aberta"""
        try:
            if isinstance(data, dict):
                order_id = data.get("id") or data.get("requestId")
                if order_id:
                    self._update_order_status(order_id, OrderStatus.OPEN, 0, "Ordem aberta no mercado")
        except Exception as e:
            logger.error(f"Erro ao processar ordem aberta: {e}")

    async def _on_success_open_order(self, data):
        """Handler para ordem aberta com sucesso - armazenar ID do servidor"""
        try:
            if isinstance(data, dict):
                server_order_id = data.get("id")
                if server_order_id:
                    for local_id, result in list(self._order_results.items()):
                        if result.status == OrderStatus.PENDING:
                            self._order_id_mapping[local_id] = server_order_id
                            self._order_id_mapping[server_order_id] = local_id
                            logger.debug(f"Ordem mapeada: {local_id} -> {server_order_id}")
                            break
        except Exception as e:
            logger.error(f"Erro em handler: {e}")

    async def _on_close_order(self, data):
        """Handler para ordem fechada"""
        try:
            if isinstance(data, dict):
                order_id = data.get("id") or data.get("requestId")
                if order_id:
                    self._update_order_status(order_id, OrderStatus.CLOSED, 0, "Ordem fechada")
        except Exception as e:
            logger.error(f"Erro ao processar ordem fechada: {e}")

    async def _on_success_close_order(self, data):
        """Handler para ordem fechada com sucesso - parsing de WIN/LOSS"""
        try:
            if isinstance(data, dict):
                profit = data.get("profit", 0)
                deals = data.get("deals", [])

                if deals and isinstance(deals, list) and len(deals) > 0:
                    deal = deals[0]
                    deal_id = deal.get("id")
                    deal_profit = deal.get("profit", profit)

                    if deal_profit > 0:
                        status = OrderStatus.WIN
                    elif deal_profit < 0:
                        status = OrderStatus.LOSS
                    else:
                        status = OrderStatus.CLOSED

                    logger.info(f"Resultado: {status.value} | Profit: ${deal_profit}")

                    for order_id, result in self._order_results.items():
                        if result.status == OrderStatus.PENDING:
                            self._order_results[order_id] = OrderResult(
                                order_id=order_id,
                                status=status,
                                profit=deal_profit,
                                message=f"Ordem fechada: {status.value}"
                            )
                            break

        except Exception as e:
            logger.error(f"Erro em handler: {e}")

    async def _on_json_data(self, data):
        """Handler para dados JSON - parsing de resultado de ordem"""
        try:
            if isinstance(data, dict):
                if "profit" in data and "deals" in data:
                    profit = data.get("profit", 0)
                    deals = data.get("deals", [])

                    if deals and isinstance(deals, list) and len(deals) > 0:
                        deal = deals[0]
                        deal_id = deal.get("id")
                        deal_profit = deal.get("profit", profit)

                        if deal_profit > 0:
                            status = OrderStatus.WIN
                        elif deal_profit < 0:
                            status = OrderStatus.LOSS
                        else:
                            status = OrderStatus.CLOSED

                        logger.info(f"Resultado (JSON): {status.value} | Profit: ${deal_profit}")

                        updated_result = OrderResult(
                            order_id=deal_id,
                            status=status,
                            profit=deal_profit,
                            message=f"Ordem fechada: {status.value}"
                        )

                        self._order_results[deal_id] = updated_result

                        for local_id, result in list(self._order_results.items()):
                            if result.status == OrderStatus.PENDING and local_id != deal_id:
                                self._order_results[local_id] = updated_result
                                logger.info(f"Ordem local {local_id} atualizada: {status.value} (${deal_profit})")
                                break

        except Exception as e:
            logger.error(f"Erro ao processar JSON: {e}")
            import traceback
            traceback.print_exc()

    async def _on_order_opened(self, data):
        """Handler para ordem aberta"""
        try:
            logger.debug(f"Ordem aberta (event): {data}")
        except Exception as e:
            logger.error(f"Erro ao processar ordem aberta: {e}")

    async def _on_order_closed(self, data):
        """Handler para ordem fechada"""
        try:
            logger.debug(f"Ordem fechada (event): {data}")
        except Exception as e:
            logger.error(f"Erro ao processar ordem fechada: {e}")

    async def _on_stream_update(self, data):
        """Handler para atualização de stream de preços"""
        try:
            if isinstance(data, dict):
                asset = data.get("asset")
                price = data.get("price") or data.get("close")
                order_id = data.get("order_id") or data.get("id")
                if asset and price:
                    self._current_prices[asset] = float(price)
                    logger.debug(f"Preço atualizado {asset}: {price}")
        except Exception as e:
            pass

    async def place_order(self, asset: str, amount: float, direction: OrderDirection, duration: int) -> OrderResult:
        """Colocar uma ordem de trading"""
        if not self.ws_manager.is_connected:
            raise OpenOBConnectionError("WebSocket não está conectado")

        self._validate_order_parameters(asset, amount, direction, duration)

        try:
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

        except (ValidationError, OpenOBConnectionError):
            raise
        except Exception as e:
            logger.error(f"Erro ao colocar ordem: {e}")
            raise TradingError(f"Falha ao colocar ordem: {e}")

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
        message = f'42["openOrder",{{"asset":"{asset}","amount":{amount},"action":"{direction}","isDemo":1,"requestId":"{request_id}","optionType":100,"time":{duration}}}]'
        return message

    def get_order_result(self, order_id: str) -> Optional[OrderResult]:
        """Obter resultado de uma ordem pelo ID"""
        return self._order_results.get(order_id)

    async def close_order(self, order_id: str) -> bool:
        """Fechar uma ordem aberta"""
        if not self.ws_manager.is_connected:
            raise OpenOBConnectionError("WebSocket não está conectado")

        try:
            message = f'42["closeOrder",{{"id":"{order_id}"}}]'
            await self.ws_manager.send_message(message)
            logger.info(f"Solicitação de fechamento enviada para ordem {order_id}")
            return True
        except OpenOBConnectionError:
            raise
        except Exception as e:
            logger.error(f"Erro ao fechar ordem: {e}")
            raise TradingError(f"Falha ao fechar ordem: {e}")

    def get_open_orders(self) -> list:
        """Obter lista de ordens abertas"""
        return [
            result for result in self._order_results.values()
            if result.status in [OrderStatus.PENDING, OrderStatus.OPEN]
        ]

    def get_current_price(self, asset: str) -> Optional[float]:
        """Obter preço atual de um ativo"""
        return self._current_prices.get(asset)
