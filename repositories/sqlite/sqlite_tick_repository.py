"""Implementação SQLite do repositório de ticks"""




import os
import asyncio
import aiosqlite
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from repositories.interfaces.tick_repository_interface import TickRepositoryInterface
from core.logger import get_logger
from core.exceptions import DatabaseError




logger = get_logger(__name__)




class SQLiteTickRepository(TickRepositoryInterface):
    """Repositório SQLite - Implementação atual"""




    def __init__(self, db_path: str = "data/openob_ticks.db"):
        self.db_path = db_path
        self.conn = None
        self._pending_ticks = []
        self._max_pending = 1000
        self._flush_task = None
        self._initialized = False
        self._flush_started = False
        self._lock = asyncio.Lock()
        logger.info(f"SQLite Repository inicializado: {db_path}")




    async def _initialize_db(self):
        """Setup inicial do banco"""
        if self._initialized:
            return

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA cache_size=-64000")
            await conn.execute("PRAGMA temp_store=MEMORY")
            await conn.execute("PRAGMA busy_timeout=5000")

            # Tabela de ticks
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                timestamp_unix INTEGER NOT NULL,
                price REAL NOT NULL,
                payout REAL,
                sequence_number INTEGER NOT NULL
            )
            """)

            # Migrar: adicionar coluna timestamp_unix se não existir (para bancos antigos)
            try:
                await conn.execute("ALTER TABLE ticks ADD COLUMN timestamp_unix INTEGER")
                # Preencher com dados existentes
                await conn.execute("UPDATE ticks SET timestamp_unix = CAST(strftime('%s', timestamp) AS INTEGER) WHERE timestamp_unix IS NULL")
                logger.info("Migração: coluna timestamp_unix adicionada")
            except aiosqlite.OperationalError:
                # Coluna já existe
                pass

            await conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_seq ON ticks(asset, sequence_number)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_time ON ticks(asset, timestamp_unix)")

            # Tabela de metadata
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_metadata (
                asset TEXT PRIMARY KEY,
                last_tick_timestamp DATETIME,
                last_tick_unix INTEGER,
                last_sequence_number INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                needs_reset BOOLEAN DEFAULT 0
            )
            """)

            # Migrar: adicionar coluna last_tick_unix se não existir
            try:
                await conn.execute("ALTER TABLE asset_metadata ADD COLUMN last_tick_unix INTEGER")
                logger.info("Migração: coluna last_tick_unix adicionada")
            except aiosqlite.OperationalError:
                # Coluna já existe
                pass

            # Migrar: adicionar coluna needs_reset se não existir
            try:
                await conn.execute("ALTER TABLE asset_metadata ADD COLUMN needs_reset BOOLEAN DEFAULT 0")
                logger.info("Migração: coluna needs_reset adicionada")
            except aiosqlite.OperationalError:
                # Coluna já existe
                pass

            await conn.commit()

        self._initialized = True


    async def _ensure_connection(self):
        """Verificar e restaurar conexão se necessário"""
        try:
            if not self._initialized:
                await self._initialize_db()
        except Exception as e:
            logger.error(f"Falha ao inicializar conexão com banco: {e}")
            raise DatabaseError(f"Falha ao conectar ao banco: {e}")


    def _add_to_pending(self, asset: str, price: float, payout: Optional[float], timestamp: datetime):
        """Adicionar tick ao buffer pendente"""
        if len(self._pending_ticks) < self._max_pending:
            self._pending_ticks.append({
                'asset': asset,
                'price': price,
                'payout': payout,
                'timestamp': timestamp
            })
            logger.debug(f"Tick adicionado ao buffer pendente: {len(self._pending_ticks)} ticks")


    async def _flush_pending(self):
        """Salvar ticks pendentes do buffer"""
        if not self._pending_ticks:
            return

        saved = 0
        for tick in self._pending_ticks[:]:
            try:
                await self.save(
                    tick['asset'],
                    tick['price'],
                    tick['payout'],
                    tick['timestamp']
                )
                saved += 1
            except Exception as e:
                logger.error(f"Erro ao salvar tick pendente: {e}")
                break

        if saved > 0:
            self._pending_ticks = self._pending_ticks[saved:]
            logger.info(f"Ticks pendentes salvos: {saved}/{len(self._pending_ticks + saved)}")


    async def _flush_loop(self):
        """Loop periódico para tentar salvar ticks pendentes"""
        while True:
            await asyncio.sleep(10)
            if self._pending_ticks:
                await self._flush_pending()




    async def _check_reset_needed(self, asset: str) -> bool:
        """Verifica se precisa reset (>30min)"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT last_tick_timestamp FROM asset_metadata WHERE asset = ?",
                (asset,)
            )
            result = await cursor.fetchone()

        if not result:
            return False

        last = datetime.fromisoformat(result[0])
        # Converter para UTC se necessário
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        return (now - last) > timedelta(minutes=30)




    async def _reset_asset(self, asset: str):
        """Resetar histórico do ativo"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("DELETE FROM ticks WHERE asset = ?", (asset,))
            await conn.execute(
                "UPDATE asset_metadata SET last_sequence_number = 0 WHERE asset = ?",
                (asset,)
            )
            await conn.commit()
        logger.debug(f"Resetado histórico de {asset}")




    async def _get_next_sequence(self, asset: str) -> int:
        """Próximo número de sequência"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT last_sequence_number FROM asset_metadata WHERE asset = ?",
                (asset,)
            )
            result = await cursor.fetchone()

        return (result[0] + 1) if result else 1




    async def _get_last_tick(self, asset: str) -> Optional[Dict]:
        """Obter último tick salvo do ativo"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM ticks WHERE asset = ? ORDER BY sequence_number DESC LIMIT 1",
                (asset,)
            )
            row = await cursor.fetchone()

        if not row:
            return None

        return {
            'timestamp': row[2],
            'price': row[3],
            'payout': row[4],
            'sequence': row[5]
        }




    async def _check_duplicate(self, asset: str, price: float, timestamp: datetime) -> bool:
        """Verificar se tick já existe (timestamp + preço único)"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT id FROM ticks WHERE asset = ? AND price = ? AND timestamp = ? LIMIT 1",
                (asset, price, timestamp.isoformat())
            )
            result = await cursor.fetchone()

        return result is not None




    async def _check_duplicate_unix(self, asset: str, price: float, timestamp_unix: int) -> bool:
        """Verificar duplicata usando timestamp Unix (mais preciso)"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT id FROM ticks WHERE asset = ? AND price = ? AND timestamp_unix = ? LIMIT 1",
                (asset, price, timestamp_unix)
            )
            result = await cursor.fetchone()

        return result is not None




    async def _update_metadata(self, asset: str, timestamp: datetime, sequence: int):
        """Atualizar metadata"""
        timestamp_unix = int(timestamp.timestamp())
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
            INSERT OR REPLACE INTO asset_metadata
            (asset, last_tick_timestamp, last_tick_unix, last_sequence_number, created_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM asset_metadata WHERE asset = ?), CURRENT_TIMESTAMP))
            """, (asset, timestamp.isoformat(), timestamp_unix, sequence, asset))
            await conn.commit()




    async def save(self, asset: str, price: float, payout: Optional[float] = None, timestamp: Optional[datetime] = None) -> int:
        """Salvar tick - Método principal com verificação de duplicatas e retry"""
        async with self._lock:
            try:
                # Iniciar flush loop na primeira chamada
                if not self._flush_started:
                    self._flush_task = asyncio.create_task(self._flush_loop())
                    self._flush_started = True

                await self._ensure_connection()

                # Usar timestamp fornecido ou atual (padronizado em UTC)
                if timestamp is None:
                    timestamp = datetime.now(timezone.utc)
                elif timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                # Usar timestamp Unix para precisão (truncar para segundos)
                timestamp_unix = int(timestamp.timestamp())
                timestamp_normalized = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)

                # Verificar duplicata usando timestamp Unix
                if await self._check_duplicate_unix(asset, price, timestamp_unix):
                    logger.debug(f"Tick duplicado ignorado: {asset} @ {price} @ {timestamp_normalized}")
                    return -1

                # Reset se >30min sem dados
                if await self._check_reset_needed(asset):
                    await self._reset_asset(asset)

                # Sequência incremental
                sequence = await self._get_next_sequence(asset)

                # Salvar com timestamp Unix normalizado
                async with aiosqlite.connect(self.db_path) as conn:
                    await conn.execute(
                        "INSERT INTO ticks (asset, timestamp, timestamp_unix, price, payout, sequence_number) VALUES (?, ?, ?, ?, ?, ?)",
                        (asset, timestamp_normalized.isoformat(), timestamp_unix, price, payout, sequence)
                    )

                    # Atualizar metadata
                    await self._update_metadata(asset, timestamp_normalized, sequence)

                    await conn.commit()

                logger.debug(f"Tick salvo: {asset} seq={sequence} price={price} @ {timestamp_normalized}")
                return sequence

            except aiosqlite.OperationalError as e:
                logger.error(f"Erro ao salvar tick no banco: {e}")
                self._add_to_pending(asset, price, payout, timestamp or datetime.now(timezone.utc))
                return -1
            except Exception as e:
                logger.error(f"Erro inesperado ao salvar tick: {e}")
                self._add_to_pending(asset, price, payout, timestamp or datetime.now(timezone.utc))
                return -1




    async def sync_and_save_batch(self, asset: str, new_ticks: List[Dict], limit: int = 500) -> int:
        """Sincronizar batch de ticks verificando duplicatas com histórico recente"""
        saved_count = 0

        # Obter últimos N ticks do histórico
        recent_history = await self.get_recent(asset, limit=limit)

        # Criar set de (timestamp_unix, price) para verificação precisa
        history_set = {(tick['timestamp'], tick['price']) for tick in recent_history}

        # Ordenar ticks por timestamp para garantir ordem cronológica
        sorted_ticks = sorted(new_ticks, key=lambda x: x.get('timestamp', datetime.min))

        for tick in sorted_ticks:
            timestamp = tick.get('timestamp')
            price = tick.get('price')
            payout = tick.get('payout')

            # Se não tiver timestamp, usar atual
            if not timestamp:
                timestamp = datetime.now(timezone.utc)
            elif isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # Converter para timestamp Unix para precisão
            timestamp_unix = int(timestamp.timestamp())
            timestamp_normalized = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)
            key = (timestamp_normalized.isoformat(), price)

            # Verificar se já existe no histórico
            if key in history_set:
                logger.debug(f"Tick já existe no histórico: {asset} @ {price} @ {timestamp_normalized}")
                continue

            # Salvar novo tick com timestamp específico
            sequence = await self.save(asset, price, payout, timestamp)
            if sequence > 0:
                saved_count += 1
                history_set.add(key)

        logger.info(f"Sincronização {asset}: {saved_count}/{len(new_ticks)} ticks salvos")
        return saved_count





    async def get_recent(self, asset: str, limit: int = 100) -> List[Dict]:
        """Obter ticks recentes"""
        try:
            await self._ensure_connection()
            query = f"SELECT * FROM ticks WHERE asset = ? ORDER BY sequence_number DESC LIMIT {limit}"
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute(query, (asset,))
                rows = await cursor.fetchall()

            return [
                {
                    'timestamp': row[2],
                    'price': row[3],
                    'payout': row[4],
                    'sequence': row[5]
                }
                for row in reversed(rows)
            ]
        except Exception as e:
            logger.error(f"Erro ao obter ticks recentes: {e}")
            return []





    async def get_by_sequence(self, asset: str, start: int, end: int) -> List[Dict]:
        """Obter range de sequência"""
        try:
            await self._ensure_connection()
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute(
                    "SELECT * FROM ticks WHERE asset = ? AND sequence_number BETWEEN ? AND ? ORDER BY sequence_number",
                    (asset, start, end)
                )
                rows = await cursor.fetchall()

            return [
                {
                    'timestamp': row[2],
                    'price': row[3],
                    'payout': row[4],
                    'sequence': row[5]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Erro ao obter ticks por sequência: {e}")
            return []





    async def get_stats(self) -> Dict:
        """Estatísticas do banco"""
        try:
            await self._ensure_connection()
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM ticks")
                total = (await cursor.fetchone())[0]
                cursor = await conn.execute("SELECT COUNT(DISTINCT asset) FROM ticks")
                assets = (await cursor.fetchone())[0]

            return {
                'total_ticks': total,
                'total_assets': assets,
                'db_size_mb': os.path.getsize(self.db_path) / (1024 * 1024),
                'pending_ticks': len(self._pending_ticks)
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                'total_ticks': 0,
                'total_assets': 0,
                'db_size_mb': 0,
                'pending_ticks': len(self._pending_ticks)
            }





    async def close(self):
        """Fechar conexão"""
        if self._flush_task:
            self._flush_task.cancel()
        logger.info("SQLite Repository fechado")
