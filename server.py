import time
from flask import Flask, Response
import cv2
import numpy as np
from ultralytics import YOLO
import threading
from config import *
from mqtt_client import setup_mqtt
from detection import detection_loop

app = Flask(__name__)
model = YOLO("../AI/weights/best.pt")

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(VIDEO_URL)
 
frame_output = [None]   
frame_lock = threading.Lock()
running = True       

control = {"running": True, "conf": 0.5, "snapshot": False}
mqtt_client = setup_mqtt(control)

@app.route("/")
def index():
    return "Servidor Flask con YOLO funcionando 🚀"

""" def detection_loop():
    global frame_output, running
    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        results = model.predict(frame, imgsz=640, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()
 
        frame_output = annotated_frame 
        detections = []
        for r in results:
            for box in r.boxes:
                cls_name = model.names[int(box.cls)]
                conf = float(box.conf)
                detections.append((cls_name, conf))

        if detections:
            print("Detecciones:", detections) """

@app.route("/video")
def video():
    def generate():
        global frame_output
        while True: 
            with frame_lock:
                frame = frame_output[0]
 
            if frame is None or not isinstance(frame, (np.ndarray,)):
                time.sleep(0.05)
                continue

            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    t = threading.Thread(target=detection_loop, args=(cap, model, control, mqtt_client, frame_output, frame_lock), daemon=True)
    t.start()

    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        control["running"] = False
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        cap.release()
        cv2.destroyAllWindows() 