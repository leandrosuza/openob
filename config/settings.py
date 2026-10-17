"""Configurações centralizadas"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()




class Settings:
    """Configurações centralizadas"""

    # Database
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    SQLITE_PATH = os.getenv("SQLITE_PATH", "data/openob_ticks.db")

    # Monitor
    MONITOR_TOP_ASSETS = int(os.getenv("MONITOR_TOP_ASSETS", "5"))

    # PocketOption
    POCKETOPTION_MONITOR_SSID = os.getenv("POCKETOPTION_MONITOR_SSID")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")




    @classmethod
    def get_log_level(cls) -> int:
        """Obter nível de log como int"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
            "FULL": logging.DEBUG,
        }
        return level_map.get(cls.LOG_LEVEL.upper(), logging.INFO)




    @classmethod
    def to_dict(cls) -> dict:
        """Converter para dicionário"""
        return {
            "DATABASE_TYPE": cls.DATABASE_TYPE,
            "SQLITE_PATH": cls.SQLITE_PATH,
            "MONITOR_TOP_ASSETS": cls.MONITOR_TOP_ASSETS,
            "POCKETOPTION_MONITOR_SSID": cls.POCKETOPTION_MONITOR_SSID,
            "LOG_LEVEL": cls.LOG_LEVEL,
        }
