"""WebSocket Manager for PocketOption"""

import asyncio
import json
import ssl
from core.constants import WEBSOCKET_ENDPOINTS, CONNECTION_SETTINGS
from core.logger import get_logger
from core.exceptions import ConnectionError as OpenOBConnectionError


logger = get_logger(__name__)

DEFAULT_HEADERS = {
    "Origin": "https://pocketoption.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


class WebSocketManager:
    """Gerenciador de conexão WebSocket"""

    def __init__(self, region: str = "DEMO", name: str = "WebSocket"):
        self.region = region
        self.name = name
        self.websocket = None
        self._event_handlers = {}
        self._running = False
        self._receive_task = None
        self._ping_task = None
        self._reconnect_task = None
        self._binary_buffer = None
        self._binary_event = None
        self._ssid = None
        self._ssl_context = None
        self._should_reconnect = False
        self._reconnect_attempts = 0
        self._create_ssl_context()


    def _create_ssl_context(self):
        """Criar contexto SSL reutilizável"""
        self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self._ssl_context.check_hostname = False
        self._ssl_context.verify_mode = ssl.CERT_NONE


    @property
    def is_connected(self):
        """Verificar se está conectado"""
        return self.websocket is not None


    async def connect(self, ssid: str = None, auto_reconnect: bool = False) -> bool:
        """Conectar ao servidor"""
        import websockets.legacy.client

        self._ssid = ssid
        self._should_reconnect = auto_reconnect
        self._reconnect_attempts = 0

        endpoints = [WEBSOCKET_ENDPOINTS.get(self.region)] + [v for k, v in WEBSOCKET_ENDPOINTS.items() if k != self.region]

        for endpoint in endpoints:
            try:
                logger.debug(f"Tentando conectar a {endpoint}")

                self.websocket = await websockets.legacy.client.connect(
                    endpoint,
                    ssl=self._ssl_context,
                    extra_headers=DEFAULT_HEADERS,
                    ping_interval=CONNECTION_SETTINGS["ping_interval"],
                    ping_timeout=CONNECTION_SETTINGS["ping_timeout"],
                    close_timeout=CONNECTION_SETTINGS.get("close_timeout", 10),
                )
                logger.debug("Conectado com sucesso")

                if not await self._handshake(ssid):
                    await self.websocket.close()
                    self.websocket = None
                    continue

                self._running = True
                self._receive_task = asyncio.create_task(self._receive_messages())
                self._ping_task = asyncio.create_task(self._ping_loop())

                if auto_reconnect:
                    self._reconnect_task = asyncio.create_task(self._auto_reconnect_loop())

                logger.debug("Handshake completo")
                return True

            except Exception as e:
                logger.error(f"Falha ao conectar a {endpoint}: {e}")
                if self.websocket:
                    await self.websocket.close()
                    self.websocket = None
                continue

        raise OpenOBConnectionError(f"Falha ao conectar a todos os endpoints para região {self.region}")


    async def _handshake(self, ssid: str = None) -> bool:
        """Executar handshake Socket.IO"""
        try:
            initial_message = await self.websocket.recv()
            logger.debug(f"Mensagem inicial: {initial_message[:100]}...")

            if not (initial_message.startswith("0") and "sid" in initial_message):
                raise OpenOBConnectionError("Formato de handshake inválido")

            await self.websocket.send("40")
            logger.debug("Handshake '40' enviado")

            conn_message = await self.websocket.recv()
            logger.debug(f"Mensagem de conexão: {conn_message[:100]}...")

            if not (conn_message.startswith("40") and "sid" in conn_message):
                raise OpenOBConnectionError("Formato de conexão inválido")

            if ssid:
                await self.websocket.send(ssid)
                logger.debug("SSID enviado durante handshake")

            return True
        except Exception as e:
            if isinstance(e, OpenOBConnectionError):
                raise
            raise OpenOBConnectionError(f"Erro durante handshake: {e}")


    async def _ping_loop(self):
        """Enviar ping periodicamente para manter conexão viva"""
        while self._running and self.websocket:
            try:
                await asyncio.sleep(20)
                if self._running and self.websocket:
                    await self.websocket.send('42["ps"]')
                    logger.debug("Ping enviado")
            except Exception as e:
                logger.error(f"Erro ao enviar ping: {e}")
                break


    async def _auto_reconnect_loop(self):
        """Loop de reconexão automática com exponential backoff"""
        while self._should_reconnect:
            if not self._running or not self.websocket:
                await asyncio.sleep(self._get_reconnect_delay())

                if not self._should_reconnect:
                    break

                logger.info(f"Tentando reconectar ({self.name}) - Tentativa {self._reconnect_attempts + 1}")
                success = await self.connect(self._ssid, auto_reconnect=True)

                if success:
                    self._reconnect_attempts = 0
                    logger.info(f"Reconexão bem-sucedida ({self.name})")
                else:
                    self._reconnect_attempts += 1
                    max_attempts = CONNECTION_SETTINGS.get("max_reconnect_attempts", 3)

                    if self._reconnect_attempts >= max_attempts:
                        logger.error(f"Máximo de tentativas de reconexão atingido ({self.name})")
                        self._should_reconnect = False
            else:
                await asyncio.sleep(5)


    def _get_reconnect_delay(self) -> float:
        """Calcular delay de reconexão com exponential backoff"""
        base_delay = CONNECTION_SETTINGS.get("reconnect_delay", 5)
        exponential_delay = base_delay * (2 ** min(self._reconnect_attempts, 5))
        return min(exponential_delay, 60)


    async def _receive_messages(self):
        """Receber mensagens do WebSocket com reconexão automática"""
        while self._running and self.websocket:
            try:
                message = await self.websocket.recv()
                await self._process_message(message)
            except Exception as e:
                logger.error(f"Erro ao receber mensagem: {e}")
                break

        if self._should_reconnect:
            logger.warning(f"Conexão perdida, reconexão automática iniciada ({self.name})")
        else:
            logger.info(f"Conexão encerrada ({self.name})")


    async def _process_message(self, message):
        """Processar mensagem recebida"""
        try:
            if isinstance(message, bytes):
                if self._binary_event:
                    self._handle_binary_data(message)
                else:
                    message = message.decode("utf-8")

            if isinstance(message, str):
                if message.startswith("451-"):
                    self._handle_binary_message(message)
                elif message.startswith("42"):
                    self._handle_socketio_message(message)
                else:
                    self._handle_json_message(message)

        except Exception as e:
            logger.debug(f"Erro ao processar mensagem: {e}")


    def _handle_binary_message(self, message: str):
        """Handle mensagem binária Socket.IO"""
        if "[" not in message:
            return

        parts = message.split("[", 1)
        if "]" not in parts[1]:
            return

        event_part = parts[1].split("]", 1)[0]
        event = event_part.strip('"')
        self._binary_event = event
        asyncio.create_task(self._emit_event(event, {"_placeholder": True, "num": 0}))


    def _handle_binary_data(self, data: bytes):
        """Handle dados binários que seguem mensagem 451-"""
        try:
            decoded = data.decode("utf-8")
            if not self._binary_event:
                return

            if decoded.startswith("["):
                parsed = json.loads(decoded)
                asyncio.create_task(self._emit_event(f"{self._binary_event}_data", parsed))
                self._binary_event = None
        except Exception as e:
            logger.debug(f"Erro ao processar dados binários: {e}")
            self._binary_event = None


    def _handle_socketio_message(self, message: str):
        """Handle mensagem Socket.IO com dados"""
        data = message[2:]
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list) and len(parsed) >= 1:
                event = parsed[0]
                event_data = parsed[1] if len(parsed) > 1 else {}
                asyncio.create_task(self._emit_event(event, event_data))
        except json.JSONDecodeError:
            pass


    def _handle_json_message(self, message: str):
        """Handle mensagem JSON separada"""
        try:
            parsed = json.loads(message)
            if isinstance(parsed, dict):
                asyncio.create_task(self._emit_event("json_data", parsed))
        except json.JSONDecodeError:
            pass


    async def _emit_event(self, event: str, data):
        """Emitir evento para handlers"""
        if event not in self._event_handlers:
            return

        for handler in self._event_handlers[event]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Erro no handler {event}: {e}")


    def add_event_handler(self, event: str, handler):
        """Adicionar handler de evento"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)


    def remove_event_handler(self, event: str, handler):
        """Remover handler de evento"""
        if event in self._event_handlers and handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)


    def has_event_handler(self, event: str) -> bool:
        """Verificar se existe handler para um evento"""
        return event in self._event_handlers and len(self._event_handlers[event]) > 0


    async def send_message(self, message: str):
        """Enviar mensagem"""
        if not self.websocket:
            raise OpenOBConnectionError("WebSocket não está conectado")
        await self.websocket.send(message)
        logger.debug(f"Mensagem enviada: {message[:100]}...")


    async def disconnect(self):
        """Desconectar"""
        self._should_reconnect = False
        self._running = False

        if self._reconnect_task:
            self._reconnect_task.cancel()

        if self._receive_task:
            self._receive_task.cancel()

        if self._ping_task:
            self._ping_task.cancel()

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        logger.info(f"Desconectado ({self.name})")


    async def reconnect(self, ssid: str = None) -> bool:
        """Reconectar ao servidor (única tentativa)"""
        await self.disconnect()
        await asyncio.sleep(CONNECTION_SETTINGS["reconnect_delay"])
        return await self.connect(ssid=ssid, auto_reconnect=False)
