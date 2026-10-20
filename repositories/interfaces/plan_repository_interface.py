"""Interface para repositório de planos"""

from abc import ABC, abstractmethod
from typing import Optional, List
from models.plan import Plan


class PlanRepositoryInterface(ABC):
    """Interface comum para todos os repositórios de planos"""

    @abstractmethod
    async def create(self, plan: Plan) -> Plan:
        """Criar plano e retornar com ID"""
        pass

    @abstractmethod
    async def get_by_id(self, plan_id: int) -> Optional[Plan]:
        """Obter plano por ID"""
        pass

    @abstractmethod
    async def get_by_type(self, plan_type: str) -> Optional[Plan]:
        """Obter plano por tipo (free, daily, weekly, monthly)"""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Plan]:
        """Listar todos os planos"""
        pass

    @abstractmethod
    async def get_active_plans(self) -> List[Plan]:
        """Listar apenas planos ativos"""
        pass

    @abstractmethod
    async def update(self, plan: Plan) -> Plan:
        """Atualizar plano"""
        pass

    @abstractmethod
    async def delete(self, plan_id: int) -> bool:
        """Deletar plano"""
        pass

    @abstractmethod
    async def close(self):
        """Fechar conexão"""
        pass
