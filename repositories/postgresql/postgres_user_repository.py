"""Repositório PostgreSQL para Users"""

import asyncpg
from datetime import datetime, timezone
from typing import Optional, List
from repositories.interfaces.user_repository_interface import UserRepositoryInterface
from models.user import User
from core.logger import get_logger, LoggerConfig

logger = get_logger(__name__)
database_logger = LoggerConfig.get_database_logger()


class PostgresUserRepository(UserRepositoryInterface):
    """Repositório PostgreSQL - Implementação com asyncpg"""

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool = None
        self._initialized = False

    async def _get_pool(self):
        """Obter pool de conexões"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=2,
                max_size=10
            )
        return self.pool

    async def _initialize_db(self):
        """Setup inicial do banco"""
        if self._initialized:
            return

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    ssid_demo VARCHAR(255),
                    plan_id INTEGER,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    ssid_real VARCHAR(255),
                    current_subscription_id INTEGER,
                    plan_expires_at TIMESTAMP WITH TIME ZONE
                )
            """)
            logger.info("Tabela users criada com sucesso")
            database_logger.info("Tabela users criada")

        self._initialized = True

    async def create(self, user: User) -> User:
        """Criar usuário"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO users (username, email, password_hash, ssid_demo, plan_id,
                is_active, balance, ssid_real, current_subscription_id, plan_expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING *""",
                user.username, user.email, user.password_hash, user.ssid_demo,
                user.plan_id, user.is_active, user.balance, user.ssid_real,
                user.current_subscription_id, user.plan_expires_at
            )
            database_logger.info(f"User criado: id={row['id']}, username={user.username}")
            return self._user_from_row(row)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Obter usuário por ID"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            return self._user_from_row(row) if row else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Obter usuário por username"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
            return self._user_from_row(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Obter usuário por email"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
            return self._user_from_row(row) if row else None

    async def update(self, user: User) -> User:
        """Atualizar usuário"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE users SET username = $1, email = $2, password_hash = $3,
                ssid_demo = $4, plan_id = $5, is_active = $6, balance = $7,
                ssid_real = $8, current_subscription_id = $9, plan_expires_at = $10,
                updated_at = NOW() WHERE id = $11 RETURNING *""",
                user.username, user.email, user.password_hash, user.ssid_demo,
                user.plan_id, user.is_active, user.balance, user.ssid_real,
                user.current_subscription_id, user.plan_expires_at, user.id
            )
            database_logger.info(f"User atualizado: id={user.id}")
            return self._user_from_row(row)

    async def delete(self, user_id: int) -> bool:
        """Deletar usuário (soft delete - desativar)"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE users SET is_active = FALSE WHERE id = $1", user_id
            )
            database_logger.info(f"User desativado: id={user_id}")
            return result == "UPDATE 1"

    async def get_by_ssid_demo(self, ssid_demo: str) -> Optional[User]:
        """Obter usuário por SSID Demo"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE ssid_demo = $1", ssid_demo)
            return self._user_from_row(row) if row else None

    async def get_by_ssid_real(self, ssid_real: str) -> Optional[User]:
        """Obter usuário por SSID Real"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE ssid_real = $1", ssid_real)
            return self._user_from_row(row) if row else None

    async def verify_password(self, username: str, password: str) -> bool:
        """Verificar senha do usuário"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = await self.get_by_username(username)
        if not user:
            return False
        return pwd_context.verify(password, user.password_hash)

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """Atualizar senha do usuário"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash(new_password)

        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                password_hash, user_id
            )
            database_logger.info(f"Password atualizado: user_id={user_id}")
            return result == "UPDATE 1"

    async def update_balance(self, user_id: int, balance: float) -> bool:
        """Atualizar saldo do usuário"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE users SET balance = $1 WHERE id = $2",
                balance, user_id
            )
            database_logger.info(f"Balance atualizado: user_id={user_id}, balance={balance}")
            return result == "UPDATE 1"

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Listar todos os usuários"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit, offset
            )
            return [self._user_from_row(row) for row in rows]

    async def get_all(self) -> List[User]:
        """Obter todos os usuários (compatibilidade)"""
        return await self.list_all()

    def _user_from_row(self, row) -> User:
        """Converter row do banco para objeto User"""
        if not row:
            return None
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            ssid_demo=row['ssid_demo'],
            plan_id=row['plan_id'],
            is_active=row['is_active'],
            balance=float(row['balance']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            ssid_real=row['ssid_real'],
            current_subscription_id=row['current_subscription_id'],
            plan_expires_at=row['plan_expires_at']
        )

    async def close(self):
        """Fechar pool de conexões"""
        if self.pool:
            await self.pool.close()
            self.pool = None
