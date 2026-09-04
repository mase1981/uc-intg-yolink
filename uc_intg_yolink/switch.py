"""YoLink switch entities - switches, outlets, and valve manipulators."""

import logging
from typing import Any

from ucapi import StatusCodes, switch
from ucapi_framework import SwitchEntity

from uc_intg_yolink.config import YoLinkConfig
from uc_intg_yolink.const import STATE_ON
from uc_intg_yolink.device import YoLinkAccount

_LOG = logging.getLogger(__name__)


def _is_on(state: dict) -> bool | None:
    value = state.get("state")
    if isinstance(value, list):
        return any(v == "open" for v in value)
    if isinstance(value, str):
        return value == "open"
    return None


class YoLinkSwitch(SwitchEntity):
    """A YoLink switch, outlet, or manipulator as an on/off switch."""

    def __init__(self, device_config: YoLinkConfig, device: YoLinkAccount, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"switch.{device_config.identifier}.{self._device_id}",
            meta.get("name", "Switch"),
            [switch.Features.ON_OFF, switch.Features.TOGGLE],
            {switch.Attributes.STATE: switch.States.UNKNOWN},
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state != STATE_ON:
            self.update({switch.Attributes.STATE: switch.States.UNAVAILABLE})
            return
        is_on = _is_on(self._device.get_state(self._device_id))
        if is_on is None:
            self.update({switch.Attributes.STATE: switch.States.UNKNOWN})
            return
        self.update({switch.Attributes.STATE: switch.States.ON if is_on else switch.States.OFF})

    async def _handle_command(self, entity: Any, cmd_id: str, params: dict | None = None, *_a: Any) -> StatusCodes:
        try:
            if cmd_id == switch.Commands.ON:
                ok = await self._device.set_switch(self._device_id, True)
            elif cmd_id == switch.Commands.OFF:
                ok = await self._device.set_switch(self._device_id, False)
            elif cmd_id == switch.Commands.TOGGLE:
                current = _is_on(self._device.get_state(self._device_id)) or False
                ok = await self._device.set_switch(self._device_id, not current)
            else:
                return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Switch command error (%s): %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR


def create_switches(device_config: YoLinkConfig, device: YoLinkAccount) -> list[SwitchEntity]:
    return [
        YoLinkSwitch(device_config, device, meta)
        for meta in device_config.devices
        if meta.get("is_switch")
    ]
