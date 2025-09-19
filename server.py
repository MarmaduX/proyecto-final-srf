from flask import Flask, Response, jsonify
import cv2
from ultralytics import YOLO
import threading
from services.detection_service import detection_service
from config.settings import settings
import time

app = Flask(__name__)
model = YOLO("../AI/weights/best.pt")

cap = cv2.VideoCapture("http://192.168.1.6:4747/video")

frame_output = None
running = True       

def detection_loop():
    global frame_output, running
    last_saved = []
    save_cooldown = 10 #Segundos para volver a guardar
    frame_count = 0

    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1
        if frame_count % 5 != 0: #Procesa cada 5 frames
            continue

        results = model.predict(frame, imgsz=640, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()
        frame_output = annotated_frame 

        detections = []
        altura_real = 10
        distancia_focal = 600

        now = time.time()

        for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    altura_px = y2 - y1
                    distancia_cm = (altura_real * distancia_focal) / altura_px if altura_px > 0 else None
                    
                    is_duplicate = False
                    for saved_cls, saved_bbox, saved_time in last_saved:
                        if cls == saved_cls and (now - saved_time) < save_cooldown:
                            sx1, sy1, sx2, sy2 = saved_bbox
                            overlap_x = min(x2, sx2) - max(x1, sx1)
                            overlap_y = min(y2, sy2) - max(y1, sy1)
                            if overlap_x > 0 and overlap_y > 0:
                                is_duplicate = True
                                break

                    if not is_duplicate:
                        detections.append({
                            "class": model.names[cls],
                            "confidence": conf,
                            "bbox": [x1, y1, x2, y2],
                            "distance_cm": distancia_cm,
                            "timestamp": now
                        })
                        last_saved.append((cls, (x1, y1, x2, y2), now))
                    
                    if distancia_cm:
                        cv2.putText(
                            annotated_frame,
                            f"{distancia_cm:.0f} cm",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2
                        )
                    
        if detections:
            print("Detecciones:", detections)
            detection_service.store_detections(detections)
        last_saved = [(c, b, t) for (c, b, t) in last_saved if now - t < save_cooldown]

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
            if cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()
    else:
        print("Failed to initialize MongoDB connection")
            cap.release()
            cv2.destroyAllWindows()
