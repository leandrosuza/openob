"""Implementação SQLite do repositório de transações"""

import os
import sqlite3
import asyncio
import threading
from datetime import datetime, timezone
from typing import Optional, List
from repositories.interfaces.transaction_repository_interface import TransactionRepositoryInterface
from models.transaction import Transaction
from core.logger import get_logger
from core.exceptions import DatabaseError


logger = get_logger(__name__)


class SQLiteTransactionRepository(TransactionRepositoryInterface):
    """Repositório SQLite - Implementação com asyncio.to_thread()"""

    def __init__(self, db_path: str = "data/openob.db"):
        self.db_path = db_path
        self.conn = None
        self._lock = threading.Lock()
        self._initialize_db_sync()
        logger.info(f"SQLite TransactionRepository inicializado: {db_path}")

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
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subscription_id INTEGER,
                plan_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                payment_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
                FOREIGN KEY (plan_id) REFERENCES plans(id)
            )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_transaction_user ON transactions(user_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_transaction_payment ON transactions(payment_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_transaction_status ON transactions(status)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_transaction_subscription ON transactions(subscription_id)")

            self.conn.commit()
            logger.info("Tabela transactions criada com sucesso")

    def _transaction_from_row(self, row: tuple) -> Transaction:
        """Converter row do banco para modelo Transaction"""
        return Transaction(
            id=row[0],
            user_id=row[1],
            subscription_id=row[2],
            plan_id=row[3],
            amount=row[4],
            currency=row[5],
            status=row[6],
            payment_method=row[7],
            payment_id=row[8],
            created_at=datetime.fromisoformat(row[9]) if row[9] else None
        )

    async def create(self, transaction: Transaction) -> Transaction:
        """Criar transação e retornar com ID"""
        try:
            return await asyncio.to_thread(self._create_sync, transaction)
        except Exception as e:
            logger.error(f"Erro ao criar transação: {e}")
            raise DatabaseError(f"Falha ao criar transação: {e}")

    def _create_sync(self, transaction: Transaction) -> Transaction:
        """Criar transação (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                """INSERT INTO transactions 
                (user_id, subscription_id, plan_id, amount, currency, status, payment_method, payment_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (transaction.user_id, transaction.subscription_id, transaction.plan_id,
                 transaction.amount, transaction.currency, transaction.status,
                 transaction.payment_method, transaction.payment_id)
            )
            self.conn.commit()

            transaction_id = cursor.lastrowid
            cursor = self.conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()
            return self._transaction_from_row(row)

    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Obter transação por ID"""
        try:
            return await asyncio.to_thread(self._get_by_id_sync, transaction_id)
        except Exception as e:
            logger.error(f"Erro ao buscar transação por ID: {e}")
            raise DatabaseError(f"Falha ao buscar transação: {e}")

    def _get_by_id_sync(self, transaction_id: int) -> Optional[Transaction]:
        """Obter transação por ID (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
            )
            row = cursor.fetchone()
            return self._transaction_from_row(row) if row else None

    async def get_by_payment_id(self, payment_id: str) -> Optional[Transaction]:
        """Obter transação por payment_id"""
        try:
            return await asyncio.to_thread(self._get_by_payment_id_sync, payment_id)
        except Exception as e:
            logger.error(f"Erro ao buscar transação por payment_id: {e}")
            raise DatabaseError(f"Falha ao buscar transação: {e}")

    def _get_by_payment_id_sync(self, payment_id: str) -> Optional[Transaction]:
        """Obter por payment_id (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM transactions WHERE payment_id = ?", (payment_id,)
            )
            row = cursor.fetchone()
            return self._transaction_from_row(row) if row else None

    async def get_user_transactions(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Transaction]:
        """Obter transações do usuário"""
        try:
            return await asyncio.to_thread(self._get_user_transactions_sync, user_id, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao buscar transações do usuário: {e}")
            raise DatabaseError(f"Falha ao buscar transações: {e}")

    def _get_user_transactions_sync(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Transaction]:
        """Obter transações do usuário (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                """SELECT * FROM transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?""",
                (user_id, limit, offset)
            )
            rows = cursor.fetchall()
            return [self._transaction_from_row(row) for row in rows]

    async def update_status(self, transaction_id: int, status: str) -> bool:
        """Atualizar status da transação"""
        try:
            await asyncio.to_thread(self._update_status_sync, transaction_id, status)
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")
            raise DatabaseError(f"Falha ao atualizar status: {e}")

    def _update_status_sync(self, transaction_id: int, status: str):
        """Atualizar status (síncrono)"""
        with self._lock:
            self.conn.execute(
                "UPDATE transactions SET status = ? WHERE id = ?",
                (status, transaction_id)
            )
            self.conn.commit()

    async def update(self, transaction: Transaction) -> Transaction:
        """Atualizar transação"""
        try:
            return await asyncio.to_thread(self._update_sync, transaction)
        except Exception as e:
            logger.error(f"Erro ao atualizar transação: {e}")
            raise DatabaseError(f"Falha ao atualizar transação: {e}")

    def _update_sync(self, transaction: Transaction) -> Transaction:
        """Atualizar transação (síncrono)"""
        with self._lock:
            self.conn.execute(
                """UPDATE transactions SET 
                user_id = ?, 
                subscription_id = ?, 
                plan_id = ?, 
                amount = ?, 
                currency = ?, 
                status = ?, 
                payment_method = ?, 
                payment_id = ? 
                WHERE id = ?""",
                (transaction.user_id, transaction.subscription_id, transaction.plan_id,
                 transaction.amount, transaction.currency, transaction.status,
                 transaction.payment_method, transaction.payment_id, transaction.id)
            )
            self.conn.commit()
            cursor = self.conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction.id,))
            row = cursor.fetchone()
            return self._transaction_from_row(row)

    async def close(self):
        """Fechar conexão"""
        if self.conn:
            self.conn.close()
            self.conn = None
        logger.info("SQLite TransactionRepository fechado")
