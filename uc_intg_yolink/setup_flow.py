"""Setup flow: authenticate a YoLink account with UAID + Secret Key."""

import asyncio
import logging
import re
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow
from yolink.message_listener import MessageListener

from uc_intg_yolink.client import YoLinkClient, device_metadata
from uc_intg_yolink.config import YoLinkConfig

_LOG = logging.getLogger(__name__)


class _NoopListener(MessageListener):
    def on_message(self, device: Any, msg_data: dict[str, Any]) -> None:
        return None


def _has_entities(meta: dict) -> bool:
    return bool(
        meta.get("is_switch")
        or meta.get("has_temp")
        or meta.get("has_humidity")
        or meta.get("has_battery")
        or meta.get("state_kind")
    )


class YoLinkSetupFlow(BaseSetupFlow[YoLinkConfig]):
    """Collect YoLink User Access Credentials, validate, and store discovered devices."""

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "YoLink Account"},
            [
                {
                    "id": "info",
                    "label": {"en": "YoLink Account"},
                    "field": {"label": {"value": {"en": (
                        "In the YoLink app, open Account -> Advanced Settings -> User Access "
                        "Credentials and tap Generate. Enter the User Access Id (UAID) and Secret "
                        "Key below. All supported devices on the account will be added."
                    )}}},
                },
                {"id": "uaid", "label": {"en": "User Access Id (UAID)"}, "field": {"text": {"value": ""}}},
                {"id": "secret_key", "label": {"en": "Secret Key"}, "field": {"password": {"value": ""}}},
            ],
        )

    async def query_device(self, input_values: dict[str, Any]) -> YoLinkConfig:
        uaid = input_values.get("uaid", "").strip()
        secret_key = input_values.get("secret_key", "").strip()
        if not uaid:
            raise ValueError("User Access Id is required")
        if not secret_key:
            raise ValueError("Secret Key is required")

        client = YoLinkClient(uaid, secret_key)
        devices: list[dict] = []
        try:
            await asyncio.wait_for(client.connect(_NoopListener()), timeout=25)
            for node in client.get_nodes().values():
                try:
                    state = await client.fetch_state(node)
                except Exception:  # pylint: disable=broad-exception-caught
                    state = {}
                meta = device_metadata(node, state)
                if _has_entities(meta):
                    devices.append(meta)
        except Exception as err:  # pylint: disable=broad-exception-caught
            raise ValueError(
                f"Could not sign in to YoLink. Check the UAID and Secret Key. ({err})"
            ) from err
        finally:
            await client.close()

        if not devices:
            raise ValueError("No supported YoLink devices were found on this account.")

        identifier = f"yolink_{re.sub(r'[^A-Za-z0-9]', '_', uaid.lower())}"
        return YoLinkConfig(
            identifier=identifier,
            name="YoLink",
            uaid=uaid,
            secret_key=secret_key,
            devices=devices,
        )
