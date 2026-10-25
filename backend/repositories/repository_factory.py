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
    """Fábrica de repositórios com singleton para pools de conexão"""

    _instances: Dict[str, any] = {}

    @staticmethod
    def create_tick_repository(config: Dict) -> TickRepositoryInterface:
        """Criar repositório de ticks PostgreSQL (singleton)"""
        cache_key = "tick_postgresql"

        if cache_key not in RepositoryFactory._instances:
            RepositoryFactory._instances[cache_key] = PostgresTickRepository(
                config.get("POSTGRES_HOST", "localhost"),
                config.get("POSTGRES_PORT", 5432),
                config.get("POSTGRES_DB", "openob"),
                config.get("POSTGRES_USER", "openob_user"),
                config.get("POSTGRES_PASSWORD", "")
            )

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_user_repository(config: Dict) -> UserRepositoryInterface:
        """Criar repositório de usuários PostgreSQL (singleton)"""
        cache_key = "user_postgresql"

        if cache_key not in RepositoryFactory._instances:
            RepositoryFactory._instances[cache_key] = PostgresUserRepository(
                config.get("POSTGRES_HOST", "localhost"),
                config.get("POSTGRES_PORT", 5432),
                config.get("POSTGRES_DB", "openob"),
                config.get("POSTGRES_USER", "openob_user"),
                config.get("POSTGRES_PASSWORD", "")
            )

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_plan_repository(config: Dict) -> PlanRepositoryInterface:
        """Criar repositório de planos PostgreSQL (singleton)"""
        cache_key = "plan_postgresql"

        if cache_key not in RepositoryFactory._instances:
            RepositoryFactory._instances[cache_key] = PostgresPlanRepository(
                config.get("POSTGRES_HOST", "localhost"),
                config.get("POSTGRES_PORT", 5432),
                config.get("POSTGRES_DB", "openob"),
                config.get("POSTGRES_USER", "openob_user"),
                config.get("POSTGRES_PASSWORD", "")
            )

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_subscription_repository(config: Dict) -> SubscriptionRepositoryInterface:
        """Criar repositório de subscriptions PostgreSQL (singleton)"""
        cache_key = "subscription_postgresql"

        if cache_key not in RepositoryFactory._instances:
            RepositoryFactory._instances[cache_key] = PostgresSubscriptionRepository(
                config.get("POSTGRES_HOST", "localhost"),
                config.get("POSTGRES_PORT", 5432),
                config.get("POSTGRES_DB", "openob"),
                config.get("POSTGRES_USER", "openob_user"),
                config.get("POSTGRES_PASSWORD", "")
            )

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_transaction_repository(config: Dict) -> TransactionRepositoryInterface:
        """Criar repositório de transações PostgreSQL (singleton)"""
        cache_key = "transaction_postgresql"

        if cache_key not in RepositoryFactory._instances:
            RepositoryFactory._instances[cache_key] = PostgresTransactionRepository(
                config.get("POSTGRES_HOST", "localhost"),
                config.get("POSTGRES_PORT", 5432),
                config.get("POSTGRES_DB", "openob"),
                config.get("POSTGRES_USER", "openob_user"),
                config.get("POSTGRES_PASSWORD", "")
            )

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_autotrade_repository(config: Dict) -> AutotradeRepositoryInterface:
        """Criar repositório de autotrade configs PostgreSQL (singleton)"""
        cache_key = "autotrade_postgresql"

        if cache_key not in RepositoryFactory._instances:
            RepositoryFactory._instances[cache_key] = PostgresAutotradeRepository(
                config.get("POSTGRES_HOST", "localhost"),
                config.get("POSTGRES_PORT", 5432),
                config.get("POSTGRES_DB", "openob"),
                config.get("POSTGRES_USER", "openob_user"),
                config.get("POSTGRES_PASSWORD", "")
            )

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    async def close_all():
        """Fechar todos os pools de conexão"""
        for instance in RepositoryFactory._instances.values():
            if hasattr(instance, 'close'):
                await instance.close()
        RepositoryFactory._instances.clear()
