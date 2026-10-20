"""Factory para criação de repositórios"""

from typing import Dict
from repositories.interfaces.tick_repository_interface import TickRepositoryInterface
from repositories.interfaces.user_repository_interface import UserRepositoryInterface
from repositories.sqlite.sqlite_tick_repository import SQLiteTickRepository
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository


class RepositoryFactory:
    """Fábrica de repositórios"""

    @staticmethod
    def create_tick_repository(config: Dict) -> TickRepositoryInterface:
        """Criar repositório de ticks baseado em config"""
        db_type = config.get("DATABASE_TYPE", "sqlite")

        if db_type == "sqlite":
            return SQLiteTickRepository(config.get("SQLITE_PATH", "data/openob_ticks.db"))

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
