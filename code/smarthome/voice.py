"""Offline voice assistant (Vosk speech recognition, no internet needed). Say: "turn on kitchen light", "lock the door".
Setup: pip install vosk sounddevice paho-mqtt requests ; download a small English model from alphacephei.com/vosk/models and unzip as ./model"""
import json, os, queue, sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from hubkit import mqtt_client

q = queue.Queue(); rec = KaldiRecognizer(Model("model"), 16000); client = mqtt_client([], lambda t, p: None)
with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=lambda d, f, t, s: q.put(bytes(d))):
    while True:
        if rec.AcceptWaveform(q.get()):
            text = json.loads(rec.Result())["text"]
            if text: client.publish("x1/home/voice", json.dumps({"text": text}))
