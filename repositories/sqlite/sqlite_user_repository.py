"""Implementação SQLite do repositório de usuários"""

import os
import sqlite3
import asyncio
import threading
from datetime import datetime, timezone
from typing import Optional, List
from repositories.interfaces.user_repository_interface import UserRepositoryInterface
from models.user import User
from core.logger import get_logger
from core.exceptions import DatabaseError


logger = get_logger(__name__)


class SQLiteUserRepository(UserRepositoryInterface):
    """Repositório SQLite - Implementação com asyncio.to_thread()"""

    def __init__(self, db_path: str = "data/openob_users.db"):
        self.db_path = db_path
        self.conn = None
        self._lock = threading.Lock()
        self._initialize_db_sync()
        logger.info(f"SQLite UserRepository inicializado: {db_path}")

    def _initialize_db_sync(self):
        """Setup inicial do banco (síncrono)"""
        with self._lock:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=-64000")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            self.conn.execute("PRAGMA busy_timeout=5000")

            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                ssid TEXT NOT NULL UNIQUE,
                plan_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                balance REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_username ON users(username)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON users(email)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ssid ON users(ssid)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_id ON users(plan_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON users(is_active)")

            self.conn.commit()
            logger.info("Tabela users criada com sucesso")

    def _user_from_row(self, row: tuple) -> User:
        """Converter row do banco para modelo User"""
        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            ssid=row[3],
            plan_id=row[4],
            is_active=bool(row[5]),
            balance=row[6],
            created_at=datetime.fromisoformat(row[7]) if row[7] else None,
            updated_at=datetime.fromisoformat(row[8]) if row[8] else None
        )

    async def create(self, user: User) -> User:
        """Criar usuário e retornar com ID"""
        try:
            return await asyncio.to_thread(self._create_sync, user)
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            raise DatabaseError(f"Falha ao criar usuário: {e}")

    def _create_sync(self, user: User) -> User:
        """Criar usuário (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "INSERT INTO users (username, email, ssid, plan_id, is_active, balance) VALUES (?, ?, ?, ?, ?, ?)",
                (user.username, user.email, user.ssid, user.plan_id, user.is_active, user.balance)
            )
            self.conn.commit()

            user_id = cursor.lastrowid
            cursor = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return self._user_from_row(row)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Obter usuário por ID"""
        try:
            return await asyncio.to_thread(self._get_by_id_sync, user_id)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por ID: {e}")
            raise DatabaseError(f"Falha ao buscar usuário: {e}")

    def _get_by_id_sync(self, user_id: int) -> Optional[User]:
        """Obter usuário por ID (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            )
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Obter usuário por username"""
        try:
            return await asyncio.to_thread(self._get_by_username_sync, username)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por username: {e}")
            raise DatabaseError(f"Falha ao buscar usuário: {e}")

    def _get_by_username_sync(self, username: str) -> Optional[User]:
        """Obter usuário por username (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            )
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Obter usuário por email"""
        try:
            return await asyncio.to_thread(self._get_by_email_sync, email)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por email: {e}")
            raise DatabaseError(f"Falha ao buscar usuário: {e}")

    def _get_by_email_sync(self, email: str) -> Optional[User]:
        """Obter usuário por email (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            )
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def get_by_ssid(self, ssid: str) -> Optional[User]:
        """Obter usuário por SSID"""
        try:
            return await asyncio.to_thread(self._get_by_ssid_sync, ssid)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por SSID: {e}")
            raise DatabaseError(f"Falha ao buscar usuário: {e}")

    def _get_by_ssid_sync(self, ssid: str) -> Optional[User]:
        """Obter usuário por SSID (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM users WHERE ssid = ?", (ssid,)
            )
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def update(self, user: User) -> User:
        """Atualizar usuário"""
        try:
            return await asyncio.to_thread(self._update_sync, user)
        except Exception as e:
            logger.error(f"Erro ao atualizar usuário: {e}")
            raise DatabaseError(f"Falha ao atualizar usuário: {e}")

    def _update_sync(self, user: User) -> User:
        """Atualizar usuário (síncrono)"""
        with self._lock:
            self.conn.execute(
                """UPDATE users SET 
                   username = ?, 
                   email = ?, 
                   ssid = ?, 
                   plan_id = ?, 
                   is_active = ?, 
                   balance = ?, 
                   updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (user.username, user.email, user.ssid, user.plan_id, user.is_active, user.balance, user.id)
            )
            self.conn.commit()
            cursor = self.conn.execute("SELECT * FROM users WHERE id = ?", (user.id,))
            row = cursor.fetchone()
            return self._user_from_row(row)

    async def update_balance(self, user_id: int, balance: float) -> bool:
        """Atualizar saldo do usuário"""
        try:
            await asyncio.to_thread(self._update_balance_sync, user_id, balance)
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar saldo: {e}")
            raise DatabaseError(f"Falha ao atualizar saldo: {e}")

    def _update_balance_sync(self, user_id: int, balance: float):
        """Atualizar saldo (síncrono)"""
        with self._lock:
            self.conn.execute(
                "UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (balance, user_id)
            )
            self.conn.commit()

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Listar todos os usuários"""
        try:
            return await asyncio.to_thread(self._list_all_sync, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar usuários: {e}")
            raise DatabaseError(f"Falha ao listar usuários: {e}")

    def _list_all_sync(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Listar usuários (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [self._user_from_row(row) for row in rows]

    async def delete(self, user_id: int) -> bool:
        """Deletar usuário"""
        try:
            await asyncio.to_thread(self._delete_sync, user_id)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar usuário: {e}")
            raise DatabaseError(f"Falha ao deletar usuário: {e}")

    def _delete_sync(self, user_id: int):
        """Deletar usuário (síncrono)"""
        with self._lock:
            self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.conn.commit()

    async def close(self):
        """Fechar conexão"""
        if self.conn:
            self.conn.close()
            logger.info("SQLite UserRepository fechado")
