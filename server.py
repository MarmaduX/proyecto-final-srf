import time
import threading
import json

import cv2
import numpy as np
from bson import ObjectId
from flask import Flask, Response, request, jsonify
from flask.json.provider import DefaultJSONProvider
from ultralytics import YOLO
from typing import Optional

from mqtt_client import setup_mqtt
from services.detection_loop import detection_loop
from services.detection_service import detection_service
from config.settings import settings
import time
from config.database import db_config


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

cap_container: dict[str, Optional[cv2.VideoCapture]] = {"cap": None}
cap = None
cap_lock = threading.Lock()
frame_output = [None]
frame_lock = threading.Lock()
running = True
control = {"running": True, "conf": 0.6, "snapshot": False}
mqtt_client = setup_mqtt(control)
camera_connected = False

# -------------------------------
# FUNCIÓN DE CONEXIÓN A LA CÁMARA
# -------------------------------
def connect_camera(rtsp_url, retry_interval=5):
    global camera_connected
    while running:
        if camera_connected:
            time.sleep(2)
            continue

        print(f"[INFO] Intentando conectar a la cámara RTSP: {rtsp_url}")
        new_cap = cv2.VideoCapture(rtsp_url)

        if new_cap.isOpened():
            with cap_lock:
                if cap_container["cap"] is not None:
                    cap_container["cap"].release()
                cap_container["cap"] = new_cap
                camera_connected = True
            print("[INFO] Cámara conectada exitosamente ✅")

            while running:
                time.sleep(2)
                with cap_lock:
                    if cap_container["cap"] is None or not cap_container["cap"].isOpened():
                        print("[WARN] Cámara desconectada, reintentando...")
                        camera_connected = False
                        break
        else:
            print(f"[WARN] No se pudo conectar a la cámara. Reintentando en {retry_interval:.1f}s...")
            new_cap.release()
            time.sleep(retry_interval)

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

@app.route("/locations")
def get_locations(): 
    if db_config.db is None:
        if not db_config.connect():
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
     
    collection = db_config.get_collection("locations")
    if collection is None:
        return jsonify({"error": "Colección no encontrada"}), 404
     
    docs = list(collection.find().sort("created_at", -1).limit(50))
     
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
    
    return jsonify(docs)


if __name__ == "__main__":
    if detection_service.initialize(): 
        # 🔹 Hilo para reconectar cámara continuamente  
        camera_thread = threading.Thread(
            target=connect_camera, args=(settings.VIDEO_URL, 3), daemon=True
        )
        camera_thread.start()
        
        # 🔹 Hilo de detección YOLO
        t = threading.Thread(
            target=detection_loop,
            args=(cap_container, model, control, mqtt_client, frame_output, frame_lock),
            daemon=True
        )
        t.start()

        try:
            app.run(host=settings.HOST, port=settings.PORT, debug=settings.FLASK_DEBUG, use_reloader=False)
        finally:
            running = False 
            with cap_lock:
                if cap:
                    cap.release()
            cv2.destroyAllWindows()
            control["running"] = False
            mqtt_client.loop_stop()
            mqtt_client.disconnect()  
    else:
        print("Failed to initialize MongoDB connection")
