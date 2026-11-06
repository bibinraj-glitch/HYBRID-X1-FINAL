// HYBRID-X1 Arduino part (v2): 3 irrigation zones + tank + temperature.
// Sends:  S:45,46,50,W:80,T:31   Receives:  "P1" = zone 1 pump on, "P0" = all off, "P2", "P3"
const int SOIL[3]  = {A0, A1, A2};   // capacitive soil sensors, one per zone
const int TANK = A3, TEMP = A4;
const int RELAY[3] = {7, 8, 9};      // 3-channel relay module (one valve/pump per zone)
const int DRY = 800, WET = 300;      // calibrate with your own sensors
unsigned long lastCmd = 0, lastSend = 0;

int pct(int raw, int dry, int wet) { return constrain(map(raw, dry, wet, 0, 100), 0, 100); }
void allOff() { for (int i = 0; i < 3; i++) digitalWrite(RELAY[i], LOW); }

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 3; i++) pinMode(RELAY[i], OUTPUT);
  allOff();
}

void loop() {
  if (Serial.available() >= 2) {
    char c = Serial.read(), z = Serial.read();          // e.g. 'P','2'
    if (c == 'P' && z == '0') allOff();
    if (c == 'P' && z >= '1' && z <= '3') { allOff(); digitalWrite(RELAY[z - '1'], HIGH); lastCmd = millis(); }
  }
  // safety: never run a pump for more than 2 minutes without a new command from the Pi
  if (millis() - lastCmd > 120000UL) allOff();

  if (millis() - lastSend > 1000) {
    lastSend = millis();
    Serial.print("S:");
    for (int i = 0; i < 3; i++) { Serial.print(pct(analogRead(SOIL[i]), DRY, WET)); Serial.print(","); }
    Serial.print("W:"); Serial.print(pct(analogRead(TANK), 0, 700));
    Serial.print(",T:"); Serial.println((int)(analogRead(TEMP) * 500.0 / 1023.0));
  }
}
