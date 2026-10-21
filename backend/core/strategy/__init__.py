"""Estrutura de estratégias de trading"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseStrategy(ABC):
    """Classe base para estratégias de trading"""

    @abstractmethod
    def get_name(self) -> str:
        """Retornar nome da estratégia"""
        pass

    @abstractmethod
    def get_required_parameters(self) -> List[str]:
        """Retornar lista de parâmetros necessários"""
        pass

    @abstractmethod
    async def analyze(self, ticks: List[Dict], parameters: Dict[str, Any]) -> Dict:
        """Analisar ticks e retornar sinal"""
        pass
