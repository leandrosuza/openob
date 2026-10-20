"""Repositório PostgreSQL para Planos"""

import asyncpg
from datetime import datetime, timezone
from typing import Optional, List
from repositories.interfaces.plan_repository_interface import PlanRepositoryInterface
from models.plan import Plan
from core.logger import get_logger, LoggerConfig

logger = get_logger(__name__)
database_logger = LoggerConfig.get_database_logger()


class PostgresPlanRepository(PlanRepositoryInterface):
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
                CREATE TABLE IF NOT EXISTS plans (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(50) NOT NULL UNIQUE,
                    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                    description TEXT,
                    duration_days INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Tabela plans criada com sucesso")
            database_logger.info("Tabela plans criada")

            await self._insert_default_plans()

        self._initialized = True

    async def _insert_default_plans(self):
        """Inserir planos padrão se não existirem"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Verificar se já existem planos
            count = await conn.fetchval("SELECT COUNT(*) FROM plans")
            if count > 0:
                return

            # Inserir planos padrão
            plans = [
                ("Free", "free", 0.00, "Plano gratuito com acesso básico", 0),
                ("Diário", "daily", 5.00, "Plano diário com acesso completo por 24 horas", 1),
                ("Semanal", "weekly", 25.00, "Plano semanal com acesso completo por 7 dias", 7),
                ("Mensal", "monthly", 80.00, "Plano mensal com acesso completo por 30 dias", 30),
            ]

            for name, ptype, price, desc, duration in plans:
                await conn.execute(
                    "INSERT INTO plans (name, type, price, description, duration_days) VALUES ($1, $2, $3, $4, $5)",
                    name, ptype, price, desc, duration
                )

            logger.info("Planos padrão inseridos com sucesso")
            database_logger.info("Planos padrão inseridos")

    async def create(self, plan: Plan) -> Plan:
        """Criar plano"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO plans (name, type, price, description, duration_days, is_active)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *""",
                plan.name, plan.type, plan.price, plan.description, plan.duration_days, plan.is_active
            )
            database_logger.info(f"Plan criado: id={row['id']}, type={plan.type}")
            return self._plan_from_row(row)

    async def get_by_id(self, plan_id: int) -> Optional[Plan]:
        """Obter plano por ID"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM plans WHERE id = $1", plan_id)
            return self._plan_from_row(row) if row else None

    async def get_by_type(self, plan_type: str) -> Optional[Plan]:
        """Obter plano por tipo"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM plans WHERE type = $1", plan_type)
            return self._plan_from_row(row) if row else None

    async def get_all(self) -> List[Plan]:
        """Obter todos os planos ativos"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM plans WHERE is_active = TRUE ORDER BY price")
            return [self._plan_from_row(row) for row in rows]

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Plan]:
        """Listar todos os planos"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM plans ORDER BY price LIMIT $1 OFFSET $2",
                limit, offset
            )
            return [self._plan_from_row(row) for row in rows]

    async def get_active_plans(self) -> List[Plan]:
        """Listar apenas planos ativos"""
        return await self.get_all()

    async def update(self, plan: Plan) -> Plan:
        """Atualizar plano"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE plans SET name = $1, type = $2, price = $3, description = $4,
                duration_days = $5, is_active = $6 WHERE id = $7 RETURNING *""",
                plan.name, plan.type, plan.price, plan.description,
                plan.duration_days, plan.is_active, plan.id
            )
            database_logger.info(f"Plan atualizado: id={plan.id}")
            return self._plan_from_row(row)

    async def delete(self, plan_id: int) -> bool:
        """Deletar plano (soft delete - desativar)"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE plans SET is_active = FALSE WHERE id = $1", plan_id
            )
            database_logger.info(f"Plan desativado: id={plan_id}")
            return result == "UPDATE 1"

    def _plan_from_row(self, row) -> Plan:
        """Converter row do banco para objeto Plan"""
        if not row:
            return None
        return Plan(
            id=row['id'],
            name=row['name'],
            type=row['type'],
            price=float(row['price']),
            description=row['description'],
            duration_days=row['duration_days'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )

    async def close(self):
        """Fechar pool de conexões"""
        if self.pool:
            await self.pool.close()
            self.pool = None
