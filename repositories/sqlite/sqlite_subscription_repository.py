"""Implementação SQLite do repositório de subscriptions"""

import os
import sqlite3
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from repositories.interfaces.subscription_repository_interface import SubscriptionRepositoryInterface
from models.subscription import Subscription
from core.logger import get_logger
from core.exceptions import DatabaseError


logger = get_logger(__name__)


class SQLiteSubscriptionRepository(SubscriptionRepositoryInterface):
    """Repositório SQLite - Implementação com asyncio.to_thread()"""

    def __init__(self, db_path: str = "data/openob.db"):
        self.db_path = db_path
        self.conn = None
        self._lock = threading.Lock()
        self._initialize_db_sync()
        logger.info(f"SQLite SubscriptionRepository inicializado: {db_path}")

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
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                status TEXT NOT NULL,
                payment_method TEXT,
                payment_id TEXT,
                auto_renew BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                cancelled_at DATETIME,
                expired_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (plan_id) REFERENCES plans(id)
            )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_subscription_user ON subscriptions(user_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_subscription_status ON subscriptions(status)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_subscription_plan ON subscriptions(plan_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_subscription_payment ON subscriptions(payment_id)")

            self.conn.commit()
            logger.info("Tabela subscriptions criada com sucesso")

    def _subscription_from_row(self, row: tuple) -> Subscription:
        """Converter row do banco para modelo Subscription"""
        return Subscription(
            id=row[0],
            user_id=row[1],
            plan_id=row[2],
            start_date=datetime.fromisoformat(row[3]) if row[3] else None,
            end_date=datetime.fromisoformat(row[4]) if row[4] else None,
            status=row[5],
            payment_method=row[6],
            payment_id=row[7],
            auto_renew=bool(row[8]),
            created_at=datetime.fromisoformat(row[9]) if row[9] else None,
            cancelled_at=datetime.fromisoformat(row[10]) if row[10] else None,
            expired_at=datetime.fromisoformat(row[11]) if row[11] else None
        )

    async def create(self, subscription: Subscription) -> Subscription:
        """Criar subscription e retornar com ID"""
        try:
            return await asyncio.to_thread(self._create_sync, subscription)
        except Exception as e:
            logger.error(f"Erro ao criar subscription: {e}")
            raise DatabaseError(f"Falha ao criar subscription: {e}")

    def _create_sync(self, subscription: Subscription) -> Subscription:
        """Criar subscription (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                """INSERT INTO subscriptions 
                (user_id, plan_id, start_date, end_date, status, payment_method, payment_id, auto_renew) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (subscription.user_id, subscription.plan_id, subscription.start_date.isoformat(),
                 subscription.end_date.isoformat(), subscription.status, subscription.payment_method,
                 subscription.payment_id, subscription.auto_renew)
            )
            self.conn.commit()

            subscription_id = cursor.lastrowid
            cursor = self.conn.execute("SELECT * FROM subscriptions WHERE id = ?", (subscription_id,))
            row = cursor.fetchone()
            return self._subscription_from_row(row)

    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Obter subscription por ID"""
        try:
            return await asyncio.to_thread(self._get_by_id_sync, subscription_id)
        except Exception as e:
            logger.error(f"Erro ao buscar subscription por ID: {e}")
            raise DatabaseError(f"Falha ao buscar subscription: {e}")

    def _get_by_id_sync(self, subscription_id: int) -> Optional[Subscription]:
        """Obter subscription por ID (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM subscriptions WHERE id = ?", (subscription_id,)
            )
            row = cursor.fetchone()
            return self._subscription_from_row(row) if row else None

    async def get_active_by_user(self, user_id: int) -> Optional[Subscription]:
        """Obter subscription ativa do usuário"""
        try:
            return await asyncio.to_thread(self._get_active_by_user_sync, user_id)
        except Exception as e:
            logger.error(f"Erro ao buscar subscription ativa: {e}")
            raise DatabaseError(f"Falha ao buscar subscription: {e}")

    def _get_active_by_user_sync(self, user_id: int) -> Optional[Subscription]:
        """Obter subscription ativa (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                """SELECT * FROM subscriptions 
                WHERE user_id = ? AND status = 'active' 
                ORDER BY created_at DESC LIMIT 1""",
                (user_id,)
            )
            row = cursor.fetchone()
            return self._subscription_from_row(row) if row else None

    async def get_all_by_user(self, user_id: int) -> List[Subscription]:
        """Obter todas as subscriptions do usuário (ativas + expiradas)"""
        try:
            return await asyncio.to_thread(self._get_all_by_user_sync, user_id)
        except Exception as e:
            logger.error(f"Erro ao buscar subscriptions do usuário: {e}")
            raise DatabaseError(f"Falha ao buscar subscriptions: {e}")

    def _get_all_by_user_sync(self, user_id: int) -> List[Subscription]:
        """Obter todas as subscriptions (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [self._subscription_from_row(row) for row in rows]

    async def get_history(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Subscription]:
        """Obter histórico de subscriptions do usuário"""
        try:
            return await asyncio.to_thread(self._get_history_sync, user_id, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            raise DatabaseError(f"Falha ao buscar histórico: {e}")

    def _get_history_sync(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Subscription]:
        """Obter histórico (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                """SELECT * FROM subscriptions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?""",
                (user_id, limit, offset)
            )
            rows = cursor.fetchall()
            return [self._subscription_from_row(row) for row in rows]

    async def get_by_status(self, status: str) -> List[Subscription]:
        """Obter subscriptions por status"""
        try:
            return await asyncio.to_thread(self._get_by_status_sync, status)
        except Exception as e:
            logger.error(f"Erro ao buscar subscriptions por status: {e}")
            raise DatabaseError(f"Falha ao buscar subscriptions: {e}")

    def _get_by_status_sync(self, status: str) -> List[Subscription]:
        """Obter por status (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM subscriptions WHERE status = ?",
                (status,)
            )
            rows = cursor.fetchall()
            return [self._subscription_from_row(row) for row in rows]

    async def get_expired_subscriptions(self) -> List[Subscription]:
        """Obter subscriptions ativas expiradas (end_date < now)"""
        try:
            return await asyncio.to_thread(self._get_expired_subscriptions_sync)
        except Exception as e:
            logger.error(f"Erro ao buscar subscriptions expiradas: {e}")
            raise DatabaseError(f"Falha ao buscar subscriptions: {e}")

    def _get_expired_subscriptions_sync(self) -> List[Subscription]:
        """Obter expiradas (síncrono)"""
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            cursor = self.conn.execute(
                """SELECT * FROM subscriptions 
                WHERE status = 'active' AND end_date < ?""",
                (now,)
            )
            rows = cursor.fetchall()
            return [self._subscription_from_row(row) for row in rows]

    async def get_grace_period_subscriptions(self, grace_period_days: int) -> List[Subscription]:
        """Obter subscriptions em grace period que já expiraram"""
        try:
            return await asyncio.to_thread(self._get_grace_period_subscriptions_sync, grace_period_days)
        except Exception as e:
            logger.error(f"Erro ao buscar subscriptions grace period: {e}")
            raise DatabaseError(f"Falha ao buscar subscriptions: {e}")

    def _get_grace_period_subscriptions_sync(self, grace_period_days: int) -> List[Subscription]:
        """Obter grace period expiradas (síncrono)"""
        with self._lock:
            now = datetime.now(timezone.utc)
            cursor = self.conn.execute(
                """SELECT * FROM subscriptions 
                WHERE status = 'grace_period' AND end_date < ?""",
                (now.isoformat(),)
            )
            rows = cursor.fetchall()
            expired = []
            for row in rows:
                sub = self._subscription_from_row(row)
                if sub.end_date + timedelta(days=grace_period_days) < now:
                    expired.append(sub)
            return expired

    async def get_auto_renew_expiring(self) -> List[Subscription]:
        """Obter subscriptions com auto_renew que estão expirando"""
        try:
            return await asyncio.to_thread(self._get_auto_renew_expiring_sync)
        except Exception as e:
            logger.error(f"Erro ao buscar subscriptions auto-renew: {e}")
            raise DatabaseError(f"Falha ao buscar subscriptions: {e}")

    def _get_auto_renew_expiring_sync(self) -> List[Subscription]:
        """Obter auto-renew expirando (síncrono)"""
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            cursor = self.conn.execute(
                """SELECT * FROM subscriptions 
                WHERE status = 'active' AND auto_renew = 1 AND end_date < ?""",
                (now,)
            )
            rows = cursor.fetchall()
            return [self._subscription_from_row(row) for row in rows]

    async def update(self, subscription: Subscription) -> Subscription:
        """Atualizar subscription"""
        try:
            return await asyncio.to_thread(self._update_sync, subscription)
        except Exception as e:
            logger.error(f"Erro ao atualizar subscription: {e}")
            raise DatabaseError(f"Falha ao atualizar subscription: {e}")

    def _update_sync(self, subscription: Subscription) -> Subscription:
        """Atualizar subscription (síncrono)"""
        with self._lock:
            self.conn.execute(
                """UPDATE subscriptions SET 
                user_id = ?, 
                plan_id = ?, 
                start_date = ?, 
                end_date = ?, 
                status = ?, 
                payment_method = ?, 
                payment_id = ?, 
                auto_renew = ?,
                cancelled_at = ?,
                expired_at = ?
                WHERE id = ?""",
                (subscription.user_id, subscription.plan_id, subscription.start_date.isoformat(),
                 subscription.end_date.isoformat(), subscription.status, subscription.payment_method,
                 subscription.payment_id, subscription.auto_renew,
                 subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
                 subscription.expired_at.isoformat() if subscription.expired_at else None,
                 subscription.id)
            )
            self.conn.commit()
            cursor = self.conn.execute("SELECT * FROM subscriptions WHERE id = ?", (subscription.id,))
            row = cursor.fetchone()
            return self._subscription_from_row(row)

    async def update_status(self, subscription_id: int, status: str) -> bool:
        """Atualizar status da subscription"""
        try:
            await asyncio.to_thread(self._update_status_sync, subscription_id, status)
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")
            raise DatabaseError(f"Falha ao atualizar status: {e}")

    def _update_status_sync(self, subscription_id: int, status: str):
        """Atualizar status (síncrono)"""
        with self._lock:
            updates = {"status": status}
            if status == "cancelled":
                updates["cancelled_at"] = datetime.now(timezone.utc).isoformat()
            elif status == "expired":
                updates["expired_at"] = datetime.now(timezone.utc).isoformat()

            if len(updates) == 1:
                self.conn.execute(
                    "UPDATE subscriptions SET status = ? WHERE id = ?",
                    (status, subscription_id)
                )
            else:
                fields = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [subscription_id]
                self.conn.execute(
                    f"UPDATE subscriptions SET {fields} WHERE id = ?",
                    values
                )
            self.conn.commit()

    async def cancel(self, subscription_id: int) -> bool:
        """Cancelar subscription"""
        try:
            await asyncio.to_thread(self._cancel_sync, subscription_id)
            return True
        except Exception as e:
            logger.error(f"Erro ao cancelar subscription: {e}")
            raise DatabaseError(f"Falha ao cancelar subscription: {e}")

    def _cancel_sync(self, subscription_id: int):
        """Cancelar subscription (síncrono)"""
        with self._lock:
            self.conn.execute(
                """UPDATE subscriptions SET 
                status = 'cancelled', 
                cancelled_at = ? 
                WHERE id = ?""",
                (datetime.now(timezone.utc).isoformat(), subscription_id)
            )
            self.conn.commit()

    async def expire_subscription(self, subscription_id: int) -> bool:
        """Expirar subscription (sem deletar - manter histórico)"""
        try:
            await asyncio.to_thread(self._expire_subscription_sync, subscription_id)
            return True
        except Exception as e:
            logger.error(f"Erro ao expirar subscription: {e}")
            raise DatabaseError(f"Falha ao expirar subscription: {e}")

    def _expire_subscription_sync(self, subscription_id: int):
        """Expirar subscription (síncrono) - NÃO deleta"""
        with self._lock:
            self.conn.execute(
                """UPDATE subscriptions SET 
                status = 'expired', 
                expired_at = ? 
                WHERE id = ?""",
                (datetime.now(timezone.utc).isoformat(), subscription_id)
            )
            self.conn.commit()

    async def create_for_user(self, user_id: int, plan_id: int, start_date, end_date, 
                            payment_method: Optional[str] = None, 
                            payment_id: Optional[str] = None,
                            auto_renew: bool = False) -> Subscription:
        """Criar subscription para um usuário"""
        try:
            return await asyncio.to_thread(self._create_for_user_sync, user_id, plan_id, 
                                           start_date, end_date, payment_method, payment_id, auto_renew)
        except Exception as e:
            logger.error(f"Erro ao criar subscription para usuário: {e}")
            raise DatabaseError(f"Falha ao criar subscription: {e}")

    def _create_for_user_sync(self, user_id: int, plan_id: int, start_date, end_date, 
                            payment_method: Optional[str], payment_id: Optional[str], auto_renew: bool) -> Subscription:
        """Criar subscription para usuário (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                """INSERT INTO subscriptions 
                (user_id, plan_id, start_date, end_date, status, payment_method, payment_id, auto_renew) 
                VALUES (?, ?, ?, ?, 'active', ?, ?, ?)""",
                (user_id, plan_id, start_date.isoformat(), end_date.isoformat(),
                 payment_method, payment_id, auto_renew)
            )
            self.conn.commit()

            subscription_id = cursor.lastrowid
            cursor = self.conn.execute("SELECT * FROM subscriptions WHERE id = ?", (subscription_id,))
            row = cursor.fetchone()
            return self._subscription_from_row(row)

    async def close(self):
        """Fechar conexão"""
        if self.conn:
            self.conn.close()
            self.conn = None
        logger.info("SQLite SubscriptionRepository fechado")
