# YoLink Integration for Unfolded Circle Remote 2/3

Control your **YoLink smart-home devices** directly from your Unfolded Circle Remote 2 or Remote 3. Turn switches, outlets, and valve controllers on and off, and monitor temperature/humidity, door, motion, leak, and vibration sensors and battery levels - all from your YoLink account.

![YoLink](https://img.shields.io/badge/YoLink-Smart%20Home-00A6A6)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-yolink?style=flat-square)](https://github.com/mase1981/uc-intg-yolink/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-yolink?style=flat-square)](https://github.com/mase1981/uc-intg-yolink/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-yolink/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)

## Supported Devices

YoLink devices on your account, including **Switches**, **Outlets** and **Multi-Outlets**, **Valve Controllers (Manipulators)**, **Temperature/Humidity Sensors**, **Door/Contact Sensors**, **Motion Sensors**, **Leak Sensors**, and **Vibration Sensors**. Battery-powered devices also report their battery level.

## Features

- **🔌 Switch control** - turn switches, outlets, multi-outlets, and valve controllers on and off.
- **🌡️ Temperature & humidity sensors** - readings from YoLink THSensors.
- **🚪 Contact & alert sensors** - door (Open/Closed), motion (Motion/Clear), leak (Wet/Dry), and vibration status.
- **🔋 Battery sensors** - battery level for battery-powered devices.
- **☁️ Realtime updates** - state changes are pushed from the YoLink cloud, with polling as a fallback.
- **Multi-device** - every supported device on your account is added automatically.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

## How It Works

YoLink devices are cloud-connected through a YoLink hub. This integration signs in to your YoLink account using **User Access Credentials** and talks to the same cloud the YoLink app uses:

- **No OAuth redirect** - authentication uses a User Access Id (UAID) and Secret Key you generate in the YoLink app, entered as two text fields.
- **One account, all devices** - every supported device on the account is added.
- **Realtime push** - the integration subscribes to the YoLink cloud so changes appear promptly, and also polls periodically as a fallback.

> Because this is a cloud integration, your Remote must have internet access and the YoLink cloud must be reachable.

## Requirements

- A YoLink account with a hub and at least one supported device.
- **User Access Credentials** from the YoLink app: **Account → Advanced Settings → User Access Credentials → Generate** (gives a UAID and Secret Key).
- Unfolded Circle Remote 2 / 3 with firmware supporting custom integrations.

## Installation

### Option 1: Remote Web Interface (Recommended)

1. Download the latest `uc-intg-yolink-<version>.tar.gz` from the [**Releases**](https://github.com/mase1981/uc-intg-yolink/releases) page.
2. Open your Remote's web interface (`http://your-remote-ip`).
3. Go to **Settings → Integrations → Add Integration → Install Custom** and upload the `.tar.gz`.

### Option 2: Docker (Advanced Users)

**Image**: `ghcr.io/mase1981/uc-intg-yolink:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-yolink:
    image: ghcr.io/mase1981/uc-intg-yolink:latest
    container_name: uc-intg-yolink
    network_mode: host
    volumes:
      - ./config:/config
    environment:
      - UC_CONFIG_HOME=/config
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-intg-yolink --restart unless-stopped --network host -v $(pwd)/config:/config -e UC_CONFIG_HOME=/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-yolink:latest
```

## Configuration

1. In the **YoLink app**, open **Account → Advanced Settings → User Access Credentials** and tap **Generate**.
2. Start setup on the Remote and enter the **UAID** and **Secret Key**.
3. The integration signs in and adds every supported device on the account.

For each device the integration creates:

| Entity | Purpose |
|--------|---------|
| **Switch** (`<name>`) | On/off for switches, outlets, and valve controllers. |
| **Temperature / Humidity sensors** | Readings from THSensors. |
| **Status sensor** | Door (Open/Closed), motion, leak, or vibration state. |
| **Battery sensor** | Battery level for battery-powered devices. |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Could not sign in to YoLink" | Re-generate the UAID and Secret Key in the YoLink app and enter them exactly. |
| "No supported YoLink devices were found" | Make sure your devices are set up and online in the YoLink app first. |
| A device is missing | Only supported device types (switches/outlets and the listed sensors) are added; other device types are skipped. |
| Devices unavailable after a while | The Remote lost internet or the YoLink cloud was unreachable; it recovers automatically when connectivity returns. |

## Credits

- **Developer**: Meir Miyara
- **YoLink cloud API**: based on the [yolink-api](https://github.com/YoSmart-Inc/yolink-api) library and the Home Assistant YoLink integration.
- **Unfolded Circle**: Remote 2/3 integration framework ([ucapi](https://github.com/unfoldedcircle/integration-python-library) / [ucapi-framework](https://github.com/JackJPowell/ucapi-framework)).

## License

Mozilla Public License 2.0 (MPL-2.0) - see the LICENSE file.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-yolink/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

---

**Made with ❤️ for the Unfolded Circle Community**

**Thank You**: Meir Miyara
