"""Integration driver for YoLink accounts."""

from ucapi_framework import BaseIntegrationDriver

from uc_intg_yolink.config import YoLinkConfig
from uc_intg_yolink.device import YoLinkAccount
from uc_intg_yolink.sensor import create_sensors
from uc_intg_yolink.switch import create_switches


class YoLinkDriver(BaseIntegrationDriver[YoLinkAccount, YoLinkConfig]):
    """Builds the entity set for each YoLink account."""

    def __init__(self) -> None:
        super().__init__(
            device_class=YoLinkAccount,
            entity_classes=[
                create_switches,
                create_sensors,
            ],
            driver_id="uc_intg_yolink",
        )
