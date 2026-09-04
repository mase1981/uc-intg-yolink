"""YoLink sensor entities - temperature, humidity, battery, and contact/alert state."""

import logging

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_yolink.config import YoLinkConfig
from uc_intg_yolink.const import (
    BATTERY_LEVEL_PERCENT,
    STATE_KIND_LABELS,
    STATE_ON,
)
from uc_intg_yolink.device import YoLinkAccount

_LOG = logging.getLogger(__name__)


class TemperatureSensor(SensorEntity):
    def __init__(self, device_config: YoLinkConfig, device: YoLinkAccount, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"sensor.{device_config.identifier}.{self._device_id}.temperature",
            f"{meta.get('name', 'Sensor')} Temperature",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: 0},
            device_class=sensor.DeviceClasses.TEMPERATURE,
            options={sensor.Options.NATIVE_UNIT: "°C", sensor.Options.DECIMALS: 1},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = self._device.get_state(self._device_id)
        value = state.get("temperature")
        if self._device.state != STATE_ON or value is None:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({sensor.Attributes.STATE: sensor.States.ON, sensor.Attributes.VALUE: round(float(value), 1)})


class HumiditySensor(SensorEntity):
    def __init__(self, device_config: YoLinkConfig, device: YoLinkAccount, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"sensor.{device_config.identifier}.{self._device_id}.humidity",
            f"{meta.get('name', 'Sensor')} Humidity",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: 0},
            device_class=sensor.DeviceClasses.HUMIDITY,
            options={sensor.Options.NATIVE_UNIT: "%"},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = self._device.get_state(self._device_id)
        value = state.get("humidity")
        if self._device.state != STATE_ON or value is None:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({sensor.Attributes.STATE: sensor.States.ON, sensor.Attributes.VALUE: round(float(value), 1)})


class BatterySensor(SensorEntity):
    def __init__(self, device_config: YoLinkConfig, device: YoLinkAccount, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"sensor.{device_config.identifier}.{self._device_id}.battery",
            f"{meta.get('name', 'Sensor')} Battery",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: -1},
            device_class=sensor.DeviceClasses.BATTERY,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = self._device.get_state(self._device_id)
        level = state.get("battery")
        if self._device.state != STATE_ON or level is None:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        percent = BATTERY_LEVEL_PERCENT.get(int(level), 0)
        self.update({sensor.Attributes.STATE: sensor.States.ON, sensor.Attributes.VALUE: percent})


class StateSensor(SensorEntity):
    """Contact/alert state for door, motion, leak, and vibration sensors."""

    def __init__(self, device_config: YoLinkConfig, device: YoLinkAccount, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        self._kind = meta["state_kind"]
        super().__init__(
            f"sensor.{device_config.identifier}.{self._device_id}.state",
            f"{meta.get('name', 'Sensor')} Status",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = self._device.get_state(self._device_id)
        value = state.get("state")
        if self._device.state != STATE_ON or value is None:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        alert_label, clear_label = STATE_KIND_LABELS.get(self._kind, ("Alert", "Clear"))
        alerted = value in ("open", "alert", "full")
        self.update(
            {
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: alert_label if alerted else clear_label,
            }
        )


def create_sensors(device_config: YoLinkConfig, device: YoLinkAccount) -> list[SensorEntity]:
    entities: list[SensorEntity] = []
    for meta in device_config.devices:
        if meta.get("has_temp"):
            entities.append(TemperatureSensor(device_config, device, meta))
        if meta.get("has_humidity"):
            entities.append(HumiditySensor(device_config, device, meta))
        if meta.get("has_battery"):
            entities.append(BatterySensor(device_config, device, meta))
        if meta.get("state_kind"):
            entities.append(StateSensor(device_config, device, meta))
    return entities
