import cv2, json, time, datetime, base64
from config import *

def detection_loop(cap, model, control, mqtt_client, frame_output, frame_lock):
    while True:
        if not control["running"]:
            time.sleep(0.1)
            continue

        ret, frame = cap.read()
        if not ret:
            continue

        results = model.predict(frame, imgsz=640, conf=control["conf"], verbose=False)
        annotated = results[0].plot()

        with frame_lock:
            frame_output[0] = annotated

        detections = []
        for r in results:
            for box in r.boxes:
                cls_name = model.names[int(box.cls)]
                conf = float(box.conf)
                detections.append({"Class": cls_name, "Conf": conf})

        # Se mandan todas las detecciones a ese topic
        if detections:
            payload = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "detections": detections}
            mqtt_client.publish(MQTT_TOPIC_DETECTIONS, json.dumps(payload))

        # Si el snapshot es true captura fotos de la deteccion
        if control.get("snapshot"):
            ok, buf = cv2.imencode(".jpg", annotated)
            if ok:
                img_b64 = base64.b64encode(buf.tobytes()).decode()
                snap_payload = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "img": img_b64}
                mqtt_client.publish(MQTT_TOPIC_SNAPSHOTS, json.dumps(snap_payload))
            control["snapshot"] = False
