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
    SQLITE_PATH = os.getenv("SQLITE_PATH", "data/openob.db")

    # Monitor
    MONITOR_TOP_ASSETS = int(os.getenv("MONITOR_TOP_ASSETS", "5"))

    # PocketOption
    POCKETOPTION_ENV = os.getenv("POCKETOPTION_ENV", "DEMO")
    POCKETOPTION_PAYOUT_SSID_DEMO = os.getenv("POCKETOPTION_PAYOUT_SSID_DEMO")
    POCKETOPTION_PAYOUT_SSID_REAL = os.getenv("POCKETOPTION_PAYOUT_SSID_REAL")
    POCKETOPTION_MONITOR_SSID_DEMO = os.getenv("POCKETOPTION_MONITOR_SSID_DEMO")
    POCKETOPTION_MONITOR_SSID_REAL = os.getenv("POCKETOPTION_MONITOR_SSID_REAL")

    @classmethod
    def get_payout_ssid(cls) -> str:
        """Obter SSID de payout baseado no ambiente"""
        if cls.POCKETOPTION_ENV == "REAL":
            return cls.POCKETOPTION_PAYOUT_SSID_REAL
        return cls.POCKETOPTION_PAYOUT_SSID_DEMO

    @classmethod
    def get_monitor_ssid(cls) -> str:
        """Obter SSID de monitoramento baseado no ambiente"""
        if cls.POCKETOPTION_ENV == "REAL":
            return cls.POCKETOPTION_MONITOR_SSID_REAL
        return cls.POCKETOPTION_MONITOR_SSID_DEMO

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
            "MONITOR_TOP_ASSETS": cls.MONITOR_TOP_ASSETS,
            "POCKETOPTION_ENV": cls.POCKETOPTION_ENV,
            "POCKETOPTION_PAYOUT_SSID_DEMO": cls.POCKETOPTION_PAYOUT_SSID_DEMO,
            "POCKETOPTION_PAYOUT_SSID_REAL": cls.POCKETOPTION_PAYOUT_SSID_REAL,
            "POCKETOPTION_MONITOR_SSID_DEMO": cls.POCKETOPTION_MONITOR_SSID_DEMO,
            "POCKETOPTION_MONITOR_SSID_REAL": cls.POCKETOPTION_MONITOR_SSID_REAL,
            "LOG_LEVEL": cls.LOG_LEVEL,
        }




    @classmethod
    def validate(cls) -> list:
        """Validar configurações e retornar lista de erros"""
        errors = []

        if cls.POCKETOPTION_ENV not in ["DEMO", "REAL"]:
            errors.append(f"POCKETOPTION_ENV inválido: {cls.POCKETOPTION_ENV}")

        if cls.POCKETOPTION_ENV == "DEMO" and not cls.POCKETOPTION_MONITOR_SSID_DEMO:
            errors.append("POCKETOPTION_MONITOR_SSID_DEMO não definido")

        if cls.POCKETOPTION_ENV == "REAL" and not cls.POCKETOPTION_MONITOR_SSID_REAL:
            errors.append("POCKETOPTION_MONITOR_SSID_REAL não definido")

        if cls.DATABASE_TYPE not in ["sqlite"]:
            errors.append(f"DATABASE_TYPE inválido: {cls.DATABASE_TYPE}")

        if cls.MONITOR_TOP_ASSETS < 1 or cls.MONITOR_TOP_ASSETS > 50:
            errors.append(f"MONITOR_TOP_ASSETS deve estar entre 1 e 50")

        if cls.LOG_LEVEL.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"LOG_LEVEL inválido: {cls.LOG_LEVEL}")

        return errors
