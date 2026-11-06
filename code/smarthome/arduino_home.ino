// HYBRID-X1 Arduino (smart home): sensors in, switches out. Talks to the Pi over USB serial (9600).
// Out (every 500 ms):  {"m":[0,1,0],"gas":120,"wet":0,"door":0,"bell":0}
// In:  L<room>:<0-100> light dimmer   F<room>:<0/1> fan   D:<0/1> door lock   V:<0/1> water valve   G:<0/1> gas valve
const int PIR[3] = {2, 4, A2}, LIGHT[3] = {3, 5, 6}, FAN[3] = {7, 8, 9};
const int GAS = A0, WET = A1, REED = A3, BELL = A4, LOCK = 13, WATER_V = 11, GAS_V = 12;
String line;

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 3; i++) { pinMode(PIR[i], INPUT); pinMode(LIGHT[i], OUTPUT); pinMode(FAN[i], OUTPUT); }
  pinMode(REED, INPUT_PULLUP); pinMode(BELL, INPUT_PULLUP);
  pinMode(LOCK, OUTPUT); pinMode(WATER_V, OUTPUT); pinMode(GAS_V, OUTPUT);
  digitalWrite(LOCK, HIGH); digitalWrite(WATER_V, HIGH); digitalWrite(GAS_V, HIGH);   // locked, valves open
}

void handle(String s) {
  int c = s.indexOf(':'); if (c < 0) return;
  int v = s.substring(c + 1).toInt(), r = s.charAt(1) - '0';
  switch (s.charAt(0)) {
    case 'L': if (r >= 0 && r < 3) analogWrite(LIGHT[r], map(v, 0, 100, 0, 255)); break;
    case 'F': if (r >= 0 && r < 3) digitalWrite(FAN[r], v); break;
    case 'D': digitalWrite(LOCK, v); break;
    case 'V': digitalWrite(WATER_V, v); break;
    case 'G': digitalWrite(GAS_V, v); break;
  }
}

void loop() {
  while (Serial.available()) { char ch = Serial.read(); if (ch == '\n') { handle(line); line = ""; } else line += ch; }
  static unsigned long t = 0;
  if (millis() - t > 500) {
    t = millis();
    Serial.print("{\"m\":["); for (int i = 0; i < 3; i++) { Serial.print(digitalRead(PIR[i])); if (i < 2) Serial.print(","); }
    Serial.print("],\"gas\":"); Serial.print(analogRead(GAS));
    Serial.print(",\"wet\":"); Serial.print(analogRead(WET) > 500);
    Serial.print(",\"door\":"); Serial.print(digitalRead(REED));
    Serial.print(",\"bell\":"); Serial.print(!digitalRead(BELL)); Serial.println("}");
  }
}
