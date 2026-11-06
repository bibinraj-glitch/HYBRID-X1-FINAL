"""HYBRID-X1 smart-home hub (Pi): Arduino serial bridge + MQTT + SQLite + Telegram + automation rules,
energy anomaly detection and learned routines, with a secure phone app.
Run: HUB_TOKEN=mysecret TG_TOKEN=... TG_CHAT=... python3 pi_home_mqtt.py     App: http://<pi-ip>:5000"""
import glob, json, os, statistics, sys, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
import serial
from hubkit import *

ROOMS = ["Living room", "Bedroom", "Kitchen"]
H = {"light": [0, 0, 0], "fan": [0, 0, 0], "locked": 1, "valve": 1, "mode": "Home", "alarm": "", "presence": 1,
     "outside": None, "watts": 0, "kwh": 0.0, "last_motion": [0, 0, 0], "temp": [26, 26, 26]}
store = Store("home.db"); ser = None; watt_hist = []; last_t = time.time(); manual_log = []; routines = []

def send(cmd):
    if ser: ser.write((cmd + "\n").encode())

def light(i, v, why="auto"):
    if H["light"][i] != v:
        H["light"][i] = v; send("L%d:%d" % (i, v))
        if why == "manual":                              # remember what the user does, to learn routines
            manual_log.append((time.localtime().tm_hour, time.localtime().tm_wday, i, v)); store.add("manual_light%d_h%d" % (i, time.localtime().tm_hour), 1)

def fan(i, v):
    if H["fan"][i] != v: H["fan"][i] = v; send("F%d:%d" % (i, v))

def dark(): h = time.localtime().tm_hour; return h >= 18 or h < 6

def alarm(kind, text):
    H["alarm"] = kind; telegram("HOME ALERT: " + text)
    if kind == "gas": send("G:0"); fan(2, 1)
    if kind == "smoke": H["locked"] = 0; send("D:0"); [light(i, 100) for i in range(3)]
    if kind == "water": H["valve"] = 0; send("V:0")

def energy():           # power = base 20 W + 12 W per light at 100% + 45 W per fan; anomaly = reading far above its own recent history
    global last_t
    w = 20 + sum(l * 0.12 for l in H["light"]) + sum(f * 45 for f in H["fan"]); H["watts"] = w
    now = time.time(); H["kwh"] += w * (now - last_t) / 3.6e6; last_t = now
    store.add("watts", w); watt_hist.append(w); del watt_hist[:-600]
    if len(watt_hist) > 60:
        mu, sd = statistics.mean(watt_hist[:-5]), statistics.pstdev(watt_hist[:-5]) or 1
        if (statistics.mean(watt_hist[-5:]) - mu) / sd > 3 and w > mu + 50: telegram("Unusual power use: %d W (normal about %d W)" % (w, mu))

def learn():            # suggest a routine when the same light action was done at the same hour on 5+ days
    seen = {}
    for h, d, i, v in manual_log: seen.setdefault((h, i, v), set()).add(d)
    return [{"hour": h, "room": ROOMS[i], "level": v, "days": len(ds)} for (h, i, v), ds in seen.items() if len(ds) >= 5 and v > 0]

def on_sensor(d):
    now = time.time()
    for i in range(3):
        if d["m"][i]:
            H["last_motion"][i] = now
            if H["mode"] == "Away": alarm("intruder", "Motion in %s while Away" % ROOMS[i])
            elif dark() and not H["light"][i]: light(i, 60)
        elif H["light"][i] and now - H["last_motion"][i] > 1200 and H["mode"] == "Home" and not H["presence"]: light(i, 0)   # nobody home: off
    if d["gas"] > 400 and not H["alarm"]: alarm("gas", "Gas leak in the kitchen, valve closed")
    if d["wet"] and not H["alarm"]: alarm("water", "Water leak, main valve closed")
    if d["door"] and H["mode"] == "Away": alarm("intruder", "Front door opened while Away")
    if d["bell"]: telegram("Visitor at the front door")
    energy(); client.publish("x1/home/state", json.dumps(H))

def on_msg(topic, payload):
    d = json.loads(payload) if payload.startswith("{") else payload
    if topic == "x1/home/esp32": H["presence"], H["outside"] = d["presence"], d["outside"]
    if topic == "x1/home/door/unlock" and d.get("who"): H["locked"] = 0; send("D:0"); telegram("Door unlocked for %s (face recognised)" % d["who"])
    if topic == "x1/home/door/stranger": telegram("Unknown person at the door", photo=d.get("photo"))
    if topic == "x1/home/voice": voice(d["text"])

def voice(t):
    t = t.lower()
    for i, r in enumerate(ROOMS):
        if r.split()[0].lower() in t and "light" in t:
            light(i, 0 if "off" in t else 80, "manual")
    if "unlock" in t: H["locked"] = 0; send("D:0")
    elif "lock" in t: H["locked"] = 1; send("D:1")

def reader():
    global ser
    while True:
        try:
            ser = serial.Serial((glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))[0], 9600, timeout=2)
            while True:
                line = ser.readline().decode(errors="ignore").strip()
                if line.startswith("{"): on_sensor(json.loads(line))
        except Exception:
            time.sleep(2)

client = mqtt_client(["x1/home/esp32", "x1/home/door/unlock", "x1/home/door/stranger", "x1/home/voice"], on_msg)
app = make_app(os.path.join(os.path.dirname(__file__), "app"))
@app.route("/api/state")
def state(): return jsonify({**H, "routines": learn()})
@app.route("/api/light/<int:i>/<int:v>")
def api_light(i, v): light(i, v, "manual"); return jsonify(H)
@app.route("/api/fan/<int:i>/<int:v>")
def api_fan(i, v): fan(i, v); return jsonify(H)
@app.route("/api/lock/<int:v>")
def api_lock(v): H["locked"] = v; send("D:%d" % v); return jsonify(H)
@app.route("/api/mode/<m>")
def api_mode(m): H["mode"] = m; H["alarm"] = "" if m != "Away" else H["alarm"]; return jsonify(H)
@app.route("/api/clear")
def clear(): H["alarm"] = ""; H["valve"] = 1; send("V:1"); send("G:1"); return jsonify(H)
@app.route("/api/history/<k>")
def hist(k): return jsonify(store.history(k, int(request.args.get("hours", 24))))

if __name__ == "__main__":
    threading.Thread(target=reader, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
