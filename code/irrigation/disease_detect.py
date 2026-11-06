"""AI plant-disease detection on the Pi (TensorFlow Lite). Photographs a leaf, classifies it, reports over MQTT + Telegram.
Setup: pip install tflite-runtime pillow picamera2 paho-mqtt requests
Get a PlantVillage model: put plant_disease.tflite and labels.txt (one class per line) next to this file."""
import json, os, sys, time
import numpy as np
from PIL import Image
from tflite_runtime.interpreter import Interpreter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from hubkit import mqtt_client, telegram

ZONE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LABELS = [l.strip() for l in open("labels.txt")]
it = Interpreter(model_path="plant_disease.tflite"); it.allocate_tensors()
inp, out = it.get_input_details()[0], it.get_output_details()[0]
size = inp["shape"][1]
client = mqtt_client([], lambda t, p: None)

def snap():
    from picamera2 import Picamera2
    cam = Picamera2(); cam.start(); time.sleep(2); cam.capture_file("leaf.jpg"); cam.close()
    return "leaf.jpg"

while True:
    img = Image.open(snap()).convert("RGB").resize((size, size))
    x = np.expand_dims(np.array(img, dtype=np.float32) / 255.0, 0)
    it.set_tensor(inp["index"], x); it.invoke()
    p = it.get_tensor(out["index"])[0]; k = int(p.argmax())
    res = {"zone": ZONE, "label": LABELS[k], "confidence": float(p[k])}
    client.publish("x1/irrigation/disease", json.dumps(res))
    if "healthy" not in LABELS[k].lower() and p[k] > 0.7:
        telegram("Possible disease in zone %d: %s" % (ZONE, LABELS[k]), photo="leaf.jpg")
    time.sleep(6 * 3600)           # check every 6 hours
