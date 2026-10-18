"""Factory para criação de repositórios"""

from typing import Dict
from repositories.interfaces.tick_repository_interface import TickRepositoryInterface
from repositories.sqlite.sqlite_tick_repository import SQLiteTickRepository


class RepositoryFactory:
    """Fábrica de repositórios"""

    @staticmethod
    def create_tick_repository(config: Dict) -> TickRepositoryInterface:
        """Criar repositório de ticks baseado em config"""
        db_type = config.get("DATABASE_TYPE", "sqlite")

        if db_type == "sqlite":
            return SQLiteTickRepository(config.get("SQLITE_PATH", "data/openob_ticks.db"))

        # Futuro:
        # elif db_type == "redis":
        #     from repositories.redis.redis_tick_repository import RedisTickRepository
        #     return RedisTickRepository(config["REDIS_HOST"])
        # elif db_type == "influxdb":
        #     from repositories.influxdb.influx_tick_repository import InfluxTickRepository
        #     return InfluxTickRepository(config["INFLUX_URL"], config["INFLUX_TOKEN"])

        else:
            raise ValueError(f"Database type not supported: {db_type}")
