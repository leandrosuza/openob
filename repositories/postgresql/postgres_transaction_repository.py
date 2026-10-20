"""Repositório PostgreSQL para Transactions"""

import asyncpg
from datetime import datetime, timezone
from typing import Optional, List
from repositories.interfaces.transaction_repository_interface import TransactionRepositoryInterface
from models.transaction import Transaction
from core.logger import get_logger, LoggerConfig

logger = get_logger(__name__)
database_logger = LoggerConfig.get_database_logger()


class PostgresTransactionRepository(TransactionRepositoryInterface):
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
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    subscription_id INTEGER,
                    plan_id INTEGER NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    currency VARCHAR(10) NOT NULL DEFAULT 'BRL',
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    payment_method VARCHAR(50),
                    payment_id VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Tabela transactions criada com sucesso")
            database_logger.info("Tabela transactions criada")

        self._initialized = True

    async def create(self, transaction: Transaction) -> Transaction:
        """Criar transaction"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO transactions (user_id, subscription_id, plan_id, amount, currency,
                status, payment_method, payment_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *""",
                transaction.user_id, transaction.subscription_id, transaction.plan_id,
                transaction.amount, transaction.currency, transaction.status,
                transaction.payment_method, transaction.payment_id
            )
            database_logger.info(f"Transaction criada: id={row['id']}, user_id={transaction.user_id}")
            return self._transaction_from_row(row)

    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Obter transaction por ID"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM transactions WHERE id = $1", transaction_id)
            return self._transaction_from_row(row) if row else None

    async def get_by_payment_id(self, payment_id: str) -> Optional[Transaction]:
        """Obter transaction por payment_id"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM transactions WHERE payment_id = $1", payment_id)
            return self._transaction_from_row(row) if row else None

    async def get_all_by_user(self, user_id: int) -> List[Transaction]:
        """Obter todas as transactions do usuário"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM transactions WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            return [self._transaction_from_row(row) for row in rows]

    async def update_status(self, transaction_id: int, status: str) -> Transaction:
        """Atualizar status da transaction"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "UPDATE transactions SET status = $1 WHERE id = $2 RETURNING *",
                status, transaction_id
            )
            database_logger.info(f"Transaction status atualizado: id={transaction_id}, status={status}")
            return self._transaction_from_row(row)

    def _transaction_from_row(self, row) -> Transaction:
        """Converter row do banco para objeto Transaction"""
        if not row:
            return None
        return Transaction(
            id=row['id'],
            user_id=row['user_id'],
            subscription_id=row['subscription_id'],
            plan_id=row['plan_id'],
            amount=float(row['amount']),
            currency=row['currency'],
            status=row['status'],
            payment_method=row['payment_method'],
            payment_id=row['payment_id'],
            created_at=row['created_at']
        )

    async def close(self):
        """Fechar pool de conexões"""
        if self.pool:
            await self.pool.close()
            self.pool = None
