"""Implementação SQLite do repositório de usuários"""

import os
import sqlite3
import asyncio
import threading
import bcrypt
from datetime import datetime, timezone
from typing import Optional, List
from repositories.interfaces.user_repository_interface import UserRepositoryInterface
from models.user import User
from core.logger import get_logger, LoggerConfig


logger = get_logger(__name__)
database_logger = LoggerConfig.get_database_logger()


class SQLiteUserRepository(UserRepositoryInterface):
    """Repositório SQLite - Implementação com asyncio.to_thread()"""

    def __init__(self, db_path: str = "data/openob.db"):
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
                password_hash TEXT NOT NULL,
                ssid_demo TEXT NOT NULL UNIQUE,
                ssid_real TEXT UNIQUE,
                plan_id INTEGER,
                current_subscription_id INTEGER,
                plan_expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                balance REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_username ON users(username)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON users(email)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ssid_demo ON users(ssid_demo)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ssid_real ON users(ssid_real)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_id ON users(plan_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_current_subscription ON users(current_subscription_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON users(is_active)")

            self.conn.commit()
            logger.info("Tabela users criada com sucesso")
            database_logger.info("Tabela users criada")

            self._migrate_table()

    def _migrate_table(self):
        """Migrar tabela adicionando colunas novas se não existirem"""
        with self._lock:
            try:
                self.conn.execute("ALTER TABLE users ADD COLUMN current_subscription_id INTEGER")
                logger.info("Migração: coluna current_subscription_id adicionada")
            except sqlite3.OperationalError:
                pass

            try:
                self.conn.execute("ALTER TABLE users ADD COLUMN plan_expires_at DATETIME")
                logger.info("Migração: coluna plan_expires_at adicionada")
            except sqlite3.OperationalError:
                pass

            self.conn.commit()

    def _user_from_row(self, row: tuple) -> User:
        """Converter row do banco para modelo User"""
        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            password_hash=row[3],
            ssid_demo=row[4],
            ssid_real=row[5],
            plan_id=row[6],
            current_subscription_id=row[7] if len(row) > 7 else None,
            plan_expires_at=datetime.fromisoformat(row[8]) if len(row) > 8 and row[8] else None,
            is_active=bool(row[9] if len(row) > 9 else row[7]),
            balance=row[10] if len(row) > 10 else row[8],
            created_at=datetime.fromisoformat(row[11] if len(row) > 11 else row[9]) if len(row) > 11 and row[11] else None,
            updated_at=datetime.fromisoformat(row[12] if len(row) > 12 else row[10]) if len(row) > 12 and row[12] else None
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de senha usando bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

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
                "INSERT INTO users (username, email, password_hash, ssid_demo, ssid_real, plan_id, current_subscription_id, plan_expires_at, is_active, balance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user.username, user.email, user.password_hash, user.ssid_demo, user.ssid_real, user.plan_id, user.current_subscription_id, user.plan_expires_at.isoformat() if user.plan_expires_at else None, user.is_active, user.balance)
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

    async def get_by_ssid_demo(self, ssid_demo: str) -> Optional[User]:
        """Obter usuário por SSID Demo"""
        try:
            return await asyncio.to_thread(self._get_by_ssid_demo_sync, ssid_demo)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por SSID Demo: {e}")
            raise DatabaseError(f"Falha ao buscar usuário: {e}")

    def _get_by_ssid_demo_sync(self, ssid_demo: str) -> Optional[User]:
        """Obter usuário por SSID Demo (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM users WHERE ssid_demo = ?", (ssid_demo,)
            )
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def get_by_ssid_real(self, ssid_real: str) -> Optional[User]:
        """Obter usuário por SSID Real"""
        try:
            return await asyncio.to_thread(self._get_by_ssid_real_sync, ssid_real)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por SSID Real: {e}")
            raise DatabaseError(f"Falha ao buscar usuário: {e}")

    def _get_by_ssid_real_sync(self, ssid_real: str) -> Optional[User]:
        """Obter usuário por SSID Real (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM users WHERE ssid_real = ?", (ssid_real,)
            )
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def verify_password(self, username: str, password: str) -> bool:
        """Verificar senha do usuário"""
        try:
            return await asyncio.to_thread(self._verify_password_sync, username, password)
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            raise DatabaseError(f"Falha ao verificar senha: {e}")

    def _verify_password_sync(self, username: str, password: str) -> bool:
        """Verificar senha (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT password_hash FROM users WHERE username = ?", (username,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            password_hash = row[0]
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """Atualizar senha do usuário"""
        try:
            await asyncio.to_thread(self._update_password_sync, user_id, new_password)
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar senha: {e}")
            raise DatabaseError(f"Falha ao atualizar senha: {e}")

    def _update_password_sync(self, user_id: int, new_password: str):
        """Atualizar senha (síncrono)"""
        with self._lock:
            password_hash = SQLiteUserRepository.hash_password(new_password)
            self.conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (password_hash, user_id)
            )
            self.conn.commit()

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
                   password_hash = ?, 
                   ssid_demo = ?, 
                   ssid_real = ?, 
                   plan_id = ?, 
                   current_subscription_id = ?, 
                   plan_expires_at = ?, 
                   is_active = ?, 
                   balance = ?, 
                   updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (user.username, user.email, user.password_hash, user.ssid_demo, user.ssid_real, user.plan_id, user.current_subscription_id, user.plan_expires_at.isoformat() if user.plan_expires_at else None, user.is_active, user.balance, user.id)
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
