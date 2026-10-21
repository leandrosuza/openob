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
                    plan_expires_at TIMESTAMP WITH TIME ZONE,
                    mode VARCHAR(20) DEFAULT 'demo',
                    is_connected BOOLEAN DEFAULT FALSE,
                    connection_status VARCHAR(50) DEFAULT 'disconnected',
                    disconnect_reason VARCHAR(255) DEFAULT NULL
                )
            """)
            logger.info("Tabela users criada com sucesso")
            database_logger.info("Tabela users criada")

            # Migrar colunas se não existirem
            try:
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mode VARCHAR(20) DEFAULT 'demo'")
                await conn.execute("UPDATE users SET mode = 'demo' WHERE mode IS NULL")
                logger.info("Migração: coluna mode adicionada")
            except Exception:
                pass

            try:
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_connected BOOLEAN DEFAULT FALSE")
                await conn.execute("UPDATE users SET is_connected = FALSE WHERE is_connected IS NULL")
                logger.info("Migração: coluna is_connected adicionada")
            except Exception:
                pass

            try:
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS connection_status VARCHAR(50) DEFAULT 'disconnected'")
                # Atualizar registros existentes com NULL para 'disconnected'
                await conn.execute("UPDATE users SET connection_status = 'disconnected' WHERE connection_status IS NULL")
                logger.info("Migração: coluna connection_status adicionada")
            except Exception:
                pass

            try:
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS disconnect_reason VARCHAR(255) DEFAULT NULL")
                logger.info("Migração: coluna disconnect_reason adicionada")
            except Exception:
                pass

        self._initialized = True

    async def create(self, user: User) -> User:
        """Criar usuário"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Garantir valores padrão para campos novos
            mode = user.mode if user.mode else 'demo'
            is_connected = user.is_connected if user.is_connected is not None else False
            connection_status = user.connection_status if user.connection_status else 'disconnected'
            disconnect_reason = user.disconnect_reason if user.disconnect_reason else None

            row = await conn.fetchrow(
                """INSERT INTO users (username, email, password_hash, ssid_demo, plan_id,
                is_active, balance, ssid_real, current_subscription_id, plan_expires_at,
                mode, is_connected, connection_status, disconnect_reason)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING *""",
                user.username, user.email, user.password_hash, user.ssid_demo,
                user.plan_id, user.is_active, user.balance, user.ssid_real,
                user.current_subscription_id, user.plan_expires_at,
                mode, is_connected, connection_status, disconnect_reason
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
                mode = $11, is_connected = $12, connection_status = $13, disconnect_reason = $14,
                updated_at = NOW() WHERE id = $15 RETURNING *""",
                user.username, user.email, user.password_hash, user.ssid_demo,
                user.plan_id, user.is_active, user.balance, user.ssid_real,
                user.current_subscription_id, user.plan_expires_at,
                user.mode, user.is_connected, user.connection_status, user.disconnect_reason, user.id
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

    async def hash_password(self, password: str) -> str:
        """Hash da senha usando bcrypt"""
        import bcrypt
        # Bcrypt limita a 72 bytes
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    async def verify_password(self, username: str, password: str) -> bool:
        """Verificar senha do usuário"""
        import bcrypt

        user = await self.get_by_username(username)
        if not user:
            return False
        # Bcrypt limita a 72 bytes
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        return bcrypt.checkpw(password_bytes, user.password_hash.encode('utf-8'))

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

    async def get_active_users(self) -> List[User]:
        """Obter usuários ativos (is_active=True)"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users WHERE is_active = TRUE ORDER BY created_at DESC"
            )
            return [self._user_from_row(row) for row in rows]

    async def get_all_users(self) -> List[User]:
        """Obter todos os usuários (sem limite)"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users ORDER BY created_at DESC"
            )
            return [self._user_from_row(row) for row in rows]

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
            plan_expires_at=row['plan_expires_at'],
            mode=row.get('mode', 'demo'),
            is_connected=row.get('is_connected', False),
            connection_status=row.get('connection_status') or 'disconnected',
            disconnect_reason=row.get('disconnect_reason')
        )

    async def close(self):
        """Fechar pool de conexões"""
        if self.pool:
            await self.pool.close()
            self.pool = None
