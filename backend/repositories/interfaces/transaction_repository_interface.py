"""Interface para repositório de transações"""

from abc import ABC, abstractmethod
from typing import Optional, List
from models.transaction import Transaction


class TransactionRepositoryInterface(ABC):
    """Interface comum para todos os repositórios de transações"""

    @abstractmethod
    async def create(self, transaction: Transaction) -> Transaction:
        """Criar transação e retornar com ID"""
        pass

    @abstractmethod
    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Obter transação por ID"""
        pass

    @abstractmethod
    async def get_by_payment_id(self, payment_id: str) -> Optional[Transaction]:
        """Obter transação por payment_id"""
        pass

    @abstractmethod
    async def get_user_transactions(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Transaction]:
        """Obter transações do usuário"""
        pass

    @abstractmethod
    async def update_status(self, transaction_id: int, status: str) -> bool:
        """Atualizar status da transação"""
        pass

    @abstractmethod
    async def update(self, transaction: Transaction) -> Transaction:
        """Atualizar transação"""
        pass

    @abstractmethod
    async def close(self):
        """Fechar conexão"""
        pass
