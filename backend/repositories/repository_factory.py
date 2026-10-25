"""Factory para criação de repositórios (somente PostgreSQL)"""

from typing import Dict
from repositories.interfaces.tick_repository_interface import TickRepositoryInterface
from repositories.interfaces.user_repository_interface import UserRepositoryInterface
from repositories.interfaces.plan_repository_interface import PlanRepositoryInterface
from repositories.interfaces.subscription_repository_interface import SubscriptionRepositoryInterface
from repositories.interfaces.transaction_repository_interface import TransactionRepositoryInterface
from repositories.interfaces.autotrade_repository_interface import AutotradeRepositoryInterface
from repositories.postgresql.postgres_tick_repository import PostgresTickRepository
from repositories.postgresql.postgres_user_repository import PostgresUserRepository
from repositories.postgresql.postgres_plan_repository import PostgresPlanRepository
from repositories.postgresql.postgres_subscription_repository import PostgresSubscriptionRepository
from repositories.postgresql.postgres_transaction_repository import PostgresTransactionRepository
from repositories.postgresql.postgres_autotrade_repository import PostgresAutotradeRepository


class RepositoryFactory:
    """Fábrica de repositórios (sem singleton para evitar problemas de cache)"""

    @staticmethod
    def create_tick_repository(config: Dict) -> TickRepositoryInterface:
        """Criar repositório de ticks PostgreSQL"""
        return PostgresTickRepository(
            config.get("POSTGRES_HOST", "localhost"),
            config.get("POSTGRES_PORT", 5432),
            config.get("POSTGRES_DB", "openob"),
            config.get("POSTGRES_USER", "openob_user"),
            config.get("POSTGRES_PASSWORD", "")
        )

    @staticmethod
    def create_user_repository(config: Dict) -> UserRepositoryInterface:
        """Criar repositório de usuários PostgreSQL"""
        return PostgresUserRepository(
            config.get("POSTGRES_HOST", "localhost"),
            config.get("POSTGRES_PORT", 5432),
            config.get("POSTGRES_DB", "openob"),
            config.get("POSTGRES_USER", "openob_user"),
            config.get("POSTGRES_PASSWORD", "")
        )

    @staticmethod
    def create_plan_repository(config: Dict) -> PlanRepositoryInterface:
        """Criar repositório de planos PostgreSQL"""
        return PostgresPlanRepository(
            config.get("POSTGRES_HOST", "localhost"),
            config.get("POSTGRES_PORT", 5432),
            config.get("POSTGRES_DB", "openob"),
            config.get("POSTGRES_USER", "openob_user"),
            config.get("POSTGRES_PASSWORD", "")
        )

    @staticmethod
    def create_subscription_repository(config: Dict) -> SubscriptionRepositoryInterface:
        """Criar repositório de subscriptions PostgreSQL"""
        return PostgresSubscriptionRepository(
            config.get("POSTGRES_HOST", "localhost"),
            config.get("POSTGRES_PORT", 5432),
            config.get("POSTGRES_DB", "openob"),
            config.get("POSTGRES_USER", "openob_user"),
            config.get("POSTGRES_PASSWORD", "")
        )

    @staticmethod
    def create_transaction_repository(config: Dict) -> TransactionRepositoryInterface:
        """Criar repositório de transações PostgreSQL"""
        return PostgresTransactionRepository(
            config.get("POSTGRES_HOST", "localhost"),
            config.get("POSTGRES_PORT", 5432),
            config.get("POSTGRES_DB", "openob"),
            config.get("POSTGRES_USER", "openob_user"),
            config.get("POSTGRES_PASSWORD", "")
        )

    @staticmethod
    def create_autotrade_repository(config: Dict) -> AutotradeRepositoryInterface:
        """Criar repositório de autotrade configs PostgreSQL"""
        return PostgresAutotradeRepository(
            config.get("POSTGRES_HOST", "localhost"),
            config.get("POSTGRES_PORT", 5432),
            config.get("POSTGRES_DB", "openob"),
            config.get("POSTGRES_USER", "openob_user"),
            config.get("POSTGRES_PASSWORD", "")
        )
