"""Async client for the YoLink cloud.

Wraps :mod:`yolink` (yolink-api). Authenticates with a User Access Id + Secret
Key (client-credentials grant, no OAuth redirect), owns the aiohttp session with
a certifi CA bundle, and manages the YoLinkHome device manager and its MQTT push.
"""

import logging
import ssl
from typing import Any

import aiohttp
import certifi
from yolink.home_manager import YoLinkHome
from yolink.local_auth_mgr import YoLinkLocalAuthMgr
from yolink.message_listener import MessageListener

from uc_intg_yolink.const import (
    TOKEN_URL,
    TYPE_STATE_KIND,
    TYPE_TH_SENSOR,
    SWITCH_TYPES,
)

_LOG = logging.getLogger(__name__)


def extract_state(brdp: Any) -> dict:
    """Pull the device state dict out of a BRDP response."""
    data = getattr(brdp, "data", None) or {}
    state = data.get("state")
    if isinstance(state, dict):
        return state
    return data if isinstance(data, dict) else {}


def device_metadata(node: Any, state: dict) -> dict:
    """Build cacheable metadata describing which entities a device needs."""
    device_type = node.device_type
    return {
        "device_id": node.device_id,
        "name": node.device_name or node.device_id,
        "type": device_type,
        "model": getattr(node, "device_model_name", "") or "",
        "is_switch": device_type in SWITCH_TYPES,
        "has_battery": "battery" in state,
        "has_temp": "temperature" in state or device_type == TYPE_TH_SENSOR,
        "has_humidity": "humidity" in state or device_type == TYPE_TH_SENSOR,
        "state_kind": TYPE_STATE_KIND.get(device_type, ""),
    }


class YoLinkClient:
    """Cloud client for one YoLink account."""

    def __init__(self, uaid: str, secret_key: str) -> None:
        self._uaid = uaid
        self._secret_key = secret_key
        self._session: aiohttp.ClientSession | None = None
        self._home: YoLinkHome | None = None
        self._nodes: dict[str, Any] = {}

    @property
    def is_connected(self) -> bool:
        return self._home is not None

    async def connect(self, listener: MessageListener) -> None:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        self._session = aiohttp.ClientSession(connector=connector)
        auth_mgr = YoLinkLocalAuthMgr(self._session, TOKEN_URL, self._uaid, self._secret_key)
        self._home = YoLinkHome()
        await self._home.async_setup(auth_mgr, listener)
        self._nodes = {node.device_id: node for node in self._home.get_devices()}

    def get_nodes(self) -> dict[str, Any]:
        return self._nodes

    def get_node(self, device_id: str) -> Any:
        return self._nodes.get(device_id)

    async def fetch_state(self, node: Any) -> dict:
        brdp = await node.fetch_state()
        return extract_state(brdp)

    async def close(self) -> None:
        if self._home is not None:
            try:
                await self._home.async_unload()
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.debug("YoLinkHome unload failed: %s", err)
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._home = None
        self._session = None
        self._nodes = {}
