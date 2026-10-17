"""
Authentication API
"""

import asyncio
from typing import Optional
from openob.core.constants import REGIONS


class AuthAPI:
    """API de autenticação"""

    def __init__(self, ws_manager, ssid: str):
        self.ws_manager = ws_manager
        self.ssid = ssid
        self._authenticated = asyncio.Event()
        self._setup_handlers()





    def _setup_handlers(self):
        """Configurar handlers de eventos"""
        handlers = {
            "authenticated": self._on_authenticated,
            "successauth": self._on_success_auth,
            "auth_error": self._on_auth_error,
        }
        for event, handler in handlers.items():
            self.ws_manager.add_event_handler(event, handler)





    async def _on_authenticated(self, data):
        """Handler para autenticação"""
        self._authenticated.set()





    async def _on_success_auth(self, data):
        """Handler para sucesso da autenticação"""
        self._authenticated.set()





    async def _on_auth_error(self, data):
        """Handler para erro de autenticação"""
        print(f"Erro de autenticação: {data}")
        self._authenticated.set()





    async def authenticate(self) -> bool:
        """Autenticar com SSID"""
        try:
            await self.ws_manager.send_message(self.ssid)

            try:
                await asyncio.wait_for(self._authenticated.wait(), timeout=10.0)
                self._authenticated.clear()
                return True
            except asyncio.TimeoutError:
                print("Timeout aguardando autenticação - não foi possível confirmar")
                return True

        except Exception as e:
            print(f"Erro ao autenticar: {e}")
            return False





    def is_authenticated(self) -> bool:
        """Verificar se está autenticado"""
        return self._authenticated.is_set()
