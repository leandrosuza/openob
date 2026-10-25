"""Logging configuration for OpenOB"""

import logging
import sys
from typing import Optional
from pathlib import Path


class LoggerConfig:
    """Configuração centralizada de logging"""

    _configured = False
    _subscription_logger = None
    _payment_logger = None
    _security_logger = None
    _database_logger = None
    _strategy_logger = None


    @classmethod
    def setup(
        cls,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        format_string: Optional[str] = None
    ):
        """Configurar logging globalmente"""
        if cls._configured:
            return

        if format_string is None:
            format_string = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

        formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

        handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

        # File handler (opcional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        # Configurar root logger
        logging.basicConfig(
            level=level,
            handlers=handlers,
            force=True
        )

        cls._configured = True

    @classmethod
    def setup_subscription_logger(cls, log_file: str = "logs/plans/subscriptions.log"):
        """Configurar logger específico para subscriptions"""
        if cls._subscription_logger:
            return cls._subscription_logger

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        cls._subscription_logger = logging.getLogger("subscription")
        cls._subscription_logger.setLevel(logging.INFO)
        subscription_handler = logging.FileHandler(log_file)
        subscription_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        cls._subscription_logger.addHandler(subscription_handler)

        return cls._subscription_logger

    @classmethod
    def setup_payment_logger(cls, log_file: str = "logs/plans/payments.log"):
        """Configurar logger específico para pagamentos"""
        if cls._payment_logger:
            return cls._payment_logger

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        cls._payment_logger = logging.getLogger("payment")
        cls._payment_logger.setLevel(logging.INFO)
        payment_handler = logging.FileHandler(log_file)
        payment_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        cls._payment_logger.addHandler(payment_handler)

        return cls._payment_logger

    @classmethod
    def setup_security_logger(cls, log_file: str = "logs/security.log"):
        """Configurar logger específico para segurança"""
        if cls._security_logger:
            return cls._security_logger

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        cls._security_logger = logging.getLogger("security")
        cls._security_logger.setLevel(logging.WARNING)
        security_handler = logging.FileHandler(log_file)
        security_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        cls._security_logger.addHandler(security_handler)

        return cls._security_logger

    @classmethod
    def get_subscription_logger(cls) -> logging.Logger:
        """Obter logger de subscriptions"""
        if not cls._subscription_logger:
            cls.setup_subscription_logger()
        return cls._subscription_logger

    @classmethod
    def get_payment_logger(cls) -> logging.Logger:
        """Obter logger de pagamentos"""
        if not cls._payment_logger:
            cls.setup_payment_logger()
        return cls._payment_logger

    @classmethod
    def get_security_logger(cls) -> logging.Logger:
        """Obter logger de segurança"""
        if not cls._security_logger:
            cls.setup_security_logger()
        return cls._security_logger

    @classmethod
    def setup_database_logger(cls, log_file: str = "logs/database.log"):
        """Configurar logger específico para database"""
        if cls._database_logger:
            return cls._database_logger

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        cls._database_logger = logging.getLogger("database")
        cls._database_logger.setLevel(logging.INFO)
        database_handler = logging.FileHandler(log_file)
        database_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        cls._database_logger.addHandler(database_handler)

        return cls._database_logger

    @classmethod
    def get_database_logger(cls) -> logging.Logger:
        """Obter logger de database"""
        if not cls._database_logger:
            cls.setup_database_logger()
        return cls._database_logger

    @classmethod
    def setup_strategy_logger(cls, log_file: str = "logs/strategy/strategy.log"):
        """Configurar logger específico para sinais finais de estratégia"""
        if cls._strategy_logger:
            return cls._strategy_logger

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        cls._strategy_logger = logging.getLogger("strategy.signals")
        cls._strategy_logger.setLevel(logging.INFO)
        cls._strategy_logger.propagate = False  # Evitar propagação para logger raiz
        strategy_handler = logging.FileHandler(log_file)
        strategy_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        cls._strategy_logger.addHandler(strategy_handler)

        return cls._strategy_logger

    @classmethod
    def get_strategy_logger(cls) -> logging.Logger:
        """Obter logger de estratégia"""
        if not cls._strategy_logger:
            cls.setup_strategy_logger()
        return cls._strategy_logger




def get_logger(name: str) -> logging.Logger:
    """Obter logger configurado para um módulo"""
    if not LoggerConfig._configured:
        LoggerConfig.setup()
    return logging.getLogger(name)
