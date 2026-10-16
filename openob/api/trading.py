"""
Trading API
"""

import uuid
import asyncio
from typing import Optional
from openob.models.trading import OrderDirection, OrderResult, OrderStatus, Order
from openob.core.constants import ASSETS, API_LIMITS


class TradingAPI:
    """API de trading e ordens"""

    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
        self._pending_orders: dict = {}
        self._order_results: dict = {}
        self._order_id_mapping: dict = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """Configurar handlers de eventos"""
        self.ws_manager.add_event_handler("order", self._on_order)
        self.ws_manager.add_event_handler("order-placed", self._on_order_placed)
        self.ws_manager.add_event_handler("order-won", self._on_order_won)
        self.ws_manager.add_event_handler("order-lost", self._on_order_lost)
        self.ws_manager.add_event_handler("buy", self._on_buy)
        self.ws_manager.add_event_handler("successbuy", self._on_success_buy)
        self.ws_manager.add_event_handler("openOrder", self._on_open_order)
        self.ws_manager.add_event_handler("successopenOrder", self._on_success_open_order)
        self.ws_manager.add_event_handler("closeOrder", self._on_close_order)
        self.ws_manager.add_event_handler("successcloseOrder", self._on_success_close_order)
        self.ws_manager.add_event_handler("json_data", self._on_json_data)
        # Handlers adicionais do PocketOptionAPI
        self.ws_manager.add_event_handler("order_opened", self._on_order_opened)
        self.ws_manager.add_event_handler("order_closed", self._on_order_closed)
        self.ws_manager.add_event_handler("stream_update", self._on_stream_update)

    async def _on_order(self, data):
        """Handler para ordem"""
        try:
            # Silencioso
            pass
        except Exception as e:
            pass

    async def _on_order_placed(self, data):
        """Handler para ordem colocada"""
        try:
            # Silencioso
            pass
        except Exception as e:
            pass

    async def _on_order_won(self, data):
        """Handler para ordem ganha"""
        try:
            # Silencioso
            pass
        except Exception as e:
            pass

    async def _on_order_lost(self, data):
        """Handler para ordem perdida"""
        try:
            # Silencioso
            pass
        except Exception as e:
            pass

    async def _on_buy(self, data):
        """Handler para resposta de compra"""
        try:
            # Silencioso
            pass
        except Exception as e:
            pass

    async def _on_success_buy(self, data):
        """Handler para compra bem-sucedida"""
        try:
            # Silencioso
            pass
        except Exception as e:
            pass

    async def _on_open_order(self, data):
        """Handler para ordem aberta"""
        try:
            # Silencioso
            pass
        except Exception as e:
            pass

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
                            break
        except Exception as e:
            pass

    async def _on_close_order(self, data):
        """Handler para ordem fechada"""
        try:
            # Silencioso
            pass
        except Exception as e:
            pass

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

                    print(f"Resultado: {status.value} | Profit: ${deal_profit}")

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
            pass

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

                        print(f"Resultado (JSON): {status.value} | Profit: ${deal_profit}")

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
                                print(f"Ordem local {local_id} atualizada: {status.value} (${deal_profit})")
                                break

        except Exception as e:
            print(f"Erro ao processar JSON: {e}")
            import traceback
            traceback.print_exc()

    async def _on_order_opened(self, data):
        """Handler para ordem aberta"""
        try:
            print(f"Ordem aberta (event): {data}")
        except Exception as e:
            print(f"Erro ao processar ordem aberta: {e}")

    async def _on_order_closed(self, data):
        """Handler para ordem fechada"""
        try:
            print(f"Ordem fechada (event): {data}")
        except Exception as e:
            print(f"Erro ao processar ordem fechada: {e}")

    async def _on_stream_update(self, data):
        """Handler para atualização de stream de preços"""
        try:
            # Silencioso para não poluir o log - ticks chegam em alta frequência
            pass
        except Exception as e:
            # Silencioso mesmo em erro
            pass

    async def place_order(self, asset: str, amount: float, direction: OrderDirection, duration: int) -> OrderResult:
        """Colocar uma ordem de trading"""
        if not self.ws_manager.is_connected:
            raise Exception("WebSocket não está conectado")

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

            print(f"Enviando ordem: {asset}, {amount}, {direction}, {duration}s")

            await self.ws_manager.send_message(order_message)

            result = OrderResult(
                order_id=order.request_id,
                status=OrderStatus.PENDING,
                profit=0,
                message="Ordem enviada"
            )

            self._pending_orders[order.request_id] = result
            self._order_results[order.request_id] = result

            return result

        except Exception as e:
            print(f"Erro ao colocar ordem: {e}")
            raise

    def _validate_order_parameters(self, asset: str, amount: float, direction: OrderDirection, duration: int):
        """Validar parâmetros da ordem"""
        if asset not in ASSETS:
            raise ValueError(f"Ativo inválido: {asset}")

        if amount < API_LIMITS["min_order_amount"] or amount > API_LIMITS["max_order_amount"]:
            raise ValueError(f"Valor da ordem deve estar entre {API_LIMITS['min_order_amount']} e {API_LIMITS['max_order_amount']}")

        if duration < API_LIMITS["min_duration"] or duration > API_LIMITS["max_duration"]:
            raise ValueError(f"Duração deve estar entre {API_LIMITS['min_duration']} e {API_LIMITS['max_duration']} segundos")

    def _format_order_message(self, asset: str, amount: float, direction: str, duration: int, request_id: str) -> str:
        """Formatar mensagem de ordem para WebSocket - formato openOrder"""
        message = f'42["openOrder",{{"asset":"{asset}","amount":{amount},"action":"{direction}","isDemo":1,"requestId":"{request_id}","optionType":100,"time":{duration}}}]'
        return message
