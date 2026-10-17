"""
Monitor API - Monitoramento de saldo, payout e ativos da corretora

Este módulo gerencia conexões dedicadas para monitoramento:
1. Monitoramento de payout: Reconecta a cada 5s para obter payout atualizado
2. Monitoramento de ativos: Fica ativo indefinidamente capturando ticks em tempo real
3. Monitoramento de saldo: Extrai saldo de eventos json_data
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from connection.websocket import WebSocketManager
from core.logger import get_logger


logger = get_logger(__name__)


class MonitorAPI:
    """API de monitoramento de saldo, payout e ativos"""

    def __init__(self, region: str = "DEMO"):
        load_dotenv()

        self.region = region
        self.ssid = os.getenv("POCKETOPTION_MONITOR_SSID")

        if not self.ssid:
            raise ValueError("POCKETOPTION_MONITOR_SSID não definido no .env")

        self.payout_ws = WebSocketManager(region=region)
        self.actives_ws = WebSocketManager(region=region)

        self.payout_running = False
        self.payout_task = None
        self.actives_running = False
        self.actives_task = None

        self.payout_data: Dict[str, Dict[str, Any]] = {}
        self.actives_data: Dict[str, Dict[str, Any]] = {}
        self.tick_data: Dict[str, float] = {}
        self.balance_data: Dict[str, Any] = {}

        self._setup_handlers()





    def _setup_handlers(self):
        """Configurar handlers para capturar eventos em ambas as conexões"""
        original_emit_payout = self.payout_ws._emit_event
        original_emit_actives = self.actives_ws._emit_event

        async def patched_emit_payout(event: str, data: Any):
            """Override para capturar eventos de payout"""
            await self._capture_payout_event(event, data)
            return await original_emit_payout(event, data)

        async def patched_emit_actives(event: str, data: Any):
            """Override para capturar eventos de ativos"""
            await self._capture_actives_event(event, data)
            return await original_emit_actives(event, data)

        self.payout_ws._emit_event = patched_emit_payout
        self.actives_ws._emit_event = patched_emit_actives





    async def _capture_payout_event(self, event: str, data: Any):
        """Capturar eventos de payout do WebSocket"""
        try:
            if event == "json_data" and isinstance(data, dict):
                if "balance" in data:
                    self.balance_data = data
                    self._log_to_file("monitoring_payout.txt", f"Saldo: {data}")

            if "updateAssets" in event and isinstance(data, dict):
                if data.get("_placeholder") and "num" in data:
                    self._log_to_file("monitoring_payout.txt", "Dados binários de ativos recebidos")

            if "updateAssets" in event and "_data" in event and isinstance(data, list):
                self._process_assets_data(data)

        except Exception as e:
            logger.error(f"Erro ao capturar evento de payout: {e}")





    async def _capture_actives_event(self, event: str, data: Any):
        """Capturar eventos de ativos do WebSocket"""
        try:
            log_entry = f"Evento: {event} | Dados: {data}"
            self._log_to_file("monitoring_actives.txt", log_entry)

            if "updateStream" in event and isinstance(data, dict):
                if data.get("_placeholder") and "num" in data:
                    self._log_to_file("monitoring_actives.txt", "Dados binários de stream recebidos")

            if "updateStream" in event and "_data" in event and isinstance(data, list):
                self._process_stream_data(data)

            if isinstance(data, dict):
                asset = data.get("asset", data.get("name", data.get("symbol", None)))
                price = data.get("price", data.get("value", data.get("close", data.get("bid", None))))
                if asset and price:
                    self.tick_data[asset] = price
                    self._log_to_file("monitoring_actives.txt", f"Tick: {asset} = {price}")

        except Exception as e:
            logger.error(f"Erro ao capturar evento de ativos: {e}")





    def _process_stream_data(self, data: List):
        """Processar dados de stream de preços"""
        try:
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, list) and len(item) >= 3:
                        asset = item[0]
                        timestamp = item[1]
                        price = item[2]

                        self.tick_data[asset] = price
                        self._log_to_file("monitoring_actives.txt", f"Stream: {asset} = {price} @ {timestamp}")

        except Exception as e:
            logger.error(f"Erro ao processar stream: {e}")





    def _process_assets_data(self, data: List):
        """Processar dados binários de ativos para extrair payout"""
        try:
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, list) and len(item) >= 6:
                        asset_id = item[0]
                        symbol = item[1]
                        name = item[2]
                        asset_type = item[3]
                        payout = item[5]

                        self.payout_data[symbol] = {
                            "id": asset_id,
                            "symbol": symbol,
                            "name": name,
                            "type": asset_type,
                            "payout": payout
                        }

                        self._log_to_file("monitoring_payout.txt", f"Payout {symbol}: {payout}%")

        except Exception as e:
            logger.error(f"Erro ao processar dados de ativos: {e}")





    def _log_to_file(self, filename: str, message: str):
        """Log para arquivo específico em logs/ws/"""
        try:
            log_path = f"logs/ws/{filename}"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            logger.error(f"Erro ao escrever no arquivo {filename}: {e}")





    async def subscribe_asset(self, symbol: str, period: int = 1):
        """Inscrever em um ativo específico para monitoramento"""
        try:
            await self.actives_ws.send_message(f'42["changeSymbol", {{"asset": "{symbol}", "period": {period}}}]')
            self._log_to_file("monitoring_actives.txt", f"Inscrição changeSymbol: {symbol}")

            await asyncio.sleep(0.5)

            await self.actives_ws.send_message(f'42["subfor", "{symbol}"]')
            self._log_to_file("monitoring_actives.txt", f"Inscrição subfor: {symbol}")

            await asyncio.sleep(0.5)

            await self.actives_ws.send_message('42["ps"]')
            self._log_to_file("monitoring_actives.txt", f"Solicitação de histórico inicial")

        except Exception as e:
            logger.error(f"Erro ao inscrever no ativo {symbol}: {e}")





    async def start_payout_monitoring(self, payout_interval: int = 5):
        """Iniciar monitoramento de payout (reconecta periodicamente)"""
        logger.info(f"Iniciando monitoramento de payout (intervalo: {payout_interval}s)")
        self.payout_running = True

        while self.payout_running:
            try:
                if not self.payout_ws.is_connected:
                    logger.info("Conectando ao servidor de payout")
                    connected = await self.payout_ws.connect(ssid=self.ssid)
                    if connected:
                        self._log_to_file("connection.txt", "Payout: Conectado com sucesso")
                        logger.info("Conexão de payout estabelecida")
                    else:
                        self._log_to_file("connection.txt", "Payout: Falha ao conectar")
                        logger.error("Falha ao conectar ao servidor de payout")

                if self.payout_ws.is_connected:
                    await self.payout_ws.send_message('42["actives/get"]')
                    self._log_to_file("monitoring_payout.txt", "Solicitação de payout enviada")
                    await asyncio.sleep(1)

                await asyncio.sleep(payout_interval)

                if self.payout_ws.is_connected:
                    await self.payout_ws.disconnect()
                    self._log_to_file("connection.txt", "Payout: Desconectado para reconexão")
                    logger.debug("Payout: Desconectado para reconexão")

            except Exception as e:
                logger.error(f"Erro no monitoramento de payout: {e}")
                self._log_to_file("connection.txt", f"Payout: Erro - {e}")
                await asyncio.sleep(payout_interval)





    async def start_actives_monitoring(self):
        """Iniciar monitoramento de ativos (conexão permanente)"""
        logger.info("Iniciando monitoramento de ativos (conexão permanente)")
        self.actives_running = True

        while self.actives_running:
            try:
                if not self.actives_ws.is_connected:
                    logger.info("Conectando ao servidor de ativos")
                    connected = await self.actives_ws.connect(ssid=self.ssid)
                    if connected:
                        self._log_to_file("connection.txt", "Ativos: Conectado com sucesso")
                        logger.info("Conexão de ativos estabelecida")
                    else:
                        self._log_to_file("connection.txt", "Ativos: Falha ao conectar")
                        logger.error("Falha ao conectar ao servidor de ativos")
                        await asyncio.sleep(5)
                        continue

                if self.actives_ws.is_connected:
                    await self.actives_ws.send_message('42["assets/get"]')
                    self._log_to_file("monitoring_actives.txt", "Solicitação de ativos enviada")
                    await asyncio.sleep(1)

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Erro no monitoramento de ativos: {e}")
                self._log_to_file("connection.txt", f"Ativos: Erro - {e}")
                await asyncio.sleep(5)





    async def start(self, payout_interval: int = 5):
        """Iniciar monitoramento"""
        logger.info("Iniciando sistema de monitoramento")
        self.payout_task = asyncio.create_task(self.start_payout_monitoring(payout_interval))
        self.actives_task = asyncio.create_task(self.start_actives_monitoring())
        logger.info("Monitoramento iniciado")





    async def stop(self):
        """Parar monitoramento"""
        logger.info("Parando sistema de monitoramento")
        self.payout_running = False
        self.actives_running = False

        if self.payout_task:
            self.payout_task.cancel()
        if self.actives_task:
            self.actives_task.cancel()

        if self.payout_ws.is_connected:
            await self.payout_ws.disconnect()
        if self.actives_ws.is_connected:
            await self.actives_ws.disconnect()

        logger.info("Monitoramento parado")





    def get_payout_data(self) -> Dict[str, Dict[str, Any]]:
        """Obter dados de payout atual"""
        return self.payout_data





    def get_actives_data(self) -> Dict[str, Dict[str, Any]]:
        """Obter dados de ativos atual"""
        return self.actives_data





    def get_tick_data(self) -> Dict[str, float]:
        """Obter dados de ticks atual"""
        return self.tick_data





    def get_balance_data(self) -> Dict[str, Any]:
        """Obter dados de saldo atual"""
        return self.balance_data
