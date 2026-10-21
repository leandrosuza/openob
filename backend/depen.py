"""Instalação de Dependências do OpenOB

Uso:
    python depen.py              # Instala dependências principais
    python depen.py --dev        # Instala dependências de desenvolvimento
    python depen.py --upgrade    # Atualiza dependências existentes
"""

import subprocess
import sys
import os


def install_from_pyproject(dev: bool = False, upgrade: bool = False):
    """Instala dependências do pyproject.toml"""
    print("="*60)
    print("OpenOB - Instalação de Dependências")
    print("="*60)

    # Lista de dependências principais
    packages = [
        "websockets>=12.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "bcrypt>=4.0.0",
        "passlib[bcrypt]>=1.7.4",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "python-jose[cryptography]>=3.3.0",
        "python-multipart>=0.0.6",
        "email-validator>=2.0.0",
        "slowapi>=0.1.9",
        "pydantic-settings>=2.0.0",
        "aiosqlite>=0.19.0",
        "asyncpg>=0.29.0",  # PostgreSQL async driver
        "psycopg2-binary>=2.9.0",  # PostgreSQL sync driver
        "anyio>=3.7.0",  # Async framework
    ]

    if dev:
        packages.extend([
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.0",
            "black>=23.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ])

    cmd = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.extend(packages)

    print(f"\nInstalando: {len(packages)} pacotes")
    if upgrade:
        print("   (modo upgrade)")

    try:
        subprocess.check_call(cmd)
        print("\n" + "="*60)
        print("Instalacao concluida com sucesso!")
        print("="*60)
        print("\nPara usar o projeto:")
        print("  python boot.py          # Monitoramento WebSocket")
        print("  python boot.py api      # Servidor API HTTP")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nErro ao instalar dependencias: {e}")
        return False


def main():
    """Função principal"""
    dev = "--dev" in sys.argv
    upgrade = "--upgrade" in sys.argv

    # Verificar se pyproject.toml existe
    if not os.path.exists("pyproject.toml"):
        print("pyproject.toml nao encontrado no diretorio atual")
        print("Execute este script na raiz do projeto")
        sys.exit(1)

    install_from_pyproject(dev=dev, upgrade=upgrade)


if __name__ == "__main__":
    main()
