"""Repositório PostgreSQL para Ticks"""

import asyncpg
from datetime import datetime, timezone
from typing import List, Dict, Optional
from repositories.interfaces.tick_repository_interface import TickRepositoryInterface
from core.logger import get_logger

logger = get_logger(__name__)


class PostgresTickRepository(TickRepositoryInterface):
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
                CREATE TABLE IF NOT EXISTS ticks (
                    id SERIAL PRIMARY KEY,
                    asset VARCHAR(100) NOT NULL,
                    price DECIMAL(10, 4) NOT NULL,
                    payout DECIMAL(5, 2),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS asset_metadata (
                    id SERIAL PRIMARY KEY,
                    asset VARCHAR(100) NOT NULL UNIQUE,
                    payout DECIMAL(5, 2),
                    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)

            logger.info("Tabelas ticks e asset_metadata criadas com sucesso")

        self._initialized = True

    async def save(self, asset: str, price: float, payout: Optional[float] = None, timestamp: Optional[datetime] = None) -> int:
        """Salvar tick e retornar ID"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO ticks (asset, price, payout, timestamp)
                VALUES ($1, $2, $3, COALESCE($4, NOW())) RETURNING id""",
                asset, price, payout, timestamp
            )
            return row['id']

    async def get_recent(self, asset: str, limit: int = 100) -> List[Dict]:
        """Obter ticks recentes de um ativo"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM ticks WHERE asset = $1
                ORDER BY timestamp DESC LIMIT $2""",
                asset, limit
            )
            return [dict(row) for row in rows]

    async def get_by_sequence(self, asset: str, start: int, end: int) -> List[Dict]:
        """Obter ticks por range de ID"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM ticks WHERE asset = $1 AND id >= $2 AND id <= $3
                ORDER BY id""",
                asset, start, end
            )
            return [dict(row) for row in rows]

    async def get_stats(self) -> Dict:
        """Obter estatísticas do banco"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            total_ticks = await conn.fetchval("SELECT COUNT(*) FROM ticks")
            assets_count = await conn.fetchval("SELECT COUNT(DISTINCT asset) FROM ticks")
            return {
                "total_ticks": total_ticks,
                "assets_count": assets_count
            }

    async def reset_all(self):
        """Resetar todos os dados da tabela ticks"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM ticks")
            logger.info("Tabela ticks resetada completamente")

    async def update_asset_metadata(self, asset: str, payout: float):
        """Atualizar metadata do asset"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO asset_metadata (asset, payout, last_updated)
                VALUES ($1, $2, NOW())
                ON CONFLICT (asset) DO UPDATE SET
                payout = EXCLUDED.payout,
                last_updated = NOW()""",
                asset, payout
            )

    async def get_asset_metadata(self, asset: str) -> Optional[dict]:
        """Obter metadata do asset"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM asset_metadata WHERE asset = $1",
                asset
            )
            if row:
                return {
                    'asset': row['asset'],
                    'payout': float(row['payout']),
                    'last_updated': row['last_updated']
                }
            return None

    async def get_all_assets_metadata(self) -> List[dict]:
        """Obter metadata de todos os assets"""
        await self._initialize_db()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM asset_metadata ORDER BY payout DESC"
            )
            return [
                {
                    'asset': row['asset'],
                    'payout': float(row['payout']),
                    'last_updated': row['last_updated']
                }
                for row in rows
            ]

    async def close(self):
        """Fechar pool de conexões"""
        if self.pool:
            await self.pool.close()
            self.pool = None
