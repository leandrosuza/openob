"""Repositório PostgreSQL para Autotrade Configs"""

import asyncpg
import json
from datetime import datetime
from typing import Optional, List
from repositories.interfaces.autotrade_repository_interface import AutotradeRepositoryInterface
from models.autotrade import AutotradeConfig
from core.logger import get_logger, LoggerConfig


logger = get_logger(__name__)
database_logger = LoggerConfig.get_database_logger()


class PostgresAutotradeRepository(AutotradeRepositoryInterface):
    """Repositório PostgreSQL - Implementação com asyncpg"""

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool = None

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
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS autotrade_configs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    strategy_name VARCHAR(100) NOT NULL,
                    parameters JSONB NOT NULL,
                    amount DECIMAL(10, 2) DEFAULT 5.0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Tabela autotrade_configs verificada/criada com sucesso")
            database_logger.info("Tabela autotrade_configs criada")

    async def create(self, config: AutotradeConfig) -> AutotradeConfig:
        """Criar config"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO autotrade_configs (user_id, strategy_name, parameters, amount, is_active)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *""",
                config.user_id, config.strategy_name, json.dumps(config.parameters),
                config.amount, config.is_active
            )
            database_logger.info(f"AutotradeConfig criado: id={row['id']}, user_id={config.user_id}")
            return self._config_from_row(row)

    async def create_config(self, user_id: int, strategy_name: str, parameters: str, amount: float, is_active: bool) -> AutotradeConfig:
        """Criar config com parâmetros individuais"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO autotrade_configs (user_id, strategy_name, parameters, amount, is_active)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *""",
                user_id, strategy_name, parameters, amount, is_active
            )
            database_logger.info(f"AutotradeConfig criado: id={row['id']}, user_id={user_id}, is_active={is_active}")
            return self._config_from_row(row)

    async def get_by_user(self, user_id: int) -> Optional[AutotradeConfig]:
        """Obter config por user_id"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM autotrade_configs WHERE user_id = $1", user_id)
            return self._config_from_row(row) if row else None

    async def update(self, config: AutotradeConfig) -> AutotradeConfig:
        """Atualizar config"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE autotrade_configs SET strategy_name = $1, parameters = $2,
                amount = $3, is_active = $4, updated_at = NOW()
                WHERE id = $5 RETURNING *""",
                config.strategy_name, json.dumps(config.parameters),
                config.amount, config.is_active, config.id
            )
            database_logger.info(f"AutotradeConfig atualizado: id={config.id}")
            return self._config_from_row(row)

    async def delete(self, user_id: int) -> bool:
        """Deletar config por user_id"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM autotrade_configs WHERE user_id = $1", user_id
            )
            database_logger.info(f"AutotradeConfig deletado: user_id={user_id}")
            return result == "DELETE 1"

    async def get_active_strategies(self) -> List[AutotradeConfig]:
        """Obter todas as configs ativas"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM autotrade_configs WHERE is_active = TRUE"
            )
            return [self._config_from_row(row) for row in rows]

    async def get_all_configs(self) -> List[AutotradeConfig]:
        """Obter todas as configs (ativas e inativas)"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM autotrade_configs")
            return [self._config_from_row(row) for row in rows]

    def _config_from_row(self, row) -> AutotradeConfig:
        """Converter row do banco para objeto AutotradeConfig"""
        if not row:
            return None

        # parameters já vem como dict do PostgreSQL JSONB
        parameters = row['parameters']
        if isinstance(parameters, str):
            parameters = json.loads(parameters)
        elif not isinstance(parameters, dict):
            parameters = dict(parameters) if parameters else {}

        # is_active pode ser None para registros antigos
        is_active = row.get('is_active', True)
        if is_active is None:
            is_active = True

        return AutotradeConfig(
            id=row['id'],
            user_id=row['user_id'],
            strategy_name=row['strategy_name'],
            parameters=parameters,
            amount=float(row['amount']),
            is_active=is_active,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    async def close(self):
        """Fechar pool de conexões"""
        if self.pool:
            await self.pool.close()
            self.pool = None
