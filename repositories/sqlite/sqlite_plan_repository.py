"""Implementação SQLite do repositório de planos"""

import os
import sqlite3
import asyncio
import threading
from datetime import datetime, timezone
from typing import Optional, List
from repositories.interfaces.plan_repository_interface import PlanRepositoryInterface
from models.plan import Plan
from core.logger import get_logger
from core.exceptions import DatabaseError


logger = get_logger(__name__)


class SQLitePlanRepository(PlanRepositoryInterface):
    """Repositório SQLite - Implementação com asyncio.to_thread()"""

    def __init__(self, db_path: str = "data/openob.db"):
        self.db_path = db_path
        self.conn = None
        self._lock = threading.Lock()
        self._initialize_db_sync()
        logger.info(f"SQLite PlanRepository inicializado: {db_path}")

    def _initialize_db_sync(self):
        """Setup inicial do banco (síncrono)"""
        with self._lock:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=DELETE")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=-64000")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            self.conn.execute("PRAGMA busy_timeout=5000")

            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL UNIQUE,
                price REAL NOT NULL,
                description TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_type ON plans(type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_active ON plans(is_active)")

            self.conn.commit()
            logger.info("Tabela plans criada com sucesso")

            self._insert_default_plans()

    def _insert_default_plans(self):
        """Inserir planos padrão se não existirem"""
        with self._lock:
            default_plans = [
                {
                    "name": "Free",
                    "type": "free",
                    "price": 0.0,
                    "description": "Plano gratuito com acesso básico",
                    "duration_days": 0,
                    "is_active": 1
                },
                {
                    "name": "Diário",
                    "type": "daily",
                    "price": 5.00,
                    "description": "Plano diário com acesso completo por 24 horas",
                    "duration_days": 1,
                    "is_active": 1
                },
                {
                    "name": "Semanal",
                    "type": "weekly",
                    "price": 25.00,
                    "description": "Plano semanal com acesso completo por 7 dias",
                    "duration_days": 7,
                    "is_active": 1
                },
                {
                    "name": "Mensal",
                    "type": "monthly",
                    "price": 80.00,
                    "description": "Plano mensal com acesso completo por 30 dias",
                    "duration_days": 30,
                    "is_active": 1
                }
            ]

            for plan in default_plans:
                try:
                    self.conn.execute(
                        """INSERT OR IGNORE INTO plans 
                        (name, type, price, description, duration_days, is_active) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (plan["name"], plan["type"], plan["price"], plan["description"], 
                         plan["duration_days"], plan["is_active"])
                    )
                except sqlite3.IntegrityError:
                    pass

            self.conn.commit()
            logger.info("Planos padrão inseridos")

    def _plan_from_row(self, row: tuple) -> Plan:
        """Converter row do banco para modelo Plan"""
        return Plan(
            id=row[0],
            name=row[1],
            type=row[2],
            price=row[3],
            description=row[4],
            duration_days=row[5],
            is_active=bool(row[6]),
            created_at=datetime.fromisoformat(row[7]) if row[7] else None
        )

    async def create(self, plan: Plan) -> Plan:
        """Criar plano e retornar com ID"""
        try:
            return await asyncio.to_thread(self._create_sync, plan)
        except Exception as e:
            logger.error(f"Erro ao criar plano: {e}")
            raise DatabaseError(f"Falha ao criar plano: {e}")

    def _create_sync(self, plan: Plan) -> Plan:
        """Criar plano (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                """INSERT INTO plans (name, type, price, description, duration_days, is_active) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (plan.name, plan.type, plan.price, plan.description, plan.duration_days, plan.is_active)
            )
            self.conn.commit()

            plan_id = cursor.lastrowid
            cursor = self.conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
            row = cursor.fetchone()
            return self._plan_from_row(row)

    async def get_by_id(self, plan_id: int) -> Optional[Plan]:
        """Obter plano por ID"""
        try:
            return await asyncio.to_thread(self._get_by_id_sync, plan_id)
        except Exception as e:
            logger.error(f"Erro ao buscar plano por ID: {e}")
            raise DatabaseError(f"Falha ao buscar plano: {e}")

    def _get_by_id_sync(self, plan_id: int) -> Optional[Plan]:
        """Obter plano por ID (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM plans WHERE id = ?", (plan_id,)
            )
            row = cursor.fetchone()
            return self._plan_from_row(row) if row else None

    async def get_by_type(self, plan_type: str) -> Optional[Plan]:
        """Obter plano por tipo"""
        try:
            return await asyncio.to_thread(self._get_by_type_sync, plan_type)
        except Exception as e:
            logger.error(f"Erro ao buscar plano por tipo: {e}")
            raise DatabaseError(f"Falha ao buscar plano: {e}")

    def _get_by_type_sync(self, plan_type: str) -> Optional[Plan]:
        """Obter plano por tipo (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM plans WHERE type = ?", (plan_type,)
            )
            row = cursor.fetchone()
            return self._plan_from_row(row) if row else None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Plan]:
        """Listar todos os planos"""
        try:
            return await asyncio.to_thread(self._list_all_sync, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar planos: {e}")
            raise DatabaseError(f"Falha ao listar planos: {e}")

    def _list_all_sync(self, limit: int = 100, offset: int = 0) -> List[Plan]:
        """Listar planos (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM plans ORDER BY id LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [self._plan_from_row(row) for row in rows]

    async def get_active_plans(self) -> List[Plan]:
        """Listar apenas planos ativos"""
        try:
            return await asyncio.to_thread(self._get_active_plans_sync)
        except Exception as e:
            logger.error(f"Erro ao listar planos ativos: {e}")
            raise DatabaseError(f"Falha ao listar planos ativos: {e}")

    def _get_active_plans_sync(self) -> List[Plan]:
        """Listar planos ativos (síncrono)"""
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM plans WHERE is_active = 1 ORDER BY duration_days"
            )
            rows = cursor.fetchall()
            return [self._plan_from_row(row) for row in rows]

    async def update(self, plan: Plan) -> Plan:
        """Atualizar plano"""
        try:
            return await asyncio.to_thread(self._update_sync, plan)
        except Exception as e:
            logger.error(f"Erro ao atualizar plano: {e}")
            raise DatabaseError(f"Falha ao atualizar plano: {e}")

    def _update_sync(self, plan: Plan) -> Plan:
        """Atualizar plano (síncrono)"""
        with self._lock:
            self.conn.execute(
                """UPDATE plans SET 
                name = ?, 
                type = ?, 
                price = ?, 
                description = ?, 
                duration_days = ?, 
                is_active = ? 
                WHERE id = ?""",
                (plan.name, plan.type, plan.price, plan.description, plan.duration_days, 
                 plan.is_active, plan.id)
            )
            self.conn.commit()
            cursor = self.conn.execute("SELECT * FROM plans WHERE id = ?", (plan.id,))
            row = cursor.fetchone()
            return self._plan_from_row(row)

    async def delete(self, plan_id: int) -> bool:
        """Deletar plano"""
        try:
            await asyncio.to_thread(self._delete_sync, plan_id)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar plano: {e}")
            raise DatabaseError(f"Falha ao deletar plano: {e}")

    def _delete_sync(self, plan_id: int):
        """Deletar plano (síncrono)"""
        with self._lock:
            self.conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
            self.conn.commit()

    async def close(self):
        """Fechar conexão"""
        if self.conn:
            self.conn.close()
            self.conn = None
        logger.info("SQLite PlanRepository fechado")
