# HYBRID-X1

One board (Arduino Uno + ESP32 + Raspberry Pi 4) running two smart products, each with a web dashboard and a mobile app:

- **Smart Irrigation**: 3 crop zones, forecast and evapotranspiration watering, flow meter, plant disease AI, fault detection
- **Smart Home**: scenes, voice commands, face recognition, Bluetooth presence, energy anomaly detection, safety sensors

Shared features: MQTT, SQLite history, Telegram alerts, token security, over-the-air updates, installable phone apps.

## Try it (no hardware needed)
Open `website/index.html` in a browser. Mobile app demo PIN: `1234`.

## Run it for real
See [`README.txt`](README.txt) for the full setup. Short version, on the Raspberry Pi:

```bash
sudo apt install mosquitto python3-pip python3-flask python3-serial caddy
pip3 install paho-mqtt requests --break-system-packages
export HUB_TOKEN=your-long-secret
python3 code/irrigation/pi_irrigation_mqtt.py   # or code/smarthome/pi_home_mqtt.py
```

## Layout
| Folder | What it holds |
|---|---|
| `website/` | Final page, web dashboards, mobile apps |
| `code/common/` | Shared MQTT, database, Telegram and security module |
| `code/irrigation/` | Pi hub, Arduino + ESP32 firmware, disease AI, phone app |
| `code/smarthome/` | Pi hub, Arduino + ESP32 firmware, face recognition, voice assistant, phone app |

## Status and safety
The code is written and syntax-checked but has not been tested on real hardware. Mains wiring must be done by a qualified electrician, and real gas and smoke alarms must use certified detectors. Never commit your WiFi password, `HUB_TOKEN` or Telegram token.
