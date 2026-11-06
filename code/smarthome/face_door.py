"""Face recognition at the front door (Pi camera). Family photos go in family/<name>.jpg.
Setup: pip install face_recognition opencv-python paho-mqtt requests"""
import json, os, sys, time
import cv2, face_recognition
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from hubkit import mqtt_client

known, names = [], []
for f in os.listdir("family"):
    enc = face_recognition.face_encodings(face_recognition.load_image_file("family/" + f))
    if enc: known.append(enc[0]); names.append(os.path.splitext(f)[0])
client = mqtt_client([], lambda t, p: None)
cam = cv2.VideoCapture(0); last = 0
while True:
    ok, frame = cam.read()
    if not ok or time.time() - last < 5: time.sleep(0.2); continue
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    for enc in face_recognition.face_encodings(rgb):
        match = face_recognition.compare_faces(known, enc, tolerance=0.5)
        last = time.time()
        if True in match:
            client.publish("x1/home/door/unlock", json.dumps({"who": names[match.index(True)]}))
        else:
            cv2.imwrite("stranger.jpg", frame)
            client.publish("x1/home/door/stranger", json.dumps({"photo": "stranger.jpg"}))
