"""Script de inicialização do banco de dados

Cria tabelas automaticamente se não existirem e insere planos padrão.
"""

import asyncio
from repositories.repository_factory import RepositoryFactory
from config.settings import Settings


async def init_database():
    """Inicializar banco de dados e criar planos padrão"""
    print("="*60)
    print("Inicializando Banco de Dados")
    print("="*60)

    config = Settings.to_dict()
    db_type = config.get("DATABASE_TYPE", "sqlite")
    print(f"Tipo de banco: {db_type}")

    if db_type == "postgresql":
        print(f"Host: {config.get('POSTGRES_HOST')}")
        print(f"Port: {config.get('POSTGRES_PORT')}")
        print(f"Database: {config.get('POSTGRES_DB')}")
    else:
        print(f"Path: {config.get('SQLITE_PATH')}")

    print("\nInicializando repositórios...")

    # Inicializar plan repository (cria tabela e planos padrão)
    plan_repo = RepositoryFactory.create_plan_repository(config)
    await plan_repo._initialize_db()
    print("[OK] Tabela plans criada e planos padrão inseridos")

    # Inicializar subscription repository
    subscription_repo = RepositoryFactory.create_subscription_repository(config)
    await subscription_repo._initialize_db()
    print("[OK] Tabela subscriptions criada")

    # Inicializar transaction repository
    transaction_repo = RepositoryFactory.create_transaction_repository(config)
    await transaction_repo._initialize_db()
    print("[OK] Tabela transactions criada")

    # Inicializar user repository
    user_repo = RepositoryFactory.create_user_repository(config)
    await user_repo._initialize_db()
    print("[OK] Tabela users criada")

    # Inicializar tick repository
    tick_repo = RepositoryFactory.create_tick_repository(config)
    await tick_repo._initialize_db()
    print("[OK] Tabelas ticks e asset_metadata criadas")

    # Fechar conexões
    await plan_repo.close()
    await subscription_repo.close()
    await transaction_repo.close()
    await user_repo.close()
    await tick_repo.close()

    print("\n" + "="*60)
    print("Banco de dados inicializado com sucesso!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(init_database())
