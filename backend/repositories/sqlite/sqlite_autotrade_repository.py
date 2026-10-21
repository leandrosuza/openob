"""Implementação SQLite do repositório de autotrade configs"""

import os
import sqlite3
import asyncio
import threading
from datetime import datetime
from typing import Optional, List
from repositories.interfaces.autotrade_repository_interface import AutotradeRepositoryInterface
from models.autotrade import AutotradeConfig
from core.logger import get_logger, LoggerConfig


logger = get_logger(__name__)
database_logger = LoggerConfig.get_database_logger()

# Lock global compartilhado entre todos os repositórios SQLite para evitar deadlocks
GLOBAL_DB_LOCK = threading.Lock()


class SQLiteAutotradeRepository(AutotradeRepositoryInterface):
    """Repositório SQLite - Implementação com asyncio.to_thread()"""

    def __init__(self, db_path: str = "data/openob.db"):
        self.db_path = db_path
        self.conn = None
        self._lock = threading.Lock()
        self._initialize_db_sync()
        logger.info(f"SQLite AutotradeRepository inicializado: {db_path}")

    def _initialize_db_sync(self):
        """Setup inicial do banco (síncrono)"""
        with GLOBAL_DB_LOCK:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=-64000")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            self.conn.execute("PRAGMA busy_timeout=5000")

            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS autotrade_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                strategy_name TEXT NOT NULL,
                parameters TEXT NOT NULL,
                amount REAL DEFAULT 5.0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON autotrade_configs(user_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy_name ON autotrade_configs(strategy_name)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON autotrade_configs(is_active)")

            self.conn.commit()
            logger.info("Tabela autotrade_configs criada com sucesso")
            database_logger.info("Tabela autotrade_configs criada")

    def _config_from_row(self, row: tuple) -> AutotradeConfig:
        """Converter row do banco para modelo AutotradeConfig"""
        import json
        return AutotradeConfig(
            id=row[0],
            user_id=row[1],
            strategy_name=row[2],
            parameters=json.loads(row[3]),
            amount=row[4],
            is_active=bool(row[5]),
            created_at=datetime.fromisoformat(row[6]) if row[6] else None,
            updated_at=datetime.fromisoformat(row[7]) if row[7] else None
        )

    async def create(self, config: AutotradeConfig) -> AutotradeConfig:
        """Criar config e retornar com ID"""
        try:
            return await asyncio.to_thread(self._create_sync, config)
        except Exception as e:
            logger.error(f"Erro ao criar config: {e}")
            raise DatabaseError(f"Falha ao criar config: {e}")

    def _create_sync(self, config: AutotradeConfig) -> AutotradeConfig:
        """Criar config (síncrono)"""
        import json
        with GLOBAL_DB_LOCK:
            cursor = self.conn.execute(
                "INSERT INTO autotrade_configs (user_id, strategy_name, parameters, amount, is_active) VALUES (?, ?, ?, ?, ?)",
                (config.user_id, config.strategy_name, json.dumps(config.parameters), config.amount, config.is_active)
            )
            self.conn.commit()

            config_id = cursor.lastrowid
            cursor = self.conn.execute("SELECT * FROM autotrade_configs WHERE id = ?", (config_id,))
            row = cursor.fetchone()
            return self._config_from_row(row)

    async def get_by_user(self, user_id: int) -> Optional[AutotradeConfig]:
        """Obter config por user_id"""
        try:
            return await asyncio.to_thread(self._get_by_user_sync, user_id)
        except Exception as e:
            logger.error(f"Erro ao buscar config por user_id: {e}")
            raise DatabaseError(f"Falha ao buscar config: {e}")

    def _get_by_user_sync(self, user_id: int) -> Optional[AutotradeConfig]:
        """Obter config por user_id (síncrono)"""
        with GLOBAL_DB_LOCK:
            cursor = self.conn.execute(
                "SELECT * FROM autotrade_configs WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
            return self._config_from_row(row) if row else None

    async def update(self, config: AutotradeConfig) -> AutotradeConfig:
        """Atualizar config"""
        try:
            return await asyncio.to_thread(self._update_sync, config)
        except Exception as e:
            logger.error(f"Erro ao atualizar config: {e}")
            raise DatabaseError(f"Falha ao atualizar config: {e}")

    def _update_sync(self, config: AutotradeConfig) -> AutotradeConfig:
        """Atualizar config (síncrono)"""
        import json
        with GLOBAL_DB_LOCK:
            self.conn.execute(
                """UPDATE autotrade_configs SET
                   strategy_name = ?,
                   parameters = ?,
                   amount = ?,
                   is_active = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (config.strategy_name, json.dumps(config.parameters), config.amount, config.is_active, config.id)
            )
            self.conn.commit()
            cursor = self.conn.execute("SELECT * FROM autotrade_configs WHERE id = ?", (config.id,))
            row = cursor.fetchone()
            return self._config_from_row(row)

    async def delete(self, user_id: int) -> bool:
        """Deletar config por user_id"""
        try:
            await asyncio.to_thread(self._delete_sync, user_id)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar config: {e}")
            raise DatabaseError(f"Falha ao deletar config: {e}")

    def _delete_sync(self, user_id: int):
        """Deletar config (síncrono)"""
        with GLOBAL_DB_LOCK:
            self.conn.execute("DELETE FROM autotrade_configs WHERE user_id = ?", (user_id,))
            self.conn.commit()

    async def get_active_strategies(self) -> List[AutotradeConfig]:
        """Obter todas as configs ativas"""
        try:
            return await asyncio.to_thread(self._get_active_strategies_sync)
        except Exception as e:
            logger.error(f"Erro ao buscar configs ativas: {e}")
            raise DatabaseError(f"Falha ao buscar configs ativas: {e}")

    def _get_active_strategies_sync(self) -> List[AutotradeConfig]:
        """Obter configs ativas (síncrono)"""
        with GLOBAL_DB_LOCK:
            cursor = self.conn.execute(
                "SELECT * FROM autotrade_configs WHERE is_active = 1"
            )
            rows = cursor.fetchall()
            return [self._config_from_row(row) for row in rows]

    async def close(self):
        """Fechar conexão"""
        if self.conn:
            self.conn.close()
            logger.info("SQLite AutotradeRepository fechado")


class DatabaseError(Exception):
    """Exceção personalizada para erros de banco de dados"""
    pass
