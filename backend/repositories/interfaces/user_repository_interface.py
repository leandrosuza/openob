"""Interface para repositório de usuários"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from models.user import User


class UserRepositoryInterface(ABC):
    """Interface comum para todos os repositórios de usuários"""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Criar usuário e retornar com ID"""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Obter usuário por ID"""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Obter usuário por username"""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Obter usuário por email"""
        pass

    @abstractmethod
    async def get_by_ssid_demo(self, ssid_demo: str) -> Optional[User]:
        """Obter usuário por SSID Demo"""
        pass

    @abstractmethod
    async def get_by_ssid_real(self, ssid_real: str) -> Optional[User]:
        """Obter usuário por SSID Real"""
        pass

    @abstractmethod
    async def verify_password(self, username: str, password: str) -> bool:
        """Verificar senha do usuário"""
        pass

    @abstractmethod
    async def update_password(self, user_id: int, new_password: str) -> bool:
        """Atualizar senha do usuário"""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Atualizar usuário"""
        pass

    @abstractmethod
    async def update_balance(self, user_id: int, balance: float) -> bool:
        """Atualizar saldo do usuário"""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Listar todos os usuários"""
        pass

    @abstractmethod
    async def get_active_users(self) -> List[User]:
        """Obter usuários ativos (is_active=True)"""
        pass

    @abstractmethod
    async def get_all_users(self) -> List[User]:
        """Obter todos os usuários (sem limite)"""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Deletar usuário"""
        pass

    @abstractmethod
    async def close(self):
        """Fechar conexão"""
        pass
