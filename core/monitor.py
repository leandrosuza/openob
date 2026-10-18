"""Monitor API - Monitoramento de saldo, payout e ativos da corretora

Este módulo gerencia conexões dedicadas para monitoramento:
1. Monitoramento de payout: Reconecta a cada 5s para obter payout atualizado
2. Monitoramento de ativos: Fica ativo indefinidamente capturando ticks em tempo real
3. Monitoramento de saldo: Extrai saldo de eventos json_data
4. Monitoramento dinâmico: Monitora automaticamente os ativos com melhor payout
"""






import asyncio
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from dotenv import load_dotenv
from connection.websocket import WebSocketManager
from core.logger import get_logger
from core.exceptions import ConfigurationError, ConnectionError as OpenOBConnectionError
from config.settings import Settings
from repositories.repository_factory import RepositoryFactory






logger = get_logger(__name__)






class MonitorAPI:
    """API de monitoramento de saldo, payout e ativos"""

    def __init__(self):
        load_dotenv()

        self.region = "DEMO"
        self.ssid = os.getenv("POCKETOPTION_MONITOR_SSID")

        if not self.ssid:
            raise ConfigurationError("POCKETOPTION_MONITOR_SSID não definido no .env")

        # Número de ativos com melhor payout para monitorar
        self.top_assets_count = int(os.getenv("MONITOR_TOP_ASSETS", "5"))

        self.payout_ws = WebSocketManager(region=self.region, name="PAYOUT")
        self.actives_ws = WebSocketManager(region=self.region, name="ATIVOS")

        self.payout_running = False
        self.payout_task = None
        self.actives_running = False
        self.actives_task = None

        self.payout_data: Dict[str, Dict[str, Any]] = {}
        self.actives_data: Dict[str, Dict[str, Any]] = {}
        self.tick_data: Dict[str, float] = {}
        self.balance_data: Dict[str, Any] = {}

        # Ativos atualmente monitorados
        self.monitored_assets: Set[str] = set()

        # Buffer para dados binários de histórico
        self._history_buffer: Dict[str, List] = {}

        # Criar repositório via factory
        config = Settings.to_dict()
        self.tick_repo = RepositoryFactory.create_tick_repository(config)
        logger.info(f"MonitorAPI inicializado com repositório: {config['DATABASE_TYPE']}")

        # Registrar callback para notificar quando ocorrer reset de asset
        self.tick_repo.register_reset_callback(self._on_asset_reset)

        # Task de health check periódico (1 minuto)
        self._health_check_task = None

        self._setup_handlers()




    async def _on_asset_reset(self, asset: str):
        """Callback quando ocorre reset de asset (gap > 1min)"""
        logger.info(f"Reset detectado para {asset} - solicitando novo histórico")
        
        # Solicitar novo histórico para o asset
        # Enviar mensagem para solicitar updateHistoryNewFast
        if self.actives_ws and self.actives_ws.is_connected:
            try:
                # Formato da mensagem para solicitar histórico
                # Isso depende da API do PocketOption - ajustar conforme necessário
                history_request = f'42["updateHistoryNewFast",{{"asset":"{asset}"}}]'
                await self.actives_ws.send_message(history_request)
                logger.info(f"Solicitação de histórico enviada para {asset}")
            except Exception as e:
                logger.error(f"Erro ao solicitar histórico para {asset}: {e}")




    async def _health_check_loop(self):
        """Loop de health check periódico (1 minuto)"""
        while self.payout_running or self.actives_running:
            try:
                await asyncio.sleep(60)  # 1 minuto
                
                if not self.monitored_assets:
                    continue

                logger.debug("Iniciando health check de gaps...")
                
                for asset in list(self.monitored_assets):
                    try:
                        # Verificar último tick do asset
                        stats = await self.tick_repo.get_stats()
                        
                        # Obter último timestamp do asset
                        recent = await self.tick_repo.get_recent(asset, limit=1)
                        
                        if not recent:
                            logger.warning(f"Asset {asset} sem ticks - solicitando histórico")
                            await self._on_asset_reset(asset)
                            continue
                        
                        last_tick = recent[0]
                        last_timestamp = datetime.fromisoformat(last_tick['timestamp'])
                        if last_timestamp.tzinfo is None:
                            last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
                        
                        now = datetime.now(timezone.utc)
                        gap = (now - last_timestamp).total_seconds()
                        
                        # Se gap > 1min, resetar e solicitar novo histórico
                        if gap > 60:
                            logger.warning(f"Health check: Gap de {gap:.0f}s detectado para {asset} - resetando")
                            # Forçar reset manual
                            await self.tick_repo._reset_asset(asset)
                            await self._on_asset_reset(asset)
                        else:
                            logger.debug(f"Health check: {asset} OK (gap: {gap:.0f}s)")
                            
                    except Exception as e:
                        logger.error(f"Erro no health check para {asset}: {e}")
                        
            except asyncio.CancelledError:
                logger.info("Health check loop cancelado")
                break
            except Exception as e:
                logger.error(f"Erro no health check loop: {e}")





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

            # Processar histórico completo (updateHistoryNewFast)
            if "updateHistoryNewFast" in event:
                if isinstance(data, dict) and data.get("_placeholder"):
                    # Placeholder indica que dados virão no próximo evento
                    self._log_to_file("monitoring_actives.txt", f"Placeholder de histórico detectado, aguardando dados")
                    # Marcar que estamos esperando dados de histórico
                    self._history_buffer["waiting"] = True
                elif isinstance(data, list) and self._history_buffer.get("waiting"):
                    # Dados do histórico
                    self._log_to_file("monitoring_actives.txt", f"Dados de histórico recebidos: {len(data)} itens")
                    self._process_history_data({"history": data})
                    self._history_buffer["waiting"] = False
                elif isinstance(data, dict) and not data.get("_placeholder"):
                    # Dados completos em dict
                    self._log_to_file("monitoring_actives.txt", f"Histórico em dict detectado")
                    self._process_history_data(data)

            # Processar ticks em formato dict
            if isinstance(data, dict):
                asset = data.get("asset", data.get("name", data.get("symbol", None)))
                price = data.get("price", data.get("value", data.get("close", data.get("bid", None))))
                if asset and price:
                    self.tick_data[asset] = price
                    self._log_to_file("monitoring_actives.txt", f"Tick: {asset} = {price}")

                    # Salvar automaticamente no repositório
                    if asset in self.monitored_assets:
                        payout = self.payout_data.get(asset, {}).get("payout")
                        self._log_to_file("monitoring_actives.txt", f"Salvando tick no repositório: {asset} @ {price}")
                        asyncio.create_task(self.tick_repo.save(asset, price, payout))
                    else:
                        self._log_to_file("monitoring_actives.txt", f"Ativo não monitorado: {asset}")

        except Exception as e:
            logger.error(f"Erro ao capturar evento de ativos: {e}")





    def _process_stream_data(self, data: List):
        """Processar dados de stream de preços"""
        try:
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, list) and len(item) >= 3:
                        asset = item[0]
                        timestamp_unix = item[1]
                        price = item[2]

                        self.tick_data[asset] = price
                        self._log_to_file("monitoring_actives.txt", f"Stream: {asset} = {price} @ {timestamp_unix}")

                        # Salvar automaticamente no repositório se ativo monitorado
                        if asset in self.monitored_assets:
                            payout = self.payout_data.get(asset, {}).get("payout")
                            # Converter timestamp Unix para datetime
                            timestamp = datetime.fromtimestamp(timestamp_unix)
                            self._log_to_file("monitoring_actives.txt", f"Salvando tick stream no repositório: {asset} @ {price}")
                            asyncio.create_task(self.tick_repo.save(asset, price, payout, timestamp))

        except Exception as e:
            logger.error(f"Erro ao processar stream: {e}")





    def _process_history_data(self, data: Dict):
        """Processar histórico completo do ativo (updateHistoryNewFast)"""
        try:
            asset = data.get("asset")
            history = data.get("history", [])

            if not history:
                return

            # Se não tiver asset no dict, verificar se está na lista de monitorados
            if not asset and self.monitored_assets:
                # Tentar salvar para todos os ativos monitorados (estratégia temporária)
                for monitored_asset in self.monitored_assets:
                    self._save_history_for_asset(monitored_asset, history)
                return

            self._save_history_for_asset(asset, history)

        except Exception as e:
            logger.error(f"Erro ao processar histórico: {e}")





    def _save_history_for_asset(self, asset: str, history: List):
        """Salvar histórico para um ativo específico"""
        try:
            # Converter histórico para formato do repositório
            ticks_batch = []
            for item in history:
                if isinstance(item, list) and len(item) >= 2:
                    timestamp_unix = item[0]
                    price = item[1]

                    # Converter timestamp Unix para datetime
                    timestamp = datetime.fromtimestamp(timestamp_unix)

                    ticks_batch.append({
                        'timestamp': timestamp,
                        'price': price,
                        'payout': self.payout_data.get(asset, {}).get("payout")
                    })

            # Salvar batch no repositório se o ativo é monitorado
            if asset in self.monitored_assets and ticks_batch:
                asyncio.create_task(self.tick_repo.sync_and_save_batch(asset, ticks_batch, limit=100))
                logger.info(f"Histórico {asset}: {len(ticks_batch)} ticks processados")

            self._log_to_file("monitoring_actives.txt", f"Histórico {asset}: {len(ticks_batch)} ticks recebidos")

        except Exception as e:
            logger.error(f"Erro ao salvar histórico para {asset}: {e}")





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





    def get_top_assets_by_payout(self, limit: int = None) -> List[Dict[str, Any]]:
        """Obter os ativos com os melhores payouts"""
        if limit is None:
            limit = self.top_assets_count

        # Filtrar ativos com payout válido e ordenar por payout (maior para menor)
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

        # Identificar ativos para adicionar e remover
        to_add = new_monitored - self.monitored_assets
        to_remove = self.monitored_assets - new_monitored

        if to_add:
            logger.debug(f"Adicionando ativos ao monitoramento: {to_add}")
            for i, symbol in enumerate(to_add):
                await self.subscribe_asset(symbol, period=1)
                self.monitored_assets.add(symbol)
                # Delay de 500ms entre cada ativo para evitar flood na API
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

        except OpenOBConnectionError:
            raise
        except Exception as e:
            logger.error(f"Erro ao inscrever no ativo {symbol}: {e}")
            raise OpenOBConnectionError(f"Falha ao inscrever no ativo {symbol}: {e}")





    async def start_payout_monitoring(self, payout_interval: int = 5):
        """Iniciar monitoramento de payout (conexão permanente com requisições periódicas)"""
        self.payout_running = True

        while self.payout_running:
            try:
                if not self.payout_ws.is_connected:
                    connected = await self.payout_ws.connect(ssid=self.ssid, auto_reconnect=True)
                    if connected:
                        self._log_to_file("connection.txt", "Payout: Conectado com sucesso")
                    else:
                        self._log_to_file("connection.txt", "Payout: Falha ao conectar")
                        logger.error("MONITOR DE PAYOUT | FALHA AO CONECTAR")
                        await asyncio.sleep(5)
                        continue

                if self.payout_ws.is_connected:
                    await self.payout_ws.send_message('42["actives/get"]')
                    self._log_to_file("monitoring_payout.txt", "Solicitação de payout enviada")
                    await asyncio.sleep(1)

                await asyncio.sleep(payout_interval)

            except Exception as e:
                logger.error(f"MONITOR DE PAYOUT | ERRO: {e}")
                self._log_to_file("connection.txt", f"Payout: Erro - {e}")
                if self.payout_ws.is_connected:
                    await self.payout_ws.disconnect()
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
                    else:
                        self._log_to_file("connection.txt", "Ativos: Falha ao conectar")
                        logger.error("MONITOR DE ATIVOS | FALHA AO CONECTAR")
                        await asyncio.sleep(5)
                        continue

                if self.actives_ws.is_connected:
                    await self.actives_ws.send_message('42["assets/get"]')
                    self._log_to_file("monitoring_actives.txt", "Solicitação de ativos enviada")
                    await asyncio.sleep(1)

                    # Atualizar dinamicamente os ativos monitorados
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
        self.payout_task = asyncio.create_task(self.start_payout_monitoring(payout_interval))
        self.actives_task = asyncio.create_task(self.start_actives_monitoring(update_interval))
        self._health_check_task = asyncio.create_task(self._health_check_loop())
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
        if self._health_check_task:
            self._health_check_task.cancel()

        if self.payout_ws.is_connected:
            await self.payout_ws.disconnect()
        if self.actives_ws.is_connected:
            await self.actives_ws.disconnect()

        # Fechar repositório
        if self.tick_repo:
            await self.tick_repo.close()

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





    def get_monitored_assets(self) -> Set[str]:
        """Obter conjunto de ativos atualmente monitorados"""
        return self.monitored_assets.copy()
