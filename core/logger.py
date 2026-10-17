"""Logging configuration for OpenOB"""




import logging
import sys
from typing import Optional
from pathlib import Path




class LoggerConfig:
    """Configuração centralizada de logging"""

    _configured = False




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




def get_logger(name: str) -> logging.Logger:
    """Obter logger configurado para um módulo"""
    if not LoggerConfig._configured:
        LoggerConfig.setup()
    return logging.getLogger(name)
