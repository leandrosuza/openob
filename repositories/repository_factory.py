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


class RepositoryFactory:
    """Fábrica de repositórios"""

    @staticmethod
    def create_tick_repository(config: Dict) -> TickRepositoryInterface:
        """Criar repositório de ticks baseado em config"""
        db_type = config.get("DATABASE_TYPE", "sqlite")

        if db_type == "sqlite":
            return SQLiteTickRepository(config.get("SQLITE_PATH", "data/openob.db"))

        else:
            raise ValueError(f"Database type not supported: {db_type}")

    @staticmethod
    def create_user_repository(config: Dict) -> UserRepositoryInterface:
        """Criar repositório de usuários baseado em config"""
        db_type = config.get("DATABASE_TYPE", "sqlite")

        if db_type == "sqlite":
            return SQLiteUserRepository(config.get("SQLITE_PATH", "data/openob.db"))

        else:
            raise ValueError(f"Database type not supported: {db_type}")

    @staticmethod
    def create_plan_repository(config: Dict) -> PlanRepositoryInterface:
        """Criar repositório de planos baseado em config"""
        db_type = config.get("DATABASE_TYPE", "sqlite")

        if db_type == "sqlite":
            return SQLitePlanRepository(config.get("SQLITE_PATH", "data/openob.db"))

        else:
            raise ValueError(f"Database type not supported: {db_type}")

    @staticmethod
    def create_subscription_repository(config: Dict) -> SubscriptionRepositoryInterface:
        """Criar repositório de subscriptions baseado em config"""
        db_type = config.get("DATABASE_TYPE", "sqlite")

        if db_type == "sqlite":
            return SQLiteSubscriptionRepository(config.get("SQLITE_PATH", "data/openob.db"))

        else:
            raise ValueError(f"Database type not supported: {db_type}")

    @staticmethod
    def create_transaction_repository(config: Dict) -> TransactionRepositoryInterface:
        """Criar repositório de transações baseado em config"""
        db_type = config.get("DATABASE_TYPE", "sqlite")

        if db_type == "sqlite":
            return SQLiteTransactionRepository(config.get("SQLITE_PATH", "data/openob.db"))

        else:
            raise ValueError(f"Database type not supported: {db_type}")
