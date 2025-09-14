from flask import Flask, Response
import cv2
from ultralytics import YOLO
import threading

app = Flask(__name__)
model = YOLO("../AI/weights/best.pt")

cap = cv2.VideoCapture("http://192.168.1.10:4747/video")
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

if __name__ == "__main__":
    t = threading.Thread(target=detection_loop, daemon=True)
    t.start()

    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        running = False
        cap.release()
        cv2.destroyAllWindows()