"""YoLink device - one cloud account exposing all its devices."""

import asyncio
import logging
from typing import Any

from ucapi_framework import DeviceEvents, PollingDevice
from yolink.client_request import ClientRequest
from yolink.message_listener import MessageListener
from yolink.outlet_request_builder import OutletRequestBuilder

from uc_intg_yolink.client import YoLinkClient
from uc_intg_yolink.config import YoLinkConfig
from uc_intg_yolink.const import (
    OUTLET_TYPES,
    POLL_INTERVAL,
    STATE_ON,
    STATE_UNAVAILABLE,
)

_LOG = logging.getLogger(__name__)


class _Listener(MessageListener):
    """Routes YoLink MQTT pushes into the device state cache."""

    def __init__(self, device: "YoLinkAccount") -> None:
        self._device = device

    def on_message(self, device: Any, msg_data: dict[str, Any]) -> None:
        self._device.on_push(device.device_id, msg_data)


class YoLinkAccount(PollingDevice):
    """One YoLink account."""

    def __init__(self, device_config: YoLinkConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: YoLinkClient | None = None
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

    async def establish_connection(self) -> YoLinkClient:
        async with self._connect_lock:
            self._loop = asyncio.get_running_loop()
            if self._client is None:
                client = YoLinkClient(self._device_config.uaid, self._device_config.secret_key)
                await asyncio.wait_for(client.connect(_Listener(self)), timeout=20)
                self._client = client
            await self._seed_states()
            self._state = STATE_ON
            return self._client

    async def _seed_states(self) -> None:
        assert self._client is not None
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

    async def poll_device(self) -> None:
        if self._client is None:
            return
        try:
            async with self._connect_lock:
                await self._seed_states()
            self.push_update()
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != STATE_UNAVAILABLE:
                self._state = STATE_UNAVAILABLE
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def disconnect(self) -> None:
        async with self._connect_lock:
            if self._client is not None:
                await self._client.close()
                self._client = None
        self._state = STATE_UNAVAILABLE
        await super().disconnect()

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
