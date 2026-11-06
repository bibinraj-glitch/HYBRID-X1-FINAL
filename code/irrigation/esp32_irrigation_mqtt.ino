// HYBRID-X1 ESP32 (irrigation): rain sensor, flow meter, humidity -> MQTT, plus over-the-air updates.
// Libraries: PubSubClient, DHT sensor library. Flow meter YF-S201 on GPIO27, DHT22 on GPIO4, rain on GPIO34.
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoOTA.h>
#include <DHT.h>
const char* SSID = "YOUR_WIFI_NAME", *PASS = "YOUR_WIFI_PASSWORD";
const char* BROKER = "192.168.1.50";                   // Raspberry Pi running Mosquitto
const char* MQTT_USER = "x1", *MQTT_PASS = "change-me";
const char* OTA_PASS = "change-me-too";
DHT dht(4, DHT22);
WiFiClient net; PubSubClient mqtt(net);
volatile unsigned long pulses = 0;
void IRAM_ATTR onPulse() { pulses++; }

void connectAll() {
  if (WiFi.status() != WL_CONNECTED) { WiFi.begin(SSID, PASS); while (WiFi.status() != WL_CONNECTED) delay(500); }
  while (!mqtt.connected()) { if (!mqtt.connect("x1-esp32-irr", MQTT_USER, MQTT_PASS)) delay(2000); }
}
void setup() {
  dht.begin();
  pinMode(27, INPUT_PULLUP); attachInterrupt(27, onPulse, FALLING);
  WiFi.begin(SSID, PASS); mqtt.setServer(BROKER, 1883);
  ArduinoOTA.setPassword(OTA_PASS); ArduinoOTA.begin();   // update firmware over WiFi
}
void loop() {
  connectAll(); mqtt.loop(); ArduinoOTA.handle();
  static unsigned long t = 0;
  if (millis() - t >= 5000) {
    unsigned long p = pulses; pulses = 0; float secs = (millis() - t) / 1000.0; t = millis();
    float lpm = (p / secs) / 7.5;                          // YF-S201: 7.5 pulses per second = 1 litre/minute
    char buf[120];
    snprintf(buf, sizeof(buf), "{\"rain\":%d,\"flow_lpm\":%.2f,\"hum\":%.0f,\"batt\":%d}", analogRead(34) < 2000, lpm, dht.readHumidity(), 100);
    mqtt.publish("x1/irrigation/esp32", buf);
  }
}
