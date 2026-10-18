"""Interface para repositório de ticks"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class TickRepositoryInterface(ABC):
    """Interface comum para todos os repositórios de ticks"""

    @abstractmethod
    async def save(self, asset: str, price: float, payout: Optional[float] = None, timestamp: Optional[datetime] = None) -> int:
        """Salvar tick e retornar sequence number"""
        pass




    @abstractmethod
    async def get_recent(self, asset: str, limit: int = 100) -> List[Dict]:
        """Obter ticks recentes de um ativo"""
        pass




    @abstractmethod
    async def get_by_sequence(self, asset: str, start: int, end: int) -> List[Dict]:
        """Obter ticks por range de sequência"""
        pass




    @abstractmethod
    async def get_stats(self) -> Dict:
        """Obter estatísticas do banco"""
        pass


    @abstractmethod
    async def reset_all(self):
        """Resetar todos os dados da tabela ticks"""
        pass




    @abstractmethod
    async def close(self):
        """Fechar conexão"""
        pass
