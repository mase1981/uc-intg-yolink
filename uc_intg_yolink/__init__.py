"""YoLink smart-home integration for Unfolded Circle Remote Two/3."""

import asyncio
import json
import logging
import os
from pathlib import Path

try:
    _driver_path = Path(__file__).parent.parent / "driver.json"
    with open(_driver_path, "r", encoding="utf-8") as f:
        __version__ = json.load(f).get("version", "0.0.0")
except (FileNotFoundError, json.JSONDecodeError):
    __version__ = "0.0.0"


async def main() -> None:
    """Integration entry point."""
    # Point the system TLS trust store at certifi so aiohttp AND the MQTT client
    # (paho/aiomqtt) can verify the YoLink cloud on the Remote's CA-less image.
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("SSL_CERT_DIR", os.path.dirname(certifi.where()))

    from ucapi import DeviceStates
    from ucapi_framework import BaseConfigManager, get_config_path

    from uc_intg_yolink.config import YoLinkConfig
    from uc_intg_yolink.driver import YoLinkDriver
    from uc_intg_yolink.setup_flow import YoLinkSetupFlow

    level = os.getenv("UC_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s",
    )
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiomqtt").setLevel(logging.WARNING)
    logging.getLogger("paho").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.CRITICAL)

    _LOG = logging.getLogger(__name__)
    _LOG.info("Starting YoLink integration v%s", __version__)

    driver = YoLinkDriver()
    config_path = get_config_path(driver.api.config_dir_path or "")
    config_manager = BaseConfigManager(
        config_path,
        add_handler=driver.on_device_added,
        remove_handler=driver.on_device_removed,
        config_class=YoLinkConfig,
    )
    driver.config_manager = config_manager

    setup_handler = YoLinkSetupFlow.create_handler(driver)
    driver_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
    await driver.api.init(os.path.abspath(driver_path), setup_handler)
    await driver.register_all_device_instances(connect=False)

    device_count = len(list(config_manager.all()))
    await driver.api.set_device_state(
        DeviceStates.CONNECTED if device_count > 0 else DeviceStates.DISCONNECTED
    )
    _LOG.info("YoLink integration started - %d account(s) configured", device_count)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
