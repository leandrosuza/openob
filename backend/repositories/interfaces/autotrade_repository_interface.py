"""Interface para repositório de autotrade configs"""

from abc import ABC, abstractmethod
from typing import Optional, List
from models.autotrade import AutotradeConfig


class AutotradeRepositoryInterface(ABC):
    """Interface comum para todos os repositórios de autotrade configs"""

    @abstractmethod
    async def create(self, config: AutotradeConfig) -> AutotradeConfig:
        """Criar config e retornar com ID"""
        pass

    @abstractmethod
    async def create_config(self, user_id: int, strategy_name: str, parameters: str, amount: float, is_active: bool) -> AutotradeConfig:
        """Criar config com parâmetros individuais"""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int) -> Optional[AutotradeConfig]:
        """Obter config por user_id"""
        pass

    @abstractmethod
    async def update(self, config: AutotradeConfig) -> AutotradeConfig:
        """Atualizar config"""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Deletar config por user_id"""
        pass

    @abstractmethod
    async def get_all_configs(self) -> List[AutotradeConfig]:
        """Obter todas as configs (ativas e inativas)"""
        pass

    @abstractmethod
    async def get_active_strategies(self) -> List[AutotradeConfig]:
        """Obter todas as configs ativas"""
        pass

    @abstractmethod
    async def close(self):
        """Fechar conexão"""
        pass
