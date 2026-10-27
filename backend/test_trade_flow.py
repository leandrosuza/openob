"""
Script de teste para entender o fluxo de eventos da corretora
Mostra a sequência completa de eventos desde o envio da ordem até o resultado final
"""

import asyncio
import json
from connection.websocket import WebSocketManager
from api.pocketoption.trading import TradingAPI
from core.logger import get_logger

logger = get_logger(__name__)


class TradeFlowTester:
    """Testador de fluxo de trades"""
    
    def __init__(self, ssid: str):
        self.ws_manager = WebSocketManager(region="DEMO", name="TEST")
        self.trading_api = TradingAPI(self.ws_manager)
        self.ssid = ssid
        self.events = []
        
    async def setup(self):
        """Configurar handlers para capturar todos os eventos"""
        
        # Capturar todos os eventos enviados
        original_send = self.ws_manager._send
        async def on_send(data):
            self.events.append({
                "direction": "OUT",
                "data": data,
                "timestamp": asyncio.get_event_loop().time()
            })
            return await original_send(data)
        self.ws_manager._send = on_send
        
        # Capturar todos os eventos recebidos
        original_emit = self.ws_manager._emit_event
        async def on_emit(event, data):
            self.events.append({
                "direction": "IN",
                "event": event,
                "data": data,
                "timestamp": asyncio.get_event_loop().time()
            })
            logger.info(f"[TEST] Evento: {event} | Data: {type(data)}")
            if isinstance(data, dict):
                if "profit" in data:
                    logger.info(f"[TEST] Profit encontrado: {data['profit']}")
                if "deals" in data:
                    logger.info(f"[TEST] Deals encontrados: {len(data['deals'])}")
                    for deal in data["deals"]:
                        logger.info(f"[TEST]   Deal ID: {deal.get('id')}")
                        logger.info(f"[TEST]   Request ID: {deal.get('requestId')}")
                        logger.info(f"[TEST]   Profit: {deal.get('profit')}")
            return await original_emit(event, data)
        self.ws_manager._emit_event = on_emit
        
    async def connect(self):
        """Conectar WebSocket"""
        logger.info(f"[TEST] Conectando WebSocket...")
        await self.ws_manager.connect(ssid=self.ssid, auto_reconnect=False)
        logger.info(f"[TEST] Conectado!")
        
    async def send_test_order(self):
        """Enviar ordem de teste"""
        logger.info(f"[TEST] Enviando ordem de teste...")
        from models.trading import OrderDirection
        
        result = await self.trading_api.place_order(
            asset="#AXP_otc",
            amount=5.0,
            direction=OrderDirection.PUT,
            duration=5
        )
        
        logger.info(f"[TEST] Ordem enviada: {result}")
        logger.info(f"[TEST] Request ID: {result.request_id if hasattr(result, 'request_id') else 'N/A'}")
        
        return result
        
    async def wait_for_result(self, order_id: str, timeout: float = 10.0):
        """Aguardar resultado da ordem"""
        logger.info(f"[TEST] Aguardando resultado para order_id: {order_id}")
        
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            await asyncio.sleep(0.5)
            
            if hasattr(self.trading_api, '_order_results') and order_id in self.trading_api._order_results:
                result = self.trading_api._order_results[order_id]
                logger.info(f"[TEST] Resultado encontrado: {result}")
                logger.info(f"[TEST] Status: {result.status}")
                logger.info(f"[TEST] Profit: {result.profit}")
                
                # Verificar se é terminal
                from models.trading import OrderStatus
                if result.status in [OrderStatus.WIN, OrderStatus.LOSS, OrderStatus.CLOSED]:
                    logger.info(f"[TEST] Trade finalizado!")
                    return result
                else:
                    logger.info(f"[TEST] Status não-terminal, continuando aguardando...")
        
        logger.warning(f"[TEST] Timeout atingido")
        return None
        
    async def analyze_events(self):
        """Analisar eventos capturados"""
        logger.info(f"[TEST] Analisando {len(self.events)} eventos capturados")
        
        for i, event in enumerate(self.events):
            direction = event["direction"]
            timestamp = event["timestamp"]
            
            if direction == "OUT":
                logger.info(f"[TEST] {i} [OUT] {timestamp:.2f}s: {event['data'][:100]}...")
            else:
                event_name = event["event"]
                data = event["data"]
                logger.info(f"[TEST] {i} [IN] {timestamp:.2f}s: {event_name}")
                
                if isinstance(data, dict):
                    if "profit" in data:
                        logger.info(f"[TEST]      -> Profit: {data['profit']}")
                    if "deals" in data:
                        logger.info(f"[TEST]      -> Deals: {len(data['deals'])}")
                        for deal in data["deals"]:
                            logger.info(f"[TEST]         - Request ID: {deal.get('requestId')}")
                            logger.info(f"[TEST]         - Profit: {deal.get('profit')}")
        
    async def run(self):
        """Executar teste completo"""
        try:
            await self.setup()
            await self.connect()
            
            # Aguardar estabilização
            await asyncio.sleep(2)
            
            # Enviar ordem
            result = await self.send_test_order()
            order_id = result.request_id if hasattr(result, 'request_id') else result.order_id
            
            # Aguardar resultado
            final_result = await self.wait_for_result(order_id, timeout=10.0)
            
            # Analisar eventos
            await self.analyze_events()
            
        except Exception as e:
            logger.error(f"[TEST] Erro: {e}")
        finally:
            await self.ws_manager.disconnect()


async def main():
    """Função principal"""
    # Obter SSID do usuário 5
    from repositories.postgresql.postgres_user_repository import PostgresUserRepository
    from database import get_session
    
    session = get_session()
    user_repo = PostgresUserRepository(session)
    
    user = await user_repo.get_by_id(5)
    if not user:
        logger.error("Usuário 5 não encontrado")
        return
    
    ssid = user.ssid_demo if user.mode == "demo" else user.ssid_real
    if not ssid:
        logger.error("SSID não configurado")
        return
    
    logger.info(f"SSID obtido: {ssid[:20]}...")
    
    # Executar teste
    tester = TradeFlowTester(ssid)
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
