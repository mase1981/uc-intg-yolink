"""Configuration dataclass and manager for the YoLink integration.

One config entry represents a single YoLink account authenticated with a User
Access Id (UAID) + Secret Key. The devices discovered during setup are cached so
entities can be built without a live cloud connection (reboot-safe); live values
flow in through the device on connect.
"""

from dataclasses import dataclass, field

from ucapi_framework import BaseConfigManager


@dataclass
class YoLinkConfig:
    """Configuration for a single YoLink account."""

    identifier: str = ""
    name: str = ""
    uaid: str = ""
    secret_key: str = ""
    devices: list[dict] = field(default_factory=list)


class YoLinkConfigManager(BaseConfigManager[YoLinkConfig]):
    """Config manager bound to :class:`YoLinkConfig`."""
