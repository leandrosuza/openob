"""Estratégia Scalping 5s"""

from typing import List, Dict, Any
from core.strategy import BaseStrategy


class Scalping5sStrategy(BaseStrategy):
    """Estratégia de scalping de 5 segundos"""

    def get_name(self) -> str:
        """Retornar nome da estratégia"""
        return "scalping5s"

    def get_required_parameters(self) -> List[str]:
        """Retornar lista de parâmetros necessários"""
        return ["lookback_period", "ma_period", "rsi_period", "rsi_oversold", "rsi_overbought"]

    async def analyze(self, ticks: List[Dict], parameters: Dict[str, Any]) -> Dict:
        """Analisar ticks e retornar sinal"""
        if len(ticks) < parameters.get("lookback_period", 50):
            return {
                "signal": "none",
                "duration": 5,
                "confidence": 0.0,
                "reason": "Insufficient ticks"
            }

        # Extrair preços dos ticks
        prices = [float(tick.get("price", 0)) for tick in ticks if tick.get("price")]

        if len(prices) < parameters.get("lookback_period", 50):
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

        # Confluência de indicadores
        signal, confidence, reason = self._determine_signal(
            ma, rsi, last_tick_direction, rsi_oversold, rsi_overbought
        )

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
