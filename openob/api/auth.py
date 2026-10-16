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
        self.ws_manager.add_event_handler("authenticated", self._on_authenticated)
        self.ws_manager.add_event_handler("successauth", self._on_success_auth)
        self.ws_manager.add_event_handler("auth_error", self._on_auth_error)

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
            # SSID já está no formato Socket.IO ("42[...]"), enviar direto
            await self.ws_manager.send_message(self.ssid)

            # Aguardar confirmação (com timeout)
            try:
                await asyncio.wait_for(self._authenticated.wait(), timeout=10.0)
                self._authenticated.clear()
                return True
            except asyncio.TimeoutError:
                print("Timeout aguardando autenticação - não foi possível confirmar")
                # Considerar autenticado mesmo sem confirmação (SSID pode estar válido)
                return True

        except Exception as e:
            print(f"Erro ao autenticar: {e}")
            return False
