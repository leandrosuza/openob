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
    MONITOR_PAYOUT_INTERVAL = int(os.getenv("MONITOR_PAYOUT_INTERVAL", "5"))
    MONITOR_ASSETS_UPDATE_INTERVAL = int(os.getenv("MONITOR_ASSETS_UPDATE_INTERVAL", "10"))

    # PocketOption
    POCKETOPTION_MONITOR_SSID = os.getenv("POCKETOPTION_MONITOR_SSID")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key-in-production")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

    # Rate Limiting
    RATE_LIMIT_REGISTER = os.getenv("RATE_LIMIT_REGISTER", "5/minute")
    RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "10/minute")
    RATE_LIMIT_REFRESH = os.getenv("RATE_LIMIT_REFRESH", "20/minute")
    RATE_LIMIT_HEALTH = os.getenv("RATE_LIMIT_HEALTH", "100/minute")
    RATE_LIMIT_SUBSCRIPTION = os.getenv("RATE_LIMIT_SUBSCRIPTION", "10/minute")
    RATE_LIMIT_PAYMENT = os.getenv("RATE_LIMIT_PAYMENT", "5/minute")

    # Subscription
    PLAN_DAILY_PRICE = float(os.getenv("PLAN_DAILY_PRICE", "5.00"))
    PLAN_WEEKLY_PRICE = float(os.getenv("PLAN_WEEKLY_PRICE", "25.00"))
    PLAN_MONTHLY_PRICE = float(os.getenv("PLAN_MONTHLY_PRICE", "80.00"))
    GRACE_PERIOD_DAYS = int(os.getenv("GRACE_PERIOD_DAYS", "3"))
    SUBSCRIPTION_CHECK_INTERVAL_HOURS = int(os.getenv("SUBSCRIPTION_CHECK_INTERVAL_HOURS", "1"))

    # Webhook
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
    WEBHOOK_TOLERANCE_SECONDS = int(os.getenv("WEBHOOK_TOLERANCE_SECONDS", "300"))

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
            "MONITOR_PAYOUT_INTERVAL": cls.MONITOR_PAYOUT_INTERVAL,
            "MONITOR_ASSETS_UPDATE_INTERVAL": cls.MONITOR_ASSETS_UPDATE_INTERVAL,
            "POCKETOPTION_MONITOR_SSID": cls.POCKETOPTION_MONITOR_SSID,
            "JWT_SECRET_KEY": cls.JWT_SECRET_KEY,
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": cls.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS": cls.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
            "CORS_ORIGINS": cls.CORS_ORIGINS,
            "RATE_LIMIT_REGISTER": cls.RATE_LIMIT_REGISTER,
            "RATE_LIMIT_LOGIN": cls.RATE_LIMIT_LOGIN,
            "RATE_LIMIT_REFRESH": cls.RATE_LIMIT_REFRESH,
            "RATE_LIMIT_HEALTH": cls.RATE_LIMIT_HEALTH,
            "RATE_LIMIT_SUBSCRIPTION": cls.RATE_LIMIT_SUBSCRIPTION,
            "RATE_LIMIT_PAYMENT": cls.RATE_LIMIT_PAYMENT,
            "PLAN_DAILY_PRICE": cls.PLAN_DAILY_PRICE,
            "PLAN_WEEKLY_PRICE": cls.PLAN_WEEKLY_PRICE,
            "PLAN_MONTHLY_PRICE": cls.PLAN_MONTHLY_PRICE,
            "GRACE_PERIOD_DAYS": cls.GRACE_PERIOD_DAYS,
            "SUBSCRIPTION_CHECK_INTERVAL_HOURS": cls.SUBSCRIPTION_CHECK_INTERVAL_HOURS,
            "WEBHOOK_SECRET": cls.WEBHOOK_SECRET,
            "WEBHOOK_TOLERANCE_SECONDS": cls.WEBHOOK_TOLERANCE_SECONDS,
            "LOG_LEVEL": cls.LOG_LEVEL,
        }




    @classmethod
    def validate(cls) -> list:
        """Validar configurações e retornar lista de erros"""
        errors = []

        if not cls.POCKETOPTION_MONITOR_SSID:
            errors.append("POCKETOPTION_MONITOR_SSID não definido")

        if not cls.JWT_SECRET_KEY or cls.JWT_SECRET_KEY == "change-this-secret-key-in-production":
            errors.append("JWT_SECRET_KEY não definido ou é valor padrão - MUDAR EM PRODUÇÃO")

        if cls.JWT_ACCESS_TOKEN_EXPIRE_MINUTES < 1 or cls.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 1440:
            errors.append(f"JWT_ACCESS_TOKEN_EXPIRE_MINUTES deve estar entre 1 e 1440")

        if cls.JWT_REFRESH_TOKEN_EXPIRE_DAYS < 1 or cls.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 365:
            errors.append(f"JWT_REFRESH_TOKEN_EXPIRE_DAYS deve estar entre 1 e 365")

        if not cls.CORS_ORIGINS:
            errors.append("CORS_ORIGINS não definido")

        if cls.DATABASE_TYPE not in ["sqlite"]:
            errors.append(f"DATABASE_TYPE inválido: {cls.DATABASE_TYPE}")

        if cls.MONITOR_TOP_ASSETS < 1 or cls.MONITOR_TOP_ASSETS > 50:
            errors.append(f"MONITOR_TOP_ASSETS deve estar entre 1 e 50")

        if cls.LOG_LEVEL.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"LOG_LEVEL inválido: {cls.LOG_LEVEL}")

        if cls.PLAN_DAILY_PRICE < 0:
            errors.append(f"PLAN_DAILY_PRICE deve ser >= 0")

        if cls.PLAN_WEEKLY_PRICE < 0:
            errors.append(f"PLAN_WEEKLY_PRICE deve ser >= 0")

        if cls.PLAN_MONTHLY_PRICE < 0:
            errors.append(f"PLAN_MONTHLY_PRICE deve ser >= 0")

        if cls.GRACE_PERIOD_DAYS < 0:
            errors.append(f"GRACE_PERIOD_DAYS deve ser >= 0")

        if cls.SUBSCRIPTION_CHECK_INTERVAL_HOURS < 1:
            errors.append(f"SUBSCRIPTION_CHECK_INTERVAL_HOURS deve ser >= 1")

        if cls.WEBHOOK_TOLERANCE_SECONDS < 0:
            errors.append(f"WEBHOOK_TOLERANCE_SECONDS deve ser >= 0")

        return errors
