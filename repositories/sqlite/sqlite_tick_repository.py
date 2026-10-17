"""Implementação SQLite do repositório de ticks"""

import sqlite3
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from repositories.interfaces.tick_repository_interface import TickRepositoryInterface
from core.logger import get_logger




logger = get_logger(__name__)




class SQLiteTickRepository(TickRepositoryInterface):
    """Repositório SQLite - Implementação atual"""

    def __init__(self, db_path: str = "data/openob_ticks.db"):
        self.db_path = db_path
        self.conn = None
        self._lock = asyncio.Lock()
        self._initialize_db()
        logger.info(f"SQLite Repository inicializado: {db_path}")




    def _initialize_db(self):
        """Setup inicial do banco"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, isolation_level=None)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000")
        self.conn.execute("PRAGMA temp_store=MEMORY")

        # Tabela de ticks
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            price REAL NOT NULL,
            payout REAL,
            sequence_number INTEGER NOT NULL
        )
        """)

        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_seq ON ticks(asset, sequence_number)")

        # Tabela de metadata
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS asset_metadata (
            asset TEXT PRIMARY KEY,
            last_tick_timestamp DATETIME,
            last_sequence_number INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            needs_reset BOOLEAN DEFAULT 0
        )
        """)




    def _check_reset_needed(self, asset: str) -> bool:
        """Verifica se precisa reset (>30min)"""
        result = self.conn.execute(
            "SELECT last_tick_timestamp FROM asset_metadata WHERE asset = ?",
            (asset,)
        ).fetchone()

        if not result:
            return False

        last = datetime.fromisoformat(result[0])
        return (datetime.now() - last) > timedelta(minutes=30)




    def _reset_asset(self, asset: str):
        """Resetar histórico do ativo"""
        self.conn.execute("DELETE FROM ticks WHERE asset = ?", (asset,))
        self.conn.execute(
            "UPDATE asset_metadata SET last_sequence_number = 0 WHERE asset = ?",
            (asset,)
        )
        logger.debug(f"Resetado histórico de {asset}")




    def _get_next_sequence(self, asset: str) -> int:
        """Próximo número de sequência"""
        result = self.conn.execute(
            "SELECT last_sequence_number FROM asset_metadata WHERE asset = ?",
            (asset,)
        ).fetchone()

        return (result[0] + 1) if result else 1




    def _get_last_tick(self, asset: str) -> Optional[Dict]:
        """Obter último tick salvo do ativo"""
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




    def _check_duplicate(self, asset: str, price: float, timestamp: datetime) -> bool:
        """Verificar se tick já existe (timestamp + preço único)"""
        result = self.conn.execute(
            "SELECT id FROM ticks WHERE asset = ? AND price = ? AND timestamp = ? LIMIT 1",
            (asset, price, timestamp.isoformat())
        ).fetchone()

        return result is not None




    def _update_metadata(self, asset: str, timestamp: datetime, sequence: int):
        """Atualizar metadata"""
        self.conn.execute("""
        INSERT OR REPLACE INTO asset_metadata
        (asset, last_tick_timestamp, last_sequence_number, created_at)
        VALUES (?, ?, ?, COALESCE((SELECT created_at FROM asset_metadata WHERE asset = ?), CURRENT_TIMESTAMP))
        """, (asset, timestamp.isoformat(), sequence, asset))




    async def save(self, asset: str, price: float, payout: Optional[float] = None, timestamp: Optional[datetime] = None) -> int:
        """Salvar tick - Método principal com verificação de duplicatas"""
        async with self._lock:
            # Usar timestamp fornecido ou atual
            if timestamp is None:
                timestamp = datetime.now()

            # Verificar duplicata
            if self._check_duplicate(asset, price, timestamp):
                logger.debug(f"Tick duplicado ignorado: {asset} @ {price} @ {timestamp}")
                return -1

            # Reset se >30min sem dados
            if self._check_reset_needed(asset):
                self._reset_asset(asset)

            # Sequência incremental
            sequence = self._get_next_sequence(asset)

            # Salvar
            self.conn.execute(
                "INSERT INTO ticks (asset, timestamp, price, payout, sequence_number) VALUES (?, ?, ?, ?, ?)",
                (asset, timestamp.isoformat(), price, payout, sequence)
            )

            # Atualizar metadata
            self._update_metadata(asset, timestamp, sequence)

            logger.debug(f"Tick salvo: {asset} seq={sequence} price={price} @ {timestamp}")
            return sequence




    async def sync_and_save_batch(self, asset: str, new_ticks: List[Dict], limit: int = 50) -> int:
        """Sincronizar batch de ticks verificando duplicatas com histórico recente"""
        saved_count = 0

        # Obter últimos N ticks do histórico
        recent_history = self.get_recent(asset, limit=limit)

        # Criar set de (timestamp, price) para verificação precisa
        history_set = {(tick['timestamp'], tick['price']) for tick in recent_history}

        for tick in new_ticks:
            timestamp = tick.get('timestamp')
            price = tick.get('price')
            payout = tick.get('payout')

            # Se não tiver timestamp, usar atual
            if not timestamp:
                timestamp = datetime.now()
            elif isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)

            key = (timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp, price)

            # Verificar se já existe no histórico
            if key in history_set:
                logger.debug(f"Tick já existe no histórico: {asset} @ {price} @ {timestamp}")
                continue

            # Salvar novo tick com timestamp específico
            sequence = await self.save(asset, price, payout, timestamp)
            if sequence > 0:
                saved_count += 1
                history_set.add(key)

        logger.info(f"Sincronização {asset}: {saved_count}/{len(new_ticks)} ticks salvos")
        return saved_count




    def get_recent(self, asset: str, limit: int = 100) -> List[Dict]:
        """Obter ticks recentes"""
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




    def get_by_sequence(self, asset: str, start: int, end: int) -> List[Dict]:
        """Obter range de sequência"""
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




    def get_stats(self) -> Dict:
        """Estatísticas do banco"""
        total = self.conn.execute("SELECT COUNT(*) FROM ticks").fetchone()[0]
        assets = self.conn.execute("SELECT COUNT(DISTINCT asset) FROM ticks").fetchone()[0]

        return {
            'total_ticks': total,
            'total_assets': assets,
            'db_size_mb': os.path.getsize(self.db_path) / (1024 * 1024)
        }




    def close(self):
        """Fechar conexão"""
        if self.conn:
            self.conn.close()
            logger.info("SQLite Repository fechado")
