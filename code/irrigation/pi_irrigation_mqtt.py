"""HYBRID-X1 irrigation hub (Pi): MQTT + SQLite + Telegram + evapotranspiration watering + secure phone app.
Run: HUB_TOKEN=mysecret TG_TOKEN=... TG_CHAT=... python3 pi_irrigation_mqtt.py     App: http://<pi-ip>:5000"""
import glob, json, math, os, sys, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
import serial
from hubkit import *

CROPS = {"tomato": (40, 65, 1.10), "rice": (60, 85, 1.20), "wheat": (25, 50, 1.00), "chilli": (35, 60, 0.90)}   # low%, high%, Kc
AREA_M2 = [20, 20, 20]
S = {"zones": [{"crop": "tomato", "soil": None, "fault": 0, "flat": 0} for _ in range(3)], "tank": None, "temp": None,
     "hum": None, "rain": 0, "flow_lpm": 0, "litres_today": 0.0, "active": 0, "auto": 1, "battery": None, "tmax": -99, "tmin": 99}
store = Store("irrigation.db"); ser = None; last_flow = time.time()

def et0():            # Hargreaves reference evapotranspiration, mm/day (Ra about 36 MJ/m2/day near latitude 13 N)
    if S["tmax"] < S["tmin"]:
        return 0
    tm = (S["tmax"] + S["tmin"]) / 2
    return max(0, 0.0023 * (tm + 17.8) * math.sqrt(max(S["tmax"] - S["tmin"], 1)) * 0.408 * 36)

def litres_needed(i):  # water the crop lost today = ETc x area (1 mm over 1 m2 = 1 litre)
    return et0() * CROPS[S["zones"][i]["crop"]][2] * AREA_M2[i]

def pump(z):
    S["active"] = z
    if ser: ser.write(("P%d" % z).encode())
    store.add("pump", z)

def decide():
    if not S["auto"]: return
    hour = time.localtime().tm_hour
    for i, z in enumerate(S["zones"]):
        z["flat"] = z["flat"] + 1 if z["soil"] == 0 else 0
        if z["flat"] == 10 and not z["fault"]:
            z["fault"] = 1; telegram("Zone %d soil sensor fault, zone disabled" % (i + 1))
    if S["active"]:
        z = S["zones"][S["active"] - 1]
        if z["soil"] >= CROPS[z["crop"]][1] or S["rain"] or S["tank"] < 10 or z["fault"]: pump(0)
        else: pump(S["active"])
        return
    if S["rain"]: return
    if S["tank"] < 10: telegram("Water tank is low"); return
    need = [(z["soil"] - CROPS[z["crop"]][0], i) for i, z in enumerate(S["zones"]) if not z["fault"] and z["soil"] is not None and z["soil"] < CROPS[z["crop"]][0]]
    if need:
        gap, i = min(need)
        if 11 <= hour < 16 and gap > -15: return
        pump(i + 1)

def on_msg(topic, payload):
    global last_flow
    d = json.loads(payload)
    if topic == "x1/irrigation/esp32":          # {"rain":0,"flow_lpm":1.2,"hum":60,"batt":87}
        S["rain"], S["hum"], S["battery"], S["flow_lpm"] = d["rain"], d["hum"], d.get("batt"), d["flow_lpm"]
        S["litres_today"] += d["flow_lpm"] * (time.time() - last_flow) / 60; last_flow = time.time()
        store.add("flow_lpm", d["flow_lpm"]); store.add("humidity", d["hum"])
    elif topic == "x1/irrigation/disease":      # published by disease_detect.py
        telegram("Plant health: %s (%d%% sure) in zone %s" % (d["label"], d["confidence"] * 100, d["zone"]))

def serial_reader():
    global ser
    while True:
        try:
            ser = serial.Serial((glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))[0], 9600, timeout=2)
            while True:
                line = ser.readline().decode(errors="ignore").strip()
                if line.startswith("S:"):
                    a = line[2:].split(",")
                    for i in range(3): S["zones"][i]["soil"] = int(a[i]); store.add("soil%d" % (i + 1), int(a[i]))
                    S["tank"], S["temp"] = int(a[3][2:]), int(a[4][2:])
                    S["tmax"], S["tmin"] = max(S["tmax"], S["temp"]), min(S["tmin"], S["temp"])
                    store.add("tank", S["tank"]); decide(); client.publish("x1/irrigation/state", json.dumps(S))
        except Exception:
            time.sleep(2)

client = mqtt_client(["x1/irrigation/esp32", "x1/irrigation/disease"], on_msg)
app = make_app(os.path.join(os.path.dirname(__file__), "app"))
@app.route("/api/state")
def state(): return jsonify({**S, "et0_mm": round(et0(), 2), "need_l": [round(litres_needed(i), 1) for i in range(3)]})
@app.route("/api/history/<k>")
def hist(k): return jsonify(store.history(k, int(request.args.get("hours", 24))))
@app.route("/api/pump/<int:z>")
def manual(z): S["auto"] = 0; pump(z); return jsonify(S)
@app.route("/api/auto/<int:v>")
def auto(v): S["auto"] = v; return jsonify(S)
@app.route("/api/crop/<int:z>/<name>")
def crop(z, name):
    if name in CROPS: S["zones"][z - 1]["crop"] = name
    return jsonify(S)

if __name__ == "__main__":
    threading.Thread(target=serial_reader, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)     # put Caddy or nginx in front for HTTPS (see README)
