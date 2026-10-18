"""Market Data API"""

import asyncio
import json
from typing import List, Optional
from datetime import datetime
from models.market import Candle
from core.constants import ASSETS, TIMEFRAMES
from core.logger import get_logger
from core.exceptions import ValidationError, ConnectionError as OpenOBConnectionError

logger = get_logger(__name__)


class MarketAPI:
    """API de dados de mercado"""

    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
        self._candles_cache: dict = {}
        self._candle_requests: dict = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """Configurar handlers de eventos"""
        handlers = {
            "changeSymbol": self._on_change_symbol,
            "updateHistoryNewFast": self._on_history_update,
            "updateStream": self._on_stream_update,
            "updateAssets": self._on_assets_update,
            "json_data": self._on_json_data,
        }
        for event, handler in handlers.items():
            self.ws_manager.add_event_handler(event, handler)

    async def _on_change_symbol(self, data):
        """Handler para resposta do changeSymbol"""
        try:
            logger.debug(f"changeSymbol response recebido: {str(data)[:100]}...")
            if isinstance(data, dict):
                asset = data.get("asset")
                period = data.get("period")
                if asset and period:
                    request_id = f"{asset}_{period}"
                    if request_id in self._candle_requests:
                        future = self._candle_requests[request_id]
                        if not future.done():
                            candles = self._parse_stream_candles(data, asset, period)
                            future.set_result(candles)
                            del self._candle_requests[request_id]
                            logger.info(f"Candles resolvidos para {request_id}: {len(candles)}")
        except Exception as e:
            logger.error(f"Erro ao processar changeSymbol: {e}")

    def _parse_stream_candles(self, stream_data: dict, asset: str, timeframe: int):
        """Parse candles de stream data"""
        candles = []
        try:
            candle_data = stream_data.get("data") or stream_data.get("candles") or []
            if isinstance(candle_data, list):
                for item in candle_data:
                    if isinstance(item, dict):
                        candle = Candle(
                            timestamp=datetime.fromtimestamp(item.get("time", 0)),
                            open=float(item.get("open", 0)),
                            high=float(item.get("high", 0)),
                            low=float(item.get("low", 0)),
                            close=float(item.get("close", 0)),
                            volume=float(item.get("volume", 0)),
                            asset=asset,
                            timeframe=timeframe,
                        )
                        candles.append(candle)
                    elif isinstance(item, (list, tuple)) and len(item) >= 5:
                        candle = Candle(
                            timestamp=datetime.fromtimestamp(item[0]),
                            open=float(item[1]),
                            close=float(item[2]),
                            high=float(item[3]),
                            low=float(item[4]),
                            volume=float(item[5]) if len(item) > 5 else 0.0,
                            asset=asset,
                            timeframe=timeframe,
                        )
                        candles.append(candle)
        except Exception as e:
            logger.error(f"Erro ao parse stream candles: {e}")
        return candles

    async def _on_history_update(self, data):
        """Handler para updateHistoryNewFast"""
        try:
            if isinstance(data, dict):
                asset = data.get("asset")
                period = data.get("period")
                history = data.get("history", [])
                if asset and period and history:
                    request_id = f"{asset}_{period}"
                    if request_id in self._candle_requests:
                        future = self._candle_requests[request_id]
                        if not future.done():
                            candles = self._parse_history_candles(history, asset, period)
                            future.set_result(candles)
                            del self._candle_requests[request_id]
                            logger.debug(f"História atualizada para {request_id}")
        except Exception as e:
            logger.error(f"Erro em handler de mercado: {e}")

    def _parse_history_candles(self, history: list, asset: str, timeframe: int):
        """Parse candles de history data"""
        candles = []
        try:
            if not history:
                return candles

            from collections import defaultdict
            candle_groups = defaultdict(list)

            for item in history:
                if isinstance(item, list) and len(item) >= 2:
                    timestamp = item[0]
                    price = item[1]
                    bucket = int(timestamp // timeframe) * timeframe
                    candle_groups[bucket].append((timestamp, price))

            for bucket in sorted(candle_groups.keys()):
                prices = [p for _, p in candle_groups[bucket]]
                if prices:
                    candle_data = {
                        "timestamp": datetime.fromtimestamp(bucket),
                        "open": float(prices[0]),
                        "close": float(prices[-1]),
                        "high": float(max(prices)),
                        "low": float(min(prices)),
                        "volume": len(prices),
                        "asset": asset,
                        "timeframe": timeframe,
                    }
                    candle = Candle.model_validate(candle_data)
                    candles.append(candle)

        except Exception as e:
            logger.error(f"Erro em handler de mercado: {e}")
        return candles

    async def _on_stream_update(self, data):
        """Handler para updateStream - atualização em tempo real de candles"""
        try:
            if isinstance(data, dict):
                asset = data.get("asset")
                period = data.get("period")
                price = data.get("price") or data.get("close")
                if asset and period and price:
                    cache_key = f"{asset}_{period}"
                    if cache_key in self._candles_cache:
                        candles = self._candles_cache[cache_key]
                        if candles:
                            last_candle = candles[-1]
                            updated_candle = Candle(
                                timestamp=last_candle.timestamp,
                                open=last_candle.open,
                                close=float(price),
                                high=max(last_candle.high, float(price)),
                                low=min(last_candle.low, float(price)),
                                volume=last_candle.volume + 1,
                                asset=asset,
                                timeframe=period,
                            )
                            candles[-1] = updated_candle
                            logger.debug(f"Candle atualizado para {asset}: {price}")
        except Exception as e:
            logger.error(f"Erro ao processar stream update: {e}")

    async def _on_assets_update(self, data):
        """Handler para atualização de ativos disponíveis"""
        try:
            if isinstance(data, dict):
                assets = data.get("assets") or data.get("active")
                if assets:
                    logger.info(f"Ativos atualizados: {len(assets) if isinstance(assets, list) else 'N/A'}")
        except Exception as e:
            logger.error(f"Erro ao processar atualização de ativos: {e}")

    async def _on_json_data(self, data):
        """Handler para dados JSON"""
        try:
            if isinstance(data, dict) and "asset" in data and "period" in data and "history" in data:
                await self._on_history_update(data)
        except Exception as e:
            logger.error(f"Erro ao processar JSON data: {e}")

    async def get_candles(self, asset: str, timeframe: str, count: int = 100) -> List[Candle]:
        """Obter candles históricos"""
        if not self.ws_manager.is_connected:
            raise OpenOBConnectionError("WebSocket não está conectado")

        if asset not in ASSETS:
            raise ValidationError(f"Ativo inválido: {asset}")

        if timeframe not in TIMEFRAMES:
            raise ValidationError(f"Timeframe inválido: {timeframe}")

        try:
            asset_id = ASSETS[asset]
            timeframe_seconds = TIMEFRAMES[timeframe]

            logger.info(f"Solicitando candles: {asset}, {timeframe}, count={count}")

            candle_future = asyncio.Future()
            request_id = f"{asset}_{timeframe_seconds}"
            self._candle_requests[request_id] = candle_future

            message = self._format_candles_message(
                asset=asset,
                timeframe=timeframe_seconds,
                start_time=0,
                end_time=0,
                count=count,
            )

            await self.ws_manager.send_message(message)

            try:
                candles = await asyncio.wait_for(candle_future, timeout=10.0)
                logger.info(f"Candles recebidos: {len(candles)}")
                return candles
            except asyncio.TimeoutError:
                logger.warning("Timeout aguardando candles")
                return []
            finally:
                if request_id in self._candle_requests:
                    del self._candle_requests[request_id]

        except OpenOBConnectionError:
            raise
        except Exception as e:
            logger.error(f"Erro ao obter candles: {e}")
            return []

    def _format_candles_message(self, asset: str, timeframe: int, start_time: int, end_time: int, count: int) -> str:
        """Formatar mensagem de solicitação de candles"""
        message_data = ["changeSymbol", {"asset": str(asset), "period": timeframe}]
        message = f"42{json.dumps(message_data)}"
        return message

    def get_available_assets(self) -> dict:
        """Obter lista de ativos disponíveis"""
        return ASSETS

    def get_available_timeframes(self) -> dict:
        """Obter lista de timeframes disponíveis"""
        return TIMEFRAMES
