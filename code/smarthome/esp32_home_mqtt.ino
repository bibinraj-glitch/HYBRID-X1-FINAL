// HYBRID-X1 ESP32 (smart home): phone presence by Bluetooth, outdoor temperature, MQTT, over-the-air updates.
// Libraries: PubSubClient, DHT sensor library, ESP32 BLE Arduino. DHT22 on GPIO4.
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoOTA.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <DHT.h>
const char* SSID = "YOUR_WIFI_NAME", *PASS = "YOUR_WIFI_PASSWORD";
const char* BROKER = "192.168.1.50", *MQTT_USER = "x1", *MQTT_PASS = "change-me", *OTA_PASS = "change-me-too";
const char* PHONE_NAME = "My Phone";             // the Bluetooth name your phone advertises (or use its MAC address)
DHT dht(4, DHT22);
WiFiClient net; PubSubClient mqtt(net);
BLEScan* scan;

void connectAll() {
  if (WiFi.status() != WL_CONNECTED) { WiFi.begin(SSID, PASS); while (WiFi.status() != WL_CONNECTED) delay(500); }
  while (!mqtt.connected()) { if (!mqtt.connect("x1-esp32-home", MQTT_USER, MQTT_PASS)) delay(2000); }
}
void setup() {
  dht.begin(); mqtt.setServer(BROKER, 1883);
  BLEDevice::init(""); scan = BLEDevice::getScan(); scan->setActiveScan(true);
  WiFi.begin(SSID, PASS); ArduinoOTA.setPassword(OTA_PASS); ArduinoOTA.begin();
}
void loop() {
  connectAll(); mqtt.loop(); ArduinoOTA.handle();
  static unsigned long t = 0;
  if (millis() - t >= 10000) {
    t = millis();
    BLEScanResults r = scan->start(3, false);               // 3 second scan
    bool here = false;
    for (int i = 0; i < r.getCount(); i++) if (String(r.getDevice(i).getName().c_str()) == PHONE_NAME) here = true;
    scan->clearResults();
    char buf[80]; snprintf(buf, sizeof(buf), "{\"presence\":%d,\"outside\":%.1f}", here, dht.readTemperature());
    mqtt.publish("x1/home/esp32", buf);
  }
}
