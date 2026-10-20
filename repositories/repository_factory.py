"""Factory para criação de repositórios"""

from typing import Dict
from repositories.interfaces.tick_repository_interface import TickRepositoryInterface
from repositories.interfaces.user_repository_interface import UserRepositoryInterface
from repositories.interfaces.plan_repository_interface import PlanRepositoryInterface
from repositories.interfaces.subscription_repository_interface import SubscriptionRepositoryInterface
from repositories.interfaces.transaction_repository_interface import TransactionRepositoryInterface
from repositories.sqlite.sqlite_tick_repository import SQLiteTickRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from repositories.sqlite.sqlite_plan_repository import SQLitePlanRepository
from repositories.sqlite.sqlite_subscription_repository import SQLiteSubscriptionRepository
from repositories.sqlite.sqlite_transaction_repository import SQLiteTransactionRepository
from repositories.postgresql.postgres_tick_repository import PostgresTickRepository
from repositories.postgresql.postgres_user_repository import PostgresUserRepository
from repositories.postgresql.postgres_plan_repository import PostgresPlanRepository
from repositories.postgresql.postgres_subscription_repository import PostgresSubscriptionRepository
from repositories.postgresql.postgres_transaction_repository import PostgresTransactionRepository


class RepositoryFactory:
    """Fábrica de repositórios com singleton para evitar conflitos de lock"""

    _instances: Dict[str, any] = {}

    @staticmethod
    def create_tick_repository(config: Dict) -> TickRepositoryInterface:
        """Criar repositório de ticks baseado em config (singleton)"""
        db_type = config.get("DATABASE_TYPE", "sqlite")
        cache_key = f"tick_{db_type}"

        if cache_key not in RepositoryFactory._instances:
            if db_type == "sqlite":
                RepositoryFactory._instances[cache_key] = SQLiteTickRepository(config.get("SQLITE_PATH", "data/openob.db"))
            elif db_type == "postgresql":
                RepositoryFactory._instances[cache_key] = PostgresTickRepository(
                    config.get("POSTGRES_HOST", "localhost"),
                    config.get("POSTGRES_PORT", 5432),
                    config.get("POSTGRES_DB", "openob"),
                    config.get("POSTGRES_USER", "openob_user"),
                    config.get("POSTGRES_PASSWORD", "")
                )
            else:
                raise ValueError(f"Database type not supported: {db_type}")

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_user_repository(config: Dict) -> UserRepositoryInterface:
        """Criar repositório de usuários baseado em config (singleton)"""
        db_type = config.get("DATABASE_TYPE", "sqlite")
        cache_key = f"user_{db_type}"

        if cache_key not in RepositoryFactory._instances:
            if db_type == "sqlite":
                RepositoryFactory._instances[cache_key] = SQLiteUserRepository(config.get("SQLITE_PATH", "data/openob.db"))
            elif db_type == "postgresql":
                RepositoryFactory._instances[cache_key] = PostgresUserRepository(
                    config.get("POSTGRES_HOST", "localhost"),
                    config.get("POSTGRES_PORT", 5432),
                    config.get("POSTGRES_DB", "openob"),
                    config.get("POSTGRES_USER", "openob_user"),
                    config.get("POSTGRES_PASSWORD", "")
                )
            else:
                raise ValueError(f"Database type not supported: {db_type}")

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_plan_repository(config: Dict) -> PlanRepositoryInterface:
        """Criar repositório de planos baseado em config (singleton)"""
        db_type = config.get("DATABASE_TYPE", "sqlite")
        cache_key = f"plan_{db_type}"

        if cache_key not in RepositoryFactory._instances:
            if db_type == "sqlite":
                RepositoryFactory._instances[cache_key] = SQLitePlanRepository(config.get("SQLITE_PATH", "data/openob.db"))
            elif db_type == "postgresql":
                RepositoryFactory._instances[cache_key] = PostgresPlanRepository(
                    config.get("POSTGRES_HOST", "localhost"),
                    config.get("POSTGRES_PORT", 5432),
                    config.get("POSTGRES_DB", "openob"),
                    config.get("POSTGRES_USER", "openob_user"),
                    config.get("POSTGRES_PASSWORD", "")
                )
            else:
                raise ValueError(f"Database type not supported: {db_type}")

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_subscription_repository(config: Dict) -> SubscriptionRepositoryInterface:
        """Criar repositório de subscriptions baseado em config (singleton)"""
        db_type = config.get("DATABASE_TYPE", "sqlite")
        cache_key = f"subscription_{db_type}"

        if cache_key not in RepositoryFactory._instances:
            if db_type == "sqlite":
                RepositoryFactory._instances[cache_key] = SQLiteSubscriptionRepository(config.get("SQLITE_PATH", "data/openob.db"))
            elif db_type == "postgresql":
                RepositoryFactory._instances[cache_key] = PostgresSubscriptionRepository(
                    config.get("POSTGRES_HOST", "localhost"),
                    config.get("POSTGRES_PORT", 5432),
                    config.get("POSTGRES_DB", "openob"),
                    config.get("POSTGRES_USER", "openob_user"),
                    config.get("POSTGRES_PASSWORD", "")
                )
            else:
                raise ValueError(f"Database type not supported: {db_type}")

        return RepositoryFactory._instances[cache_key]

    @staticmethod
    def create_transaction_repository(config: Dict) -> TransactionRepositoryInterface:
        """Criar repositório de transações baseado em config (singleton)"""
        db_type = config.get("DATABASE_TYPE", "sqlite")
        cache_key = f"transaction_{db_type}"

        if cache_key not in RepositoryFactory._instances:
            if db_type == "sqlite":
                RepositoryFactory._instances[cache_key] = SQLiteTransactionRepository(config.get("SQLITE_PATH", "data/openob.db"))
            elif db_type == "postgresql":
                RepositoryFactory._instances[cache_key] = PostgresTransactionRepository(
                    config.get("POSTGRES_HOST", "localhost"),
                    config.get("POSTGRES_PORT", 5432),
                    config.get("POSTGRES_DB", "openob"),
                    config.get("POSTGRES_USER", "openob_user"),
                    config.get("POSTGRES_PASSWORD", "")
                )
            else:
                raise ValueError(f"Database type not supported: {db_type}")

        return RepositoryFactory._instances[cache_key]
