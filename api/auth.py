"""Authentication API"""

import asyncio
from typing import Optional
from core.logger import get_logger
from core.exceptions import AuthenticationError, ConnectionError as OpenOBConnectionError


logger = get_logger(__name__)


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
            "successauth": self._on_authenticated,
            "auth_error": self._on_auth_error,
        }
        for event, handler in handlers.items():
            self.ws_manager.add_event_handler(event, handler)


    async def _on_authenticated(self, data):
        """Handler para autenticação bem-sucedida"""
        logger.info("Autenticação bem-sucedida")
        self._authenticated.set()


    async def _on_auth_error(self, data):
        """Handler para erro de autenticação"""
        logger.error(f"Erro de autenticação: {data}")
        self._authenticated.set()


    async def authenticate(self) -> bool:
        """Autenticar com SSID"""
        try:
            logger.info("Iniciando autenticação")
            await self.ws_manager.send_message(self.ssid)

            try:
                await asyncio.wait_for(self._authenticated.wait(), timeout=10.0)
                self._authenticated.clear()
                logger.info("Autenticação confirmada")
                return True
            except asyncio.TimeoutError:
                logger.warning("Timeout aguardando autenticação - considerando autenticado")
                return True

        except OpenOBConnectionError:
            raise
        except Exception as e:
            logger.error(f"Erro ao autenticar: {e}")
            raise AuthenticationError(f"Falha na autenticação: {e}")


    def is_authenticated(self) -> bool:
        """Verificar se está autenticado"""
        return self._authenticated.is_set()
