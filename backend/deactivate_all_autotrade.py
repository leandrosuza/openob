"""Script para desativar todas as configs de autotrade"""

import asyncio
import asyncpg
from config.settings import Settings

async def deactivate_all():
    """Desativar is_active em todas as configs de autotrade"""
    conn = await asyncpg.connect(
        host=Settings.POSTGRES_HOST,
        port=Settings.POSTGRES_PORT,
        user=Settings.POSTGRES_USER,
        password=Settings.POSTGRES_PASSWORD,
        database=Settings.POSTGRES_DB
    )

    try:
        # Atualizar todas as configs para is_active=False
        result = await conn.execute(
            "UPDATE autotrade_configs SET is_active = FALSE"
        )
        print(f"[OK] {result} configs desativadas")

        # Verificar resultado
        rows = await conn.fetch("SELECT user_id, is_active FROM autotrade_configs")
        print(f"\nStatus atual:")
        for row in rows:
            print(f"  User {row['user_id']}: is_active={row['is_active']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(deactivate_all())
