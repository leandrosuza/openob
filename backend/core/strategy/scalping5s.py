"""Estratégia Scalping 5s"""

import logging
import asyncio
import time
from typing import List, Dict, Any
from core.strategy import BaseStrategy
from config.settings import Settings
from pathlib import Path

# Configurar logger específico para esta estratégia com arquivo dedicado
strategy_name = "scalping5s"
strategy_logger = logging.getLogger(f"strategy.{strategy_name}")
strategy_logger.setLevel(logging.DEBUG)

# Handler para arquivo em logs/strategy/{strategy_name}.log
strategy_log_dir = Path("logs/strategy")
strategy_log_dir.mkdir(parents=True, exist_ok=True)
strategy_file_handler = logging.FileHandler(strategy_log_dir / f"{strategy_name}.log")
strategy_file_handler.setLevel(logging.DEBUG)
strategy_file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
strategy_logger.addHandler(strategy_file_handler)

logger = strategy_logger


class Scalping5sStrategy(BaseStrategy):
    """Estratégia de scalping de 5 segundos com temporização precisa"""

    def __init__(self):
        super().__init__()
        self.last_signal_time = 0.0  # Timestamp do último sinal
        self.last_aligned_emitted = 0.0  # Último alinhamento em que emitimos sinal
        self.timeframe_seconds = 5  # Timeframe de 5 segundos
        self.tolerance_ms = 500  # Tolerância de 500ms

    def get_name(self) -> str:
        """Retornar nome da estratégia"""
        return "scalping5s"

    def _get_last_aligned_time(self, current_time: float) -> float:
        """Calcular o último alinhamento de 5 segundos (00, 05, 10, 15, etc.)"""
        # Arredondar para baixo ao múltiplo de 5 mais próximo
        return current_time - (current_time % self.timeframe_seconds)

    def get_required_parameters(self) -> List[str]:
        """Retornar lista de parâmetros necessários"""
        return ["lookback_period", "ma_period", "rsi_period", "rsi_oversold", "rsi_overbought"]

    async def analyze(self, ticks: List[Dict], parameters: Dict[str, Any]) -> Dict:
        """Analisar ticks e retornar sinal (apenas em segundos alinhados: 00, 05, 10, etc.)"""
        current_time = time.time()
        last_aligned_time = self._get_last_aligned_time(current_time)
        time_since_aligned = current_time - last_aligned_time

        # Verificar se estamos dentro da tolerância do alinhamento
        in_tolerance = time_since_aligned <= (self.tolerance_ms / 1000)
        
        # Emitir apenas se estamos na tolerância E não emitimos neste alinhamento ainda
        should_emit = in_tolerance and (last_aligned_time != self.last_aligned_emitted)

        if Settings.LOG_LEVEL.upper() == "DEBUG":
            strategy_logger.info(f"[STRATEGY] scalping5s - Analisando {len(ticks)} ticks")
            strategy_logger.info(f"[STRATEGY] Tempo atual: {current_time:.3f}")
            strategy_logger.info(f"[STRATEGY] Último alinhamento: {last_aligned_time:.3f}")
            strategy_logger.info(f"[STRATEGY] Tempo desde alinhamento: {time_since_aligned:.3f}s")
            strategy_logger.info(f"[STRATEGY] Na tolerância: {in_tolerance}")
            strategy_logger.info(f"[STRATEGY] Último alinhamento emitido: {self.last_aligned_emitted:.3f}")
            strategy_logger.info(f"[STRATEGY] Deve emitir sinal: {should_emit}")

        if not should_emit:
            return {
                "signal": "none",
                "duration": 5,
                "confidence": 0.0,
                "reason": f"Aguardando alinhamento ({time_since_aligned:.3f}s desde alinhamento)"
            }

        if len(ticks) < parameters.get("lookback_period", 50):
            if Settings.LOG_LEVEL.upper() == "DEBUG":
                strategy_logger.info(f"[STRATEGY] Ticks insuficientes: {len(ticks)} < {parameters.get('lookback_period', 50)}")
            return {
                "signal": "none",
                "duration": 5,
                "confidence": 0.0,
                "reason": "Insufficient ticks"
            }

        # Extrair preços dos ticks
        prices = [float(tick.get("price", 0)) for tick in ticks if tick.get("price")]

        if len(prices) < parameters.get("lookback_period", 50):
            if Settings.LOG_LEVEL.upper() == "DEBUG":
                strategy_logger.info(f"[STRATEGY] Preços insuficientes: {len(prices)} < {parameters.get('lookback_period', 50)}")
            return {
                "signal": "none",
                "duration": 5,
                "confidence": 0.0,
                "reason": "Insufficient price data"
            }

        # Calcular indicadores
        ma_period = parameters.get("ma_period", 5)
        rsi_period = parameters.get("rsi_period", 14)
        rsi_oversold = parameters.get("rsi_oversold", 30)
        rsi_overbought = parameters.get("rsi_overbought", 70)

        # Média móvel simples
        ma = self._calculate_sma(prices, ma_period)

        # RSI
        rsi = self._calculate_rsi(prices, rsi_period)

        # Direção dos últimos ticks
        last_tick_direction = self._get_tick_direction(prices[-5:])

        if Settings.LOG_LEVEL.upper() == "DEBUG":
            strategy_logger.info(f"[STRATEGY] Indicadores calculados:")
            strategy_logger.info(f"[STRATEGY]   - Preço atual: {prices[-1]:.5f}")
            strategy_logger.info(f"[STRATEGY]   - MA({ma_period}): {ma:.5f}")
            strategy_logger.info(f"[STRATEGY]   - RSI({rsi_period}): {rsi:.2f}")
            strategy_logger.info(f"[STRATEGY]   - Direção últimos 5 ticks: {last_tick_direction}")
            strategy_logger.info(f"[STRATEGY]   - RSI oversold threshold: {rsi_oversold}")
            strategy_logger.info(f"[STRATEGY]   - RSI overbought threshold: {rsi_overbought}")

        # Confluência de indicadores
        signal, confidence, reason = self._determine_signal(
            ma, rsi, last_tick_direction, rsi_oversold, rsi_overbought
        )

        if Settings.LOG_LEVEL.upper() == "DEBUG":
            strategy_logger.info(f"[STRATEGY] Sinal gerado: {signal.upper()} (confiança: {confidence:.2f})")
            strategy_logger.info(f"[STRATEGY] Motivo: {reason}")

        # Atualizar timestamp do último sinal e alinhamento emitido
        if signal != "none":
            self.last_signal_time = time.time()
            self.last_aligned_emitted = last_aligned_time
            if Settings.LOG_LEVEL.upper() == "DEBUG":
                strategy_logger.info(f"[STRATEGY] Timestamp do sinal atualizado: {self.last_signal_time:.3f}")
                strategy_logger.info(f"[STRATEGY] Alinhamento emitido atualizado: {self.last_aligned_emitted:.3f}")
                strategy_logger.info(f"[STRATEGY] Sinal emitido em: {int(self.last_signal_time % 60):02d}s (alinhado)")

        return {
            "signal": signal,
            "duration": 5,
            "confidence": confidence,
            "reason": reason
        }

    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Calcular média móvel simples"""
        if len(prices) < period:
            return 0.0
        return sum(prices[-period:]) / period

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calcular RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _get_tick_direction(self, prices: List[float]) -> str:
        """Determinar direção dos últimos ticks"""
        if len(prices) < 2:
            return "neutral"

        positive_ticks = sum(1 for i in range(1, len(prices)) if prices[i] > prices[i - 1])
        negative_ticks = sum(1 for i in range(1, len(prices)) if prices[i] < prices[i - 1])

        if positive_ticks > negative_ticks:
            return "up"
        elif negative_ticks > positive_ticks:
            return "down"
        else:
            return "neutral"

    def _determine_signal(
        self, ma: float, rsi: float, direction: str, rsi_oversold: float, rsi_overbought: float
    ) -> tuple:
        """Determinar sinal baseado em confluência de indicadores"""
        current_price = ma  # Simplificado - usar preço atual como proxy

        signal = "none"
        confidence = 0.0
        reasons = []

        # CALL: MA em alta + RSI não sobrecomprado + direção up
        if direction == "up" and rsi < rsi_overbought:
            signal = "call"
            confidence = 0.7
            reasons.append(f"MA({ma:.5f}) com direção up")
            reasons.append(f"RSI({rsi:.2f}) < {rsi_overbought}")

        # PUT: MA em baixa + RSI não sobrevendido + direção down
        elif direction == "down" and rsi > rsi_oversold:
            signal = "put"
            confidence = 0.7
            reasons.append(f"MA({ma:.5f}) com direção down")
            reasons.append(f"RSI({rsi:.2f}) > {rsi_oversold}")

        # Aumentar confiança se RSI em extremos
        if signal != "none":
            if rsi < rsi_oversold + 10 and signal == "call":
                confidence += 0.2
                reasons.append(f"RSI muito baixo ({rsi:.2f})")
            elif rsi > rsi_overbought - 10 and signal == "put":
                confidence += 0.2
                reasons.append(f"RSI muito alto ({rsi:.2f})")

        confidence = min(confidence, 1.0)
        reason = "; ".join(reasons) if reasons else "No clear signal"

        return signal, confidence, reason
