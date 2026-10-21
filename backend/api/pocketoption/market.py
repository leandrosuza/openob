"""Market Data API"""

import asyncio
import json
from typing import List, Optional
from datetime import datetime
from collections import defaultdict
from models.market import Candle
from core.constants import ASSETS, TIMEFRAMES
from core.logger import get_logger
from core.exceptions import ValidationError


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


    def _parse_candle_from_dict(self, item: dict, asset: str, timeframe: int) -> Optional[Candle]:
        """Parse candle de dict"""
        try:
            return Candle(
                timestamp=datetime.fromtimestamp(item.get("time", 0)),
                open=float(item.get("open", 0)),
                high=float(item.get("high", 0)),
                low=float(item.get("low", 0)),
                close=float(item.get("close", 0)),
                volume=float(item.get("volume", 0)),
                asset=asset,
                timeframe=timeframe,
            )
        except Exception as e:
            logger.error(f"Erro ao parsear candle de dict: {e}")
            return None


    def _parse_candle_from_list(self, item: list, asset: str, timeframe: int) -> Optional[Candle]:
        """Parse candle de lista/tupla"""
        try:
            return Candle(
                timestamp=datetime.fromtimestamp(item[0]),
                open=float(item[1]),
                close=float(item[2]),
                high=float(item[3]),
                low=float(item[4]),
                volume=float(item[5]) if len(item) > 5 else 0.0,
                asset=asset,
                timeframe=timeframe,
            )
        except Exception as e:
            logger.error(f"Erro ao parsear candle de lista: {e}")
            return None


    def _parse_stream_candles(self, stream_data: dict, asset: str, timeframe: int) -> List[Candle]:
        """Parse candles de stream data"""
        candles = []
        candle_data = stream_data.get("data") or stream_data.get("candles") or []

        if not isinstance(candle_data, list):
            return candles

        for item in candle_data:
            if isinstance(item, dict):
                candle = self._parse_candle_from_dict(item, asset, timeframe)
                if candle:
                    candles.append(candle)
            elif isinstance(item, (list, tuple)) and len(item) >= 5:
                candle = self._parse_candle_from_list(item, asset, timeframe)
                if candle:
                    candles.append(candle)

        return candles


    def _parse_history_candles(self, history: list, asset: str, timeframe: int) -> List[Candle]:
        """Parse candles de history data"""
        if not history:
            return []

        candles = []
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
                candle = Candle(
                    timestamp=datetime.fromtimestamp(bucket),
                    open=float(prices[0]),
                    close=float(prices[-1]),
                    high=float(max(prices)),
                    low=float(min(prices)),
                    volume=len(prices),
                    asset=asset,
                    timeframe=timeframe,
                )
                candles.append(candle)

        return candles


    async def _on_change_symbol(self, data):
        """Handler para resposta do changeSymbol"""
        if not isinstance(data, dict):
            return

        asset = data.get("asset")
        period = data.get("period")
        if not asset or not period:
            return

        request_id = f"{asset}_{period}"
        if request_id not in self._candle_requests:
            return

        future = self._candle_requests[request_id]
        if future.done():
            return

        candles = self._parse_stream_candles(data, asset, period)
        future.set_result(candles)
        del self._candle_requests[request_id]
        logger.info(f"Candles resolvidos para {request_id}: {len(candles)}")


    async def _on_history_update(self, data):
        """Handler para updateHistoryNewFast"""
        if not isinstance(data, dict):
            return

        asset = data.get("asset")
        period = data.get("period")
        history = data.get("history", [])
        if not asset or not period or not history:
            return

        request_id = f"{asset}_{period}"
        if request_id not in self._candle_requests:
            return

        future = self._candle_requests[request_id]
        if future.done():
            return

        candles = self._parse_history_candles(history, asset, period)
        future.set_result(candles)
        del self._candle_requests[request_id]
        logger.debug(f"História atualizada para {request_id}")


    async def _on_stream_update(self, data):
        """Handler para updateStream - atualização em tempo real de candles"""
        if not isinstance(data, dict):
            return

        asset = data.get("asset")
        period = data.get("period")
        price = data.get("price") or data.get("close")
        if not asset or not period or not price:
            return

        cache_key = f"{asset}_{period}"
        if cache_key not in self._candles_cache or not self._candles_cache[cache_key]:
            return

        candles = self._candles_cache[cache_key]
        last_candle = candles[-1]
        price_float = float(price)

        updated_candle = Candle(
            timestamp=last_candle.timestamp,
            open=last_candle.open,
            close=price_float,
            high=max(last_candle.high, price_float),
            low=min(last_candle.low, price_float),
            volume=last_candle.volume + 1,
            asset=asset,
            timeframe=period,
        )
        candles[-1] = updated_candle
        logger.debug(f"Candle atualizado para {asset}: {price}")


    async def _on_assets_update(self, data):
        """Handler para atualização de ativos disponíveis"""
        if not isinstance(data, dict):
            return

        assets = data.get("assets") or data.get("active")
        if assets:
            logger.info(f"Ativos atualizados: {len(assets) if isinstance(assets, list) else 'N/A'}")


    async def _on_json_data(self, data):
        """Handler para dados JSON"""
        if isinstance(data, dict) and "asset" in data and "period" in data and "history" in data:
            await self._on_history_update(data)


    async def get_candles(self, asset: str, timeframe: str, count: int = 100) -> List[Candle]:
        """Obter candles históricos"""
        if not self.ws_manager.is_connected:
            raise ConnectionError("WebSocket não está conectado")

        if asset not in ASSETS:
            raise ValidationError(f"Ativo inválido: {asset}")

        if timeframe not in TIMEFRAMES:
            raise ValidationError(f"Timeframe inválido: {timeframe}")

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


    def _format_candles_message(self, asset: str, timeframe: int, start_time: int, end_time: int, count: int) -> str:
        """Formatar mensagem de solicitação de candles"""
        message_data = ["changeSymbol", {"asset": str(asset), "period": timeframe}]
        return f"42{json.dumps(message_data)}"


    def get_available_assets(self) -> dict:
        """Obter lista de ativos disponíveis"""
        return ASSETS


    def get_available_timeframes(self) -> dict:
        """Obter lista de timeframes disponíveis"""
        return TIMEFRAMES
