"""Monitor API - Monitoramento de saldo, payout e ativos da corretora

Este módulo gerencia conexões dedicadas para monitoramento:
1. Monitoramento de payout: Reconecta a cada 5s para obter payout atualizado
2. Monitoramento de ativos: Fica ativo indefinidamente capturando ticks em tempo real
3. Monitoramento de saldo: Extrai saldo de eventos json_data
4. Monitoramento dinâmico: Monitora automaticamente os ativos com melhor payout
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List, Set
from connection.websocket import WebSocketManager
from core.logger import get_logger
from core.exceptions import ConfigurationError
from config.settings import Settings
from repositories.repository_factory import RepositoryFactory


logger = get_logger(__name__)


class MonitorAPI:
    """API de monitoramento de saldo, payout e ativos"""

    def __init__(self):
        self.region = "DEMO"
        self.ssid = Settings.POCKETOPTION_MONITOR_SSID

        if not self.ssid:
            raise ConfigurationError("POCKETOPTION_MONITOR_SSID não definido no .env")

        self.top_assets_count = Settings.MONITOR_TOP_ASSETS

        self.payout_ws = WebSocketManager(region=self.region, name="PAYOUT")
        self.actives_ws = WebSocketManager(region=self.region, name="ATIVOS")

        self.payout_running = False
        self.payout_task = None
        self.actives_running = False
        self.actives_task = None

        self.payout_data: Dict[str, Dict[str, Any]] = {}
        self.balance_data: Dict[str, Any] = {}

        self.monitored_assets: Set[str] = set()

        config = Settings.to_dict()
        self.tick_repo = RepositoryFactory.create_tick_repository(config)
        logger.info(f"MonitorAPI inicializado com repositório: {config['DATABASE_TYPE']}")

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


    def _log_to_file(self, filename: str, message: str):
        """Log para arquivo específico em logs/ws/ apenas em modo DEBUG"""
        from config.settings import Settings

        if Settings.LOG_LEVEL.upper() != "DEBUG":
            return

        try:
            log_path = f"logs/ws/{filename}"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            logger.error(f"Erro ao escrever no arquivo {filename}: {e}")


    async def _capture_payout_event(self, event: str, data: Any):
        """Capturar eventos de payout do WebSocket"""
        try:
            self._log_to_file("monitoring_payout.txt", f"Evento recebido: {event} | Tipo: {type(data)}")

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
                    self._log_to_file("monitoring_actives.txt", f"Tick: {asset} = {price}")

                    if asset in self.monitored_assets:
                        payout = self.payout_data.get(asset, {}).get("payout")
                        self._log_to_file("monitoring_actives.txt", f"Salvando tick no repositório: {asset} @ {price}")
                        asyncio.create_task(self.tick_repo.save(asset, price, payout))
                    else:
                        self._log_to_file("monitoring_actives.txt", f"Ativo não monitorado: {asset}")

        except Exception as e:
            logger.error(f"Erro ao capturar evento de ativos: {e}")


    def _process_assets_data(self, data: List):
        """Processar dados binários de ativos para extrair payout"""
        if not isinstance(data, list) or len(data) == 0:
            return

        for item in data:
            if not isinstance(item, list) or len(item) < 6:
                continue

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


    def _process_stream_data(self, data: List):
        """Processar dados de stream de preços"""
        if not isinstance(data, list) or len(data) == 0:
            return

        for item in data:
            if not isinstance(item, list) or len(item) < 3:
                continue

            asset = item[0]
            timestamp_unix = item[1]
            price = item[2]

            self._log_to_file("monitoring_actives.txt", f"Stream: {asset} = {price} @ {timestamp_unix}")

            if asset in self.monitored_assets:
                payout = self.payout_data.get(asset, {}).get("payout")
                timestamp = datetime.fromtimestamp(timestamp_unix)
                self._log_to_file("monitoring_actives.txt", f"Salvando tick stream no repositório: {asset} @ {price}")
                asyncio.create_task(self.tick_repo.save(asset, price, payout, timestamp))


    def get_top_assets_by_payout(self, limit: int = None) -> List[Dict[str, Any]]:
        """Obter os ativos com os melhores payouts"""
        if limit is None:
            limit = self.top_assets_count

        valid_assets = [
            (symbol, data) for symbol, data in self.payout_data.items()
            if data.get("payout", 0) > 0
        ]

        sorted_assets = sorted(valid_assets, key=lambda x: x[1]["payout"], reverse=True)
        top_assets = [data for symbol, data in sorted_assets[:limit]]

        logger.debug(f"Top {limit} ativos por payout: {[a['symbol'] + '(' + str(a['payout']) + '%)' for a in top_assets]}")
        return top_assets


    async def update_monitored_assets(self):
        """Atualizar dinamicamente os ativos monitorados baseado no payout"""
        if not self.payout_data:
            logger.debug("Sem dados de payout disponíveis para atualizar monitoramento")
            return

        top_assets = self.get_top_assets_by_payout()
        new_monitored = {asset["symbol"] for asset in top_assets}

        to_add = new_monitored - self.monitored_assets
        to_remove = self.monitored_assets - new_monitored

        if to_add:
            logger.debug(f"Adicionando ativos ao monitoramento: {to_add}")
            for i, symbol in enumerate(to_add):
                await self.subscribe_asset(symbol, period=1)
                self.monitored_assets.add(symbol)
                if i < len(to_add) - 1:
                    await asyncio.sleep(0.5)

        if to_remove:
            logger.debug(f"Removendo ativos do monitoramento: {to_remove}")
            for symbol in to_remove:
                self.monitored_assets.discard(symbol)
                self._log_to_file("monitoring_actives.txt", f"Ativo removido do monitoramento: {symbol}")

        if not to_add and not to_remove:
            logger.debug("Nenhuma alteração necessária nos ativos monitorados")


    async def subscribe_asset(self, symbol: str, period: int = 1):
        """Inscrever em um ativo específico e iniciar stream"""
        try:
            await self.actives_ws.send_message(f'42["changeSymbol", {{"asset": "{symbol}", "period": {period}}}]')
            self._log_to_file("monitoring_actives.txt", f"Inscrição changeSymbol: {symbol}")
            await asyncio.sleep(0.5)

            await self.actives_ws.send_message(f'42["subfor", "{symbol}"]')
            self._log_to_file("monitoring_actives.txt", f"Inscrição subfor: {symbol}")
            await asyncio.sleep(0.5)

            await self.actives_ws.send_message('42["ps"]')
            self._log_to_file("monitoring_actives.txt", f"Stream iniciado: {symbol}")
            logger.info(f"Stream iniciado para {symbol}")

        except Exception as e:
            logger.error(f"Erro ao inscrever no ativo {symbol}: {e}")
            raise


    async def start_payout_monitoring(self, payout_interval: int = 5):
        """Iniciar monitoramento de payout (conexão permanente com requisições periódicas)"""
        self.payout_running = True
        logger.info("Payout monitoring: iniciado")

        while self.payout_running:
            try:
                logger.debug(f"Payout monitoring: payout_running={self.payout_running}, is_connected={self.payout_ws.is_connected}")

                if not self.payout_ws.is_connected:
                    logger.info("Payout monitoring: tentando conectar...")
                    connected = await self.payout_ws.connect(ssid=self.ssid, auto_reconnect=True)
                    if connected:
                        self._log_to_file("connection.txt", "Payout: Conectado com sucesso")
                        logger.info("Payout monitoring: conectado com sucesso")
                    else:
                        self._log_to_file("connection.txt", "Payout: Falha ao conectar")
                        logger.error("MONITOR DE PAYOUT | FALHA AO CONECTAR")
                        await asyncio.sleep(5)
                        continue

                if self.payout_ws.is_connected:
                    logger.debug("Payout monitoring: enviando solicitação de actives")
                    await self.payout_ws.send_message('42["actives/get"]')
                    self._log_to_file("monitoring_payout.txt", "Solicitação de payout enviada")
                    await asyncio.sleep(1)

                logger.debug(f"Payout monitoring: aguardando {payout_interval}s antes da próxima requisição")
                await asyncio.sleep(payout_interval)

            except Exception as e:
                logger.error(f"MONITOR DE PAYOUT | ERRO: {e}")
                self._log_to_file("connection.txt", f"Payout: Erro - {e}")
                await asyncio.sleep(payout_interval)


    async def start_actives_monitoring(self, update_interval: int = 30):
        """Iniciar monitoramento de ativos (conexão permanente) com atualização dinâmica"""
        self.actives_running = True

        while self.actives_running:
            try:
                if not self.actives_ws.is_connected:
                    connected = await self.actives_ws.connect(ssid=self.ssid, auto_reconnect=True)
                    if connected:
                        self._log_to_file("connection.txt", "Ativos: Conectado com sucesso")
                        logger.info("Resetando tabela ticks ao reconectar WebSocket de ativos")
                        await self.tick_repo.reset_all()
                    else:
                        self._log_to_file("connection.txt", "Ativos: Falha ao conectar")
                        logger.error("MONITOR DE ATIVOS | FALHA AO CONECTAR")
                        await asyncio.sleep(5)
                        continue

                if self.actives_ws.is_connected:
                    await self.actives_ws.send_message('42["assets/get"]')
                    self._log_to_file("monitoring_actives.txt", "Solicitação de ativos enviada")
                    await asyncio.sleep(1)

                    await self.update_monitored_assets()

                await asyncio.sleep(update_interval)

            except Exception as e:
                logger.error(f"MONITOR DE ATIVOS | ERRO: {e}")
                self._log_to_file("connection.txt", f"Ativos: Erro - {e}")
                await asyncio.sleep(5)


    async def start(self, payout_interval: int = 5, update_interval: int = 30):
        """Iniciar monitoramento"""
        logger.info("Iniciando sistema de monitoramento")
        logger.info(f"Monitorando top {self.top_assets_count} ativos por payout")

        logger.info("Resetando tabela ticks ao iniciar o sistema")
        await self.tick_repo.reset_all()

        self.payout_task = asyncio.create_task(self.start_payout_monitoring(payout_interval))
        self.actives_task = asyncio.create_task(self.start_actives_monitoring(update_interval))
        logger.info("Monitoramento iniciado")
        logger.info(f"Tasks criadas: payout={self.payout_task}, actives={self.actives_task}")


    async def stop(self):
        """Parar monitoramento"""
        logger.info("Parando sistema de monitoramento")
        self.payout_running = False
        self.actives_running = False

        tasks_to_cancel = []
        if self.payout_task:
            tasks_to_cancel.append(self.payout_task)
        if self.actives_task:
            tasks_to_cancel.append(self.actives_task)

        for task in tasks_to_cancel:
            task.cancel()

        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

        if self.payout_ws.is_connected:
            await self.payout_ws.disconnect()
        if self.actives_ws.is_connected:
            await self.actives_ws.disconnect()

        if self.tick_repo:
            await self.tick_repo.close()

        logger.info("Monitoramento parado")
