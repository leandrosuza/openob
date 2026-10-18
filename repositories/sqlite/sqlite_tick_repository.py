"""Implementação SQLite do repositório de ticks"""

import os
import sqlite3
import asyncio
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from repositories.interfaces.tick_repository_interface import TickRepositoryInterface
from core.logger import get_logger
from core.exceptions import DatabaseError

logger = get_logger(__name__)


class SQLiteTickRepository(TickRepositoryInterface):
    """Repositório SQLite - Implementação com asyncio.to_thread()"""

    def __init__(self, db_path: str = "data/openob_ticks.db"):
        self.db_path = db_path
        self.conn = None
        self._pending_ticks = []
        self._max_pending = 1000
        self._flush_task = None
        self._initialized = False
        self._flush_started = False
        self._lock = asyncio.Lock()
        self._thread_lock = threading.Lock()  # Lock para proteger sqlite3 de threads concorrentes
        self._startup_time = datetime.now(timezone.utc)  # Timestamp de inicialização do repositório

        # Inicializar banco de forma síncrona no __init__
        self._initialize_db_sync()
        logger.info(f"SQLite Repository inicializado: {db_path}")

    def _initialize_db_sync(self):
        """Setup inicial do banco (síncrono)"""
        with self._thread_lock:
            if self._initialized:
                return

            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=-64000")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            self.conn.execute("PRAGMA busy_timeout=5000")

            # Tabela de ticks
            self.conn.execute("""
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

            # Migrar: adicionar coluna timestamp_unix se não existir
            try:
                self.conn.execute("ALTER TABLE ticks ADD COLUMN timestamp_unix INTEGER")
                self.conn.execute("UPDATE ticks SET timestamp_unix = CAST(strftime('%s', timestamp) AS INTEGER) WHERE timestamp_unix IS NULL")
                logger.info("Migração: coluna timestamp_unix adicionada")
            except sqlite3.OperationalError:
                pass

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_seq ON ticks(asset, sequence_number)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_time ON ticks(asset, timestamp_unix)")

            # Tabela de metadata
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_metadata (
                asset TEXT PRIMARY KEY,
                last_tick_timestamp DATETIME,
                last_sequence_number INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                needs_reset BOOLEAN DEFAULT 0,
                last_tick_unix INTEGER
            )
            """)

            # Migrar: adicionar coluna last_tick_unix
            try:
                self.conn.execute("ALTER TABLE asset_metadata ADD COLUMN last_tick_unix INTEGER")
                logger.info("Migração: coluna last_tick_unix adicionada")
            except sqlite3.OperationalError:
                pass

            # Migrar: adicionar coluna needs_reset
            try:
                self.conn.execute("ALTER TABLE asset_metadata ADD COLUMN needs_reset BOOLEAN DEFAULT 0")
                logger.info("Migração: coluna needs_reset adicionada")
            except sqlite3.OperationalError:
                pass

            self.conn.commit()
            self._initialized = True

    async def _initialize_db(self):
        """Setup inicial do banco (async wrapper)"""
        await asyncio.to_thread(self._initialize_db_sync)

    async def _ensure_connection(self):
        """Verificar e restaurar conexão se necessário"""
        try:
            if self.conn:
                await asyncio.to_thread(self.conn.execute, "SELECT 1")
            else:
                await self._initialize_db()
        except Exception as e:
            logger.warning(f"Conexão com banco perdida, tentando reconectar: {e}")
            try:
                await self._initialize_db()
                logger.info("Conexão com banco restaurada")
            except Exception as e:
                logger.error(f"Falha ao reconectar ao banco: {e}")
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

    def _check_reset_needed_sync(self, asset: str) -> bool:
        """Verifica se precisa reset (>1min) - DESABILITADO"""
        return False

    async def _check_reset_needed(self, asset: str) -> bool:
        """Verifica se precisa reset (>1min)"""
        return await asyncio.to_thread(self._check_reset_needed_sync, asset)

    def _reset_asset_sync(self, asset: str):
        """Resetar histórico do ativo - síncrono (sem lock interno, chamado de dentro de lock)"""
        self.conn.execute("DELETE FROM ticks WHERE asset = ?", (asset,))
        self.conn.execute(
            "UPDATE asset_metadata SET last_sequence_number = 0 WHERE asset = ?",
            (asset,)
        )
        self.conn.commit()
        logger.info(f"Histórico resetado para {asset} (gap > 1min detectado)")

    async def _reset_asset(self, asset: str):
        """Resetar histórico do ativo"""
        await asyncio.to_thread(self._reset_asset_sync, asset)

    async def reset_asset(self, asset: str):
        """Resetar histórico do ativo (método público)"""
        await self._reset_asset(asset)

    async def reset_all(self):
        """Resetar todos os dados da tabela ticks"""
        await asyncio.to_thread(self._reset_all_sync)

    def _reset_all_sync(self):
        """Resetar todos os dados - síncrono"""
        with self._thread_lock:
            self.conn.execute("DELETE FROM ticks")
            self.conn.execute("DELETE FROM asset_metadata")
            self.conn.commit()
            logger.info("Tabela ticks resetada completamente")

    def _get_next_sequence_sync(self, asset: str) -> int:
        """Próximo número de sequência - síncrono (sem lock interno, chamado de dentro de lock)"""
        result = self.conn.execute(
            "SELECT last_sequence_number FROM asset_metadata WHERE asset = ?",
            (asset,)
        ).fetchone()

        return (result[0] + 1) if result else 1

    async def _get_next_sequence(self, asset: str) -> int:
        """Próximo número de sequência"""
        return await asyncio.to_thread(self._get_next_sequence_sync, asset)

    def _get_last_tick_sync(self, asset: str) -> Optional[Dict]:
        """Obter último tick salvo do ativo - síncrono"""
        with self._thread_lock:
            row = self.conn.execute(
                "SELECT * FROM ticks WHERE asset = ? ORDER BY sequence_number DESC LIMIT 1",
                (asset,)
            ).fetchone()

            if not row:
                return None

            return {
                'timestamp': row[2],
                'price': row[3],
                'payout': row[4],
                'sequence': row[5]
            }

    async def _get_last_tick(self, asset: str) -> Optional[Dict]:
        """Obter último tick salvo do ativo"""
        return await asyncio.to_thread(self._get_last_tick_sync, asset)

    def _check_duplicate_sync(self, asset: str, price: float, timestamp: datetime) -> bool:
        """Verificar se tick já existe - síncrono"""
        with self._thread_lock:
            result = self.conn.execute(
                "SELECT id FROM ticks WHERE asset = ? AND price = ? AND timestamp = ? LIMIT 1",
                (asset, price, timestamp.isoformat())
            ).fetchone()

            return result is not None

    async def _check_duplicate(self, asset: str, price: float, timestamp: datetime) -> bool:
        """Verificar se tick já existe (timestamp + preço único)"""
        return await asyncio.to_thread(self._check_duplicate_sync, asset, price, timestamp)

    def _check_duplicate_unix_sync(self, asset: str, price: float, timestamp_unix: int) -> bool:
        """Verificar duplicata usando timestamp Unix - síncrono (sem lock interno, chamado de dentro de lock)"""
        result = self.conn.execute(
            "SELECT id FROM ticks WHERE asset = ? AND price = ? AND timestamp_unix = ? LIMIT 1",
            (asset, price, timestamp_unix)
        ).fetchone()

        return result is not None

    async def _check_duplicate_unix(self, asset: str, price: float, timestamp_unix: int) -> bool:
        """Verificar duplicata usando timestamp Unix (mais preciso)"""
        return await asyncio.to_thread(self._check_duplicate_unix_sync, asset, price, timestamp_unix)

    def _update_metadata_sync(self, asset: str, timestamp: datetime, sequence: int):
        """Atualizar metadata - síncrono (sem lock interno, chamado de dentro de lock)"""
        timestamp_unix = int(timestamp.timestamp())
        self.conn.execute("""
        INSERT OR REPLACE INTO asset_metadata
        (asset, last_tick_timestamp, last_sequence_number, created_at, needs_reset, last_tick_unix)
        VALUES (?, ?, ?, COALESCE((SELECT created_at FROM asset_metadata WHERE asset = ?), CURRENT_TIMESTAMP), 0, ?)
        """, (asset, timestamp.isoformat(), sequence, asset, timestamp_unix))
        self.conn.commit()

    async def _update_metadata(self, asset: str, timestamp: datetime, sequence: int):
        """Atualizar metadata"""
        await asyncio.to_thread(self._update_metadata_sync, asset, timestamp, sequence)

    def _save_tick_sync(self, asset: str, price: float, payout: Optional[float], timestamp: datetime) -> int:
        """Salvar tick - síncrono"""
        with self._thread_lock:
            timestamp_unix = int(timestamp.timestamp())
            timestamp_normalized = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)

            # Verificar duplicata
            if self._check_duplicate_unix_sync(asset, price, timestamp_unix):
                return -1

            # Reset se >1min sem dados (garante histórico recente)
            if self._check_reset_needed_sync(asset):
                self._reset_asset_sync(asset)

            # Sequência incremental
            sequence = self._get_next_sequence_sync(asset)

            # Salvar
            self.conn.execute(
                "INSERT INTO ticks (asset, timestamp, timestamp_unix, price, payout, sequence_number) VALUES (?, ?, ?, ?, ?, ?)",
                (asset, timestamp_normalized.isoformat(), timestamp_unix, price, payout, sequence)
            )

            # Atualizar metadata
            self._update_metadata_sync(asset, timestamp_normalized, sequence)

            # Commit para persistir no disco
            self.conn.commit()

            return sequence

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

                # Salvar em thread separada
                sequence = await asyncio.to_thread(self._save_tick_sync, asset, price, payout, timestamp)

                if sequence > 0:
                    logger.debug(f"Tick salvo: {asset} seq={sequence} price={price}")
                else:
                    logger.debug(f"Tick duplicado ignorado: {asset} @ {price}")

                return sequence

            except sqlite3.OperationalError as e:
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

    def _get_recent_sync(self, asset: str, limit: int) -> List[Dict]:
        """Obter ticks recentes - síncrono"""
        with self._thread_lock:
            query = f"SELECT * FROM ticks WHERE asset = ? ORDER BY sequence_number DESC LIMIT {limit}"
            rows = self.conn.execute(query, (asset,)).fetchall()

            return [
                {
                    'timestamp': row[2],
                    'price': row[3],
                    'payout': row[4],
                    'sequence': row[5]
                }
                for row in reversed(rows)
            ]

    async def get_recent(self, asset: str, limit: int = 100) -> List[Dict]:
        """Obter ticks recentes"""
        try:
            await self._ensure_connection()
            return await asyncio.to_thread(self._get_recent_sync, asset, limit)
        except Exception as e:
            logger.error(f"Erro ao obter ticks recentes: {e}")
            return []

    def _get_by_sequence_sync(self, asset: str, start: int, end: int) -> List[Dict]:
        """Obter range de sequência - síncrono"""
        with self._thread_lock:
            rows = self.conn.execute(
                "SELECT * FROM ticks WHERE asset = ? AND sequence_number BETWEEN ? AND ? ORDER BY sequence_number",
                (asset, start, end)
            ).fetchall()

            return [
                {
                    'timestamp': row[2],
                    'price': row[3],
                    'payout': row[4],
                    'sequence': row[5]
                }
                for row in rows
            ]

    async def get_by_sequence(self, asset: str, start: int, end: int) -> List[Dict]:
        """Obter range de sequência"""
        try:
            await self._ensure_connection()
            return await asyncio.to_thread(self._get_by_sequence_sync, asset, start, end)
        except Exception as e:
            logger.error(f"Erro ao obter ticks por sequência: {e}")
            return []

    def _get_stats_sync(self) -> Dict:
        """Estatísticas do banco - síncrono"""
        with self._thread_lock:
            total = self.conn.execute("SELECT COUNT(*) FROM ticks").fetchone()[0]
            assets = self.conn.execute("SELECT COUNT(DISTINCT asset) FROM ticks").fetchone()[0]

            return {
                'total_ticks': total,
                'total_assets': assets,
                'db_size_mb': os.path.getsize(self.db_path) / (1024 * 1024),
                'pending_ticks': len(self._pending_ticks)
            }

    async def get_stats(self) -> Dict:
        """Estatísticas do banco"""
        try:
            await self._ensure_connection()
            return await asyncio.to_thread(self._get_stats_sync)
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                'total_ticks': 0,
                'total_assets': 0,
                'db_size_mb': 0,
                'pending_ticks': len(self._pending_ticks)
            }

    def _close_sync(self):
        """Fechar conexão - síncrono"""
        if self._flush_task:
            self._flush_task.cancel()
        
        if self.conn:
            self.conn.close()
            self.conn = None
        
        logger.info("SQLite Repository fechado")

    async def close(self):
        """Fechar conexão"""
        await asyncio.to_thread(self._close_sync)
