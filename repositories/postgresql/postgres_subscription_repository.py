"""Repositório PostgreSQL para Subscriptions"""

import asyncpg
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from repositories.interfaces.subscription_repository_interface import SubscriptionRepositoryInterface
from models.subscription import Subscription
from core.logger import get_logger, LoggerConfig

logger = get_logger(__name__)
database_logger = LoggerConfig.get_database_logger()


class PostgresSubscriptionRepository(SubscriptionRepositoryInterface):
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
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    plan_id INTEGER NOT NULL,
                    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    payment_method VARCHAR(50),
                    payment_id VARCHAR(255),
                    auto_renew BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    cancelled_at TIMESTAMP WITH TIME ZONE,
                    expired_at TIMESTAMP WITH TIME ZONE
                )
            """)
            logger.info("Tabela subscriptions criada com sucesso")
            database_logger.info("Tabela subscriptions criada")

        self._initialized = True

    async def create(self, subscription: Subscription) -> Subscription:
        """Criar subscription"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO subscriptions (user_id, plan_id, start_date, end_date, status,
                payment_method, payment_id, auto_renew)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *""",
                subscription.user_id, subscription.plan_id, subscription.start_date,
                subscription.end_date, subscription.status, subscription.payment_method,
                subscription.payment_id, subscription.auto_renew
            )
            database_logger.info(f"Subscription criada: id={row['id']}, user_id={subscription.user_id}")
            return self._subscription_from_row(row)

    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Obter subscription por ID"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM subscriptions WHERE id = $1", subscription_id)
            return self._subscription_from_row(row) if row else None

    async def get_active_by_user(self, user_id: int) -> Optional[Subscription]:
        """Obter subscription ativa do usuário"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT * FROM subscriptions WHERE user_id = $1 AND status = 'active'
                ORDER BY end_date DESC LIMIT 1""",
                user_id
            )
            return self._subscription_from_row(row) if row else None

    async def get_all_by_user(self, user_id: int) -> List[Subscription]:
        """Obter todas as subscriptions do usuário (histórico)"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM subscriptions WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            return [self._subscription_from_row(row) for row in rows]

    async def get_expired_subscriptions(self) -> List[Subscription]:
        """Obter subscriptions expiradas (end_date < agora e status = active)"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM subscriptions WHERE end_date < NOW() AND status = 'active'"""
            )
            return [self._subscription_from_row(row) for row in rows]

    async def get_grace_period_subscriptions(self, grace_days: int) -> List[Subscription]:
        """Obter subscriptions em grace period que devem expirar"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM subscriptions WHERE status = 'grace_period'
                AND end_date + INTERVAL '1 day' * $1 < NOW()""",
                grace_days
            )
            return [self._subscription_from_row(row) for row in rows]

    async def get_auto_renew_expiring(self) -> List[Subscription]:
        """Obter subscriptions com auto_renew que estão expirando"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM subscriptions WHERE auto_renew = TRUE
                AND end_date < NOW() AND status = 'active'"""
            )
            return [self._subscription_from_row(row) for row in rows]

    async def get_history(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Subscription]:
        """Obter histórico de subscriptions do usuário"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM subscriptions WHERE user_id = $1
                ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
                user_id, limit, offset
            )
            return [self._subscription_from_row(row) for row in rows]

    async def get_by_status(self, status: str) -> List[Subscription]:
        """Obter subscriptions por status"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM subscriptions WHERE status = $1 ORDER BY created_at DESC",
                status
            )
            return [self._subscription_from_row(row) for row in rows]

    async def update(self, subscription: Subscription) -> Subscription:
        """Atualizar subscription"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE subscriptions SET user_id = $1, plan_id = $2, start_date = $3,
                end_date = $4, status = $5, payment_method = $6, payment_id = $7,
                auto_renew = $8, cancelled_at = $9, expired_at = $10 WHERE id = $11 RETURNING *""",
                subscription.user_id, subscription.plan_id, subscription.start_date,
                subscription.end_date, subscription.status, subscription.payment_method,
                subscription.payment_id, subscription.auto_renew, subscription.cancelled_at,
                subscription.expired_at, subscription.id
            )
            database_logger.info(f"Subscription atualizada: id={subscription.id}")
            return self._subscription_from_row(row)

    async def update_status(self, subscription_id: int, status: str) -> bool:
        """Atualizar status da subscription"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE subscriptions SET status = $1 WHERE id = $2",
                status, subscription_id
            )
            database_logger.warning(f"Subscription status atualizado: id={subscription_id}, status={status}")
            return result == "UPDATE 1"

    async def cancel(self, subscription_id: int) -> bool:
        """Cancelar subscription"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE subscriptions SET status = 'cancelled', cancelled_at = NOW()
                WHERE id = $1""",
                subscription_id
            )
            database_logger.warning(f"Subscription cancelada: id={subscription_id}")
            return result == "UPDATE 1"

    async def expire_subscription(self, subscription_id: int) -> bool:
        """Expirar subscription (marcar como expired, NÃO deletar)"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE subscriptions SET status = 'expired', expired_at = NOW()
                WHERE id = $1""",
                subscription_id
            )
            database_logger.warning(f"Subscription expirada: id={subscription_id}")
            return result == "UPDATE 1"

    async def create_for_user(self, user_id: int, plan_id: int, start_date, end_date,
                            payment_method: Optional[str] = None,
                            payment_id: Optional[str] = None,
                            auto_renew: bool = False) -> Subscription:
        """Criar subscription para um usuário"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO subscriptions (user_id, plan_id, start_date, end_date,
                payment_method, payment_id, auto_renew)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *""",
                user_id, plan_id, start_date, end_date, payment_method, payment_id, auto_renew
            )
            database_logger.info(f"Subscription criada para user: id={row['id']}, user_id={user_id}")
            return self._subscription_from_row(row)

    def _subscription_from_row(self, row) -> Subscription:
        """Converter row do banco para objeto Subscription"""
        if not row:
            return None
        return Subscription(
            id=row['id'],
            user_id=row['user_id'],
            plan_id=row['plan_id'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            status=row['status'],
            payment_method=row['payment_method'],
            payment_id=row['payment_id'],
            auto_renew=row['auto_renew'],
            created_at=row['created_at'],
            cancelled_at=row['cancelled_at'],
            expired_at=row['expired_at']
        )

    async def close(self):
        """Fechar pool de conexões"""
        if self.pool:
            await self.pool.close()
            self.pool = None
