HYBRID-X1 ADVANCED PACKAGE  (irrigation/ and smarthome/ are two separate projects; common/ is shared)

WHAT IS INSIDE
  common/hubkit.py                 MQTT, SQLite history, Telegram alerts, token security, serves the phone app
  irrigation/pi_irrigation_mqtt.py Pi hub: evapotranspiration watering, flow meter, fault detection, history, Telegram
  irrigation/disease_detect.py     AI plant disease detection (TensorFlow Lite + Pi camera)
  irrigation/esp32_irrigation_mqtt.ino  ESP32: rain, flow meter, humidity -> MQTT, OTA updates
  irrigation/app/                  Phone app (app.html + manifest.json + sw.js) = installable PWA
  smarthome/pi_home_mqtt.py        Pi hub: rules, energy anomaly detection, learned routines, Telegram
  smarthome/arduino_home.ino       Arduino: PIR, gas, water, door, doorbell in; lights, fans, lock, valves out
  smarthome/esp32_home_mqtt.ino    ESP32: Bluetooth phone presence, outside temperature, MQTT, OTA
  smarthome/face_door.py           Face recognition at the door
  smarthome/voice.py               Offline voice assistant (Vosk)
  smarthome/app/                   Phone app (installable PWA)
  (the Arduino sketch for irrigation is arduino_irrigation_v2.ino from the earlier irrigation package)

SETUP ON THE RASPBERRY PI  (run once)
  sudo apt install mosquitto mosquitto-clients python3-pip python3-flask python3-serial caddy
  pip3 install paho-mqtt requests --break-system-packages
  sudo mosquitto_passwd -c /etc/mosquitto/passwd x1        (choose a password; add  password_file /etc/mosquitto/passwd  and  allow_anonymous false  to the Mosquitto config)

RUN A PROJECT  (example: irrigation)
  export HUB_TOKEN=pick-a-long-secret   MQTT_USER=x1  MQTT_PASS=your-mqtt-password
  export TG_TOKEN=<bot token from @BotFather>   TG_CHAT=<your chat id>          (optional, for Telegram alerts)
  python3 irrigation/pi_irrigation_mqtt.py
  Open http://<pi-ip>:5000 on your phone, enter HUB_TOKEN, then browser menu > Add to Home Screen.
  Do not use 1234 as the token: that is the demo PIN and opens the built-in demo instead.

HTTPS (security)   Install Caddy and use a Caddyfile:   x1.local { reverse_proxy localhost:5000 }   (or use Tailscale for safe remote access)

ESP32 / ARDUINO
  Edit WiFi name, password, Pi IP, MQTT user and password in the .ino files. First upload by cable;
  after that the ESP32 can be updated over WiFi (Arduino IDE > Tools > Port > network port).

AI FEATURES
  Plant disease: put a PlantVillage plant_disease.tflite and labels.txt in irrigation/, then  python3 disease_detect.py 1
  Face recognition: put family photos in smarthome/family/ named dad.jpg, mom.jpg, then  python3 face_door.py
  Voice: unzip a small Vosk English model as smarthome/model, then  python3 voice.py

IMPORTANT
  These files were written and syntax-checked but not tested on real hardware. Test each part on its own first.
  Mains wiring for lights and fans must be done by a qualified electrician. Use certified gas and smoke detectors.

FINAL PACKAGE LAYOUT
  website/index.html   open this first: overview, both web dashboards, both mobile apps and the build guide in one page
  website/*.html       the same four pages as separate files
  code/                everything for the real hardware (see the lists above)
