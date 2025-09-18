from flask import Flask, Response, jsonify
import cv2
from ultralytics import YOLO
import threading
from services.detection_service import detection_service
from config.settings import settings

app = Flask(__name__)
model = YOLO("../AI/weights/best.pt")

cap = cv2.VideoCapture("http://192.168.1.51:4747/video")
frame_output = None   
running = True       

def detection_loop():
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
            print("Detecciones:", detections)
            detection_service.store_detections(detections)

@app.route("/")
def index():
    return "Servidor Flask con YOLO funcionando 🚀"

@app.route("/video")
def video():
    def generate():
        global frame_output
        while True:
            if frame_output is not None:
                ret, buffer = cv2.imencode(".jpg", frame_output)
                frame = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/detections")
def get_detections():
    detections = detection_service.get_recent_detections(limit=50)
    return jsonify(detections)

if __name__ == "__main__":
    if detection_service.initialize():
        t = threading.Thread(target=detection_loop, daemon=True)
        t.start()

        try:
            app.run(host=settings.HOST, port=settings.PORT, debug=settings.FLASK_DEBUG)
        finally:
            running = False
            cap.release()
            cv2.destroyAllWindows()
    else:
        print("Failed to initialize MongoDB connection")