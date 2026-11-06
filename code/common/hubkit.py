"""Shared toolkit for both HYBRID-X1 hubs: MQTT, SQLite history, Telegram alerts, token security, app hosting."""
import json, os, sqlite3, threading, time
import paho.mqtt.client as mqtt
import requests
from flask import Flask, jsonify, request, abort, send_from_directory

TOKEN = os.environ.get("HUB_TOKEN", "change-me")          # the app sends this as header X-Token
TG_TOKEN, TG_CHAT = os.environ.get("TG_TOKEN", ""), os.environ.get("TG_CHAT", "")
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_USER, MQTT_PASS = os.environ.get("MQTT_USER"), os.environ.get("MQTT_PASS")

def telegram(text, photo=None):
    """Send a Telegram message (create a bot with @BotFather, put its token in TG_TOKEN)."""
    if not (TG_TOKEN and TG_CHAT):
        return
    try:
        if photo:
            requests.post("https://api.telegram.org/bot%s/sendPhoto" % TG_TOKEN, data={"chat_id": TG_CHAT, "caption": text}, files={"photo": open(photo, "rb")}, timeout=10)
        else:
            requests.post("https://api.telegram.org/bot%s/sendMessage" % TG_TOKEN, data={"chat_id": TG_CHAT, "text": text}, timeout=10)
    except Exception:
        pass

class Store:
    """Every reading goes into SQLite so charts can show weeks of history."""
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS r(ts REAL, k TEXT, v REAL)")
        self.lock = threading.Lock()
    def add(self, k, v):
        with self.lock:
            self.db.execute("INSERT INTO r VALUES(?,?,?)", (time.time(), k, v)); self.db.commit()
    def history(self, k, hours=24):
        with self.lock:
            return self.db.execute("SELECT ts,v FROM r WHERE k=? AND ts>? ORDER BY ts", (k, time.time() - hours * 3600)).fetchall()

def mqtt_client(topics, on_message):
    c = mqtt.Client()
    if MQTT_USER:
        c.username_pw_set(MQTT_USER, MQTT_PASS)
    c.on_connect = lambda cl, u, f, rc: [cl.subscribe(t) for t in topics]
    c.on_message = lambda cl, u, m: on_message(m.topic, m.payload.decode(errors="ignore"))
    c.connect(MQTT_HOST, 1883, 60)
    c.loop_start()
    return c

def make_app(static_dir):
    """Flask app: /api/* needs the X-Token header; the phone app (app.html, manifest, service worker) is served at /."""
    app = Flask(__name__, static_folder=None)
    @app.before_request
    def guard():
        if request.path.startswith("/api/") and request.headers.get("X-Token") != TOKEN:
            abort(401)
    @app.route("/")
    def home(): return send_from_directory(static_dir, "app.html")
    @app.route("/<path:f>")
    def files(f): return send_from_directory(static_dir, f)
    return app
