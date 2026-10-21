"""Interface para repositório de subscriptions"""

from abc import ABC, abstractmethod
from typing import Optional, List
from models.subscription import Subscription


class SubscriptionRepositoryInterface(ABC):
    """Interface comum para todos os repositórios de subscriptions"""

    @abstractmethod
    async def create(self, subscription: Subscription) -> Subscription:
        """Criar subscription e retornar com ID"""
        pass

    @abstractmethod
    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Obter subscription por ID"""
        pass

    @abstractmethod
    async def get_active_by_user(self, user_id: int) -> Optional[Subscription]:
        """Obter subscription ativa do usuário"""
        pass

    @abstractmethod
    async def get_all_by_user(self, user_id: int) -> List[Subscription]:
        """Obter todas as subscriptions do usuário (ativas + expiradas)"""
        pass

    @abstractmethod
    async def get_history(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Subscription]:
        """Obter histórico de subscriptions do usuário"""
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[Subscription]:
        """Obter subscriptions por status"""
        pass

    @abstractmethod
    async def get_expired_subscriptions(self) -> List[Subscription]:
        """Obter subscriptions ativas expiradas (end_date < now)"""
        pass

    @abstractmethod
    async def get_grace_period_subscriptions(self, grace_period_days: int) -> List[Subscription]:
        """Obter subscriptions em grace period que já expiraram"""
        pass

    @abstractmethod
    async def get_auto_renew_expiring(self) -> List[Subscription]:
        """Obter subscriptions com auto_renew que estão expirando"""
        pass

    @abstractmethod
    async def update(self, subscription: Subscription) -> Subscription:
        """Atualizar subscription"""
        pass

    @abstractmethod
    async def update_status(self, subscription_id: int, status: str) -> bool:
        """Atualizar status da subscription"""
        pass

    @abstractmethod
    async def cancel(self, subscription_id: int) -> bool:
        """Cancelar subscription"""
        pass

    @abstractmethod
    async def expire_subscription(self, subscription_id: int) -> bool:
        """Expirar subscription (sem deletar - manter histórico)"""
        pass

    @abstractmethod
    async def create_for_user(self, user_id: int, plan_id: int, start_date, end_date, 
                            payment_method: Optional[str] = None, 
                            payment_id: Optional[str] = None,
                            auto_renew: bool = False) -> Subscription:
        """Criar subscription para um usuário"""
        pass

    @abstractmethod
    async def close(self):
        """Fechar conexão"""
        pass
