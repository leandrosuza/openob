"""Instalação de Dependências do Projeto OpenOB

Este script instala todas as dependências necessárias para o projeto.
Uso:
    python dependencies.py              # Instala dependências principais
    python dependencies.py --dev         # Instala dependências de desenvolvimento
    python dependencies.py --all        # Instala todas as dependências
"""

import subprocess
import sys
from typing import List


def install_packages(packages: List[str], description: str = ""):
    """Instala pacotes usando pip"""
    if description:
        print(f"\n{'='*60}")
        print(f"{description}")
        print(f"{'='*60}")

    for package in packages:
        print(f"\n📦 Instalando: {package}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado com sucesso")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {package}: {e}")
            return False
    return True


def main():
    """Função principal"""
    print("="*60)
    print("OpenOB - Instalação de Dependências")
    print("="*60)

    # Dependências principais
    main_deps = [
        "websockets>=12.0",
        "pydantic>=2.0.0",
    ]

    # Dependências de desenvolvimento
    dev_deps = [
        "pytest>=7.0",
        "pytest-asyncio>=0.21",
        "pytest-cov>=4.0",
        "black>=23.0",
        "ruff>=0.1.0",
        "mypy>=1.0.0",
    ]

    # Verificar argumentos
    install_dev = "--dev" in sys.argv or "--all" in sys.argv
    install_all = "--all" in sys.argv

    # Instalar dependências principais
    if not install_packages(main_deps, "📚 Dependências Principais"):
        print("\n❌ Falha ao instalar dependências principais")
        sys.exit(1)

    # Instalar dependências de desenvolvimento se solicitado
    if install_dev or install_all:
        if not install_packages(dev_deps, "🛠️  Dependências de Desenvolvimento"):
            print("\n❌ Falha ao instalar dependências de desenvolvimento")
            sys.exit(1)

    print("\n" + "="*60)
    print("✅ Instalação concluída com sucesso!")
    print("="*60)
    print("\nPara usar o projeto:")
    print("  python -m openob")
    print("\nPara rodar testes:")
    print("  pytest test/")
    print("\nPara formatação:")
    print("  black openob/")
    print("  ruff check openob/")
    print("  mypy openob/")

if __name__ == "__main__":
    main()
