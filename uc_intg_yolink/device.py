"""YoLink device - one cloud account driven by the yolink-api client + MQTT.

Uses ExternalClientDevice because yolink-api (YoLinkHome) manages its own cloud
connection and MQTT push internally. Authentication and the MQTT subscription
happen in the connect path, so the framework watchdog's reconnect re-authenticates
and re-subscribes automatically - recovery == reconnect. Concurrent connect()
calls are serialised (rule 9) so the framework's double-connect can never orphan
a second MQTT client.
"""

import asyncio
import logging
from typing import Any

from ucapi_framework import ExternalClientDevice
from yolink.client_request import ClientRequest
from yolink.message_listener import MessageListener
from yolink.outlet_request_builder import OutletRequestBuilder

from uc_intg_yolink.client import YoLinkClient
from uc_intg_yolink.config import YoLinkConfig
from uc_intg_yolink.const import OUTLET_TYPES, STATE_ON, STATE_UNAVAILABLE

_LOG = logging.getLogger(__name__)


class _Listener(MessageListener):
    """Routes YoLink MQTT pushes into the device state cache."""

    def __init__(self, device: "YoLinkAccount") -> None:
        self._device = device

    def on_message(self, device: Any, msg_data: dict[str, Any]) -> None:
        self._device.on_push(device.device_id, msg_data)


class YoLinkAccount(ExternalClientDevice):
    """One YoLink account."""

    def __init__(self, device_config: YoLinkConfig, **kwargs: Any) -> None:
        super().__init__(device_config, **kwargs)
        self._device_config = device_config
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._state: str = STATE_UNAVAILABLE
        self._states: dict[str, dict] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return "yolink-cloud"

    @property
    def log_id(self) -> str:
        return f"{self.name} (YoLink)"

    @property
    def state(self) -> str:
        return self._state

    def get_state(self, device_id: str) -> dict:
        return self._states.get(device_id, {})

    def device_type(self, device_id: str) -> str:
        node = self._client.get_node(device_id) if self._client else None
        return node.device_type if node else ""

    # -- ExternalClientDevice interface --------------------------------
    async def connect(self) -> bool:
        async with self._connect_lock:
            return await super().connect()

    async def disconnect(self) -> None:
        async with self._connect_lock:
            await super().disconnect()

    async def create_client(self) -> YoLinkClient:
        await self.disconnect_client()  # defensive - watchdog bypasses connect()
        return YoLinkClient(self._device_config.uaid, self._device_config.secret_key)

    async def connect_client(self) -> None:
        self._loop = asyncio.get_running_loop()
        await asyncio.wait_for(self._client.connect(_Listener(self)), timeout=20)
        await self._seed_states()
        self._state = STATE_ON

    async def disconnect_client(self) -> None:
        if self._client is not None:
            await self._client.close()
        self._state = STATE_UNAVAILABLE

    def check_client_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    async def _seed_states(self) -> None:
        for device_id, node in self._client.get_nodes().items():
            try:
                self._states[device_id] = await self._client.fetch_state(node)
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.debug("[%s] fetch_state failed for %s: %s", self.log_id, device_id, err)

    def on_push(self, device_id: str, data: dict) -> None:
        current = self._states.setdefault(device_id, {})
        if isinstance(data, dict):
            current.update(data)
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(self.push_update)

    async def set_switch(self, device_id: str, on: bool) -> bool:
        if self._client is None:
            return False
        node = self._client.get_node(device_id)
        if node is None:
            return False
        state = "open" if on else "close"
        if node.device_type in OUTLET_TYPES:
            request = OutletRequestBuilder.set_state_request(state, None)
        else:
            request = ClientRequest("setState", {"state": state})
        await node.call_device(request)
        try:
            self._states[device_id] = await self._client.fetch_state(node)
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Refresh after command failed: %s", self.log_id, err)
        self.push_update()
        return True
