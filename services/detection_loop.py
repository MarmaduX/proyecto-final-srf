import cv2, json, time, datetime, base64 
from config.settings import settings
from services.detection_service import detection_service
import time

def detection_loop(cap, model, control, mqtt_client, frame_output, frame_lock):    
    last_saved = []
    save_cooldown = 10 
    frame_count = 0
    while True:
        if not control["running"]:
            time.sleep(0.1)
            continue

        ret, frame = cap.read()
        if not ret:
            continue
        
        altura_real = 10
        distancia_focal = 600
        now = time.time()
        
        results = model.predict(frame, imgsz=640, conf=control["conf"], verbose=False)
        annotated = results[0].plot()

        with frame_lock:
            frame_output[0] = annotated

        detections = []
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
                        annotated,
                        f"{distancia_cm:.0f} cm",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    ) 

        frame_count += 1 
        if detections:
            payload = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "detections": detections}
            mqtt_client.publish(settings.MQTT_TOPIC_DETECTIONS, json.dumps(payload))  # Se mandan todas las detecciones a ese topic
            if frame_count % 5 == 0:
                detection_service.store_detections(detections)

        # Si el snapshot es true captura fotos de la deteccion
        if control.get("snapshot"):
            ok, buf = cv2.imencode(".jpg", annotated)
            if ok:
                img_b64 = base64.b64encode(buf.tobytes()).decode()
                snap_payload = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "img": img_b64}
                mqtt_client.publish(settings.MQTT_TOPIC_SNAPSHOTS, json.dumps(snap_payload))
            control["snapshot"] = False
            
        last_saved = [(c, b, t) for (c, b, t) in last_saved if now - t < save_cooldown]
