import time
import threading
import json

import cv2
import numpy as np
from bson import ObjectId
from flask import Flask, Response, request, jsonify
from flask.json.provider import DefaultJSONProvider
from ultralytics import YOLO

from mqtt_client import setup_mqtt
from services.detection_loop import detection_loop
from services.detection_service import detection_service
from config.settings import settings
import time


app = Flask(__name__)

class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, default=self.default, **kwargs)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

    def default(self, obj):  # type: ignore
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

app.json_provider_class = CustomJSONProvider
app.json = app.json_provider_class(app)

model = YOLO(settings.MODEL_PATH)
    
cap = cv2.VideoCapture(settings.VIDEO_URL)
if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la cámara")
 
frame_output = [None]   
frame_lock = threading.Lock()
running = True       

control = {"running": True, "conf": 0.6, "snapshot": False}
mqtt_client = setup_mqtt(control)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return jsonify({"status": "ok"})
    return "Servidor Flask con YOLO funcionando 🚀"

@app.route("/video")
def video():
    def generate():
        global frame_output
        try:
            while True:
                with frame_lock:
                    frame = frame_output[0]

                if frame is None or not isinstance(frame, np.ndarray):
                    time.sleep(0.05)
                    continue

                ok, buffer = cv2.imencode(".jpg", frame)
                if not ok:
                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
                )
        except GeneratorExit:
            print("Cliente desconectado del stream")


    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/detections")
def get_detections():
    detections = detection_service.get_recent_detections(limit=50)
    return jsonify(detections)

if __name__ == "__main__":
    if detection_service.initialize():
        t = threading.Thread(target=detection_loop, args=(cap, model, control, mqtt_client, frame_output, frame_lock), daemon=True)
        t.start()
        try:
            app.run(host=settings.HOST, port=settings.PORT, debug=settings.FLASK_DEBUG, use_reloader=False)
        finally:
            running = False 
            cap.release()
            cv2.destroyAllWindows()
            control["running"] = False
            mqtt_client.loop_stop()
            mqtt_client.disconnect()  
    else:
        print("Failed to initialize MongoDB connection")
        cap.release()
        cv2.destroyAllWindows()
