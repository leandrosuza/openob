"""Configurações centralizadas"""

import os
import logging
from dotenv import load_dotenv
from core.exceptions import ConfigurationError

load_dotenv()


class Settings:
    """Configurações centralizadas"""

    # Database
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    SQLITE_PATH = os.getenv("SQLITE_PATH", "data/openob_ticks.db")
    SQLITE_USERS_PATH = os.getenv("SQLITE_USERS_PATH", "data/openob_users.db")

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
        }
        return level_map.get(cls.LOG_LEVEL.upper(), logging.INFO)




    @classmethod
    def to_dict(cls) -> dict:
        """Converter para dicionário"""
        return {
            "DATABASE_TYPE": cls.DATABASE_TYPE,
            "SQLITE_PATH": cls.SQLITE_PATH,
            "SQLITE_USERS_PATH": cls.SQLITE_USERS_PATH,
            "MONITOR_TOP_ASSETS": cls.MONITOR_TOP_ASSETS,
            "POCKETOPTION_MONITOR_SSID": cls.POCKETOPTION_MONITOR_SSID,
            "LOG_LEVEL": cls.LOG_LEVEL,
        }




    @classmethod
    def validate(cls) -> list:
        """Validar configurações e retornar lista de erros"""
        errors = []

        if not cls.POCKETOPTION_MONITOR_SSID:
            errors.append("POCKETOPTION_MONITOR_SSID não definido")

        if cls.DATABASE_TYPE not in ["sqlite"]:
            errors.append(f"DATABASE_TYPE inválido: {cls.DATABASE_TYPE}")

        if cls.MONITOR_TOP_ASSETS < 1 or cls.MONITOR_TOP_ASSETS > 50:
            errors.append(f"MONITOR_TOP_ASSETS deve estar entre 1 e 50")

        if cls.LOG_LEVEL.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"LOG_LEVEL inválido: {cls.LOG_LEVEL}")

        return errors
