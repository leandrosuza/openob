"""Script para iniciar servidor API HTTP

Este script inicia o servidor FastAPI para a API HTTP REST,
separado do monitoramento WebSocket (boot.py).

Uso:
    python api_server.py

Ou com uvicorn diretamente:
    uvicorn api.http_main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
sys.path.insert(0, '.')

from api.rest.http_main import app
import uvicorn


if __name__ == "__main__":
    print("=" * 60)
    print("OpenOB API HTTP Server")
    print("=" * 60)
    print("Iniciando servidor em http://0.0.0.0:8000")
    print("Documentação: http://localhost:8000/docs")
    print("Pressione Ctrl+C para encerrar")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload em desenvolvimento
    )
