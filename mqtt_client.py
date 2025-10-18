import json
import paho.mqtt.client as mqtt
from config.settings import settings 
from models.location import Location
from config.database import db_config 
from bson import json_util

def setup_mqtt(control):
    client = mqtt.Client()
    client.user_data_set(control)

    def on_connect(c, userdata, flags, rc):
        print("MQTT conectado, rc =", rc)
        c.subscribe(settings.MQTT_TOPIC_COMMANDS)
        c.subscribe(settings.MQTT_TOPIC_LOCATIONS)
        c.subscribe(settings.MQTT_TOPIC_FUMIGATE)
        c.subscribe(settings.MQTT_TOPIC_REQUEST_UNFUMIGATED)
        
    def on_message(c, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode(errors="ignore")
        try:
            data = json.loads(payload)
        except:
            data = payload.strip()
        print(f"[MQTT] Mensaje recibido en {topic}: {data}")

        if topic == settings.MQTT_TOPIC_COMMANDS:
            if isinstance(data, str) and data == "stop":
                userdata["running"] = False
                c.publish(settings.MQTT_TOPIC_ACK, json.dumps({"status": "stopped"}))
                
        elif topic == settings.MQTT_TOPIC_LOCATIONS:
            # Esperamos un formato tipo: {"mesa": 1, "pata": 3}
            if isinstance(data, dict) and "mesa" in data and "pata" in data:
                loc = Location(
                    mesa=float(data["mesa"]),
                    pata=float(data["pata"]),
                    source="robot",
                    extra={"raw": data}
                )
                try:
                    if db_config.db is None:
                        if not db_config.connect():
                            print("[ERROR] No se pudo conectar a la DB")
                            return

                    # Obtenemos la colección
                    collection = db_config.get_collection("locations")
                    if collection is None:
                        print("[ERROR] Colección 'locations' no encontrada")
                        return

                    # Guardamos en la colección
                    result = collection.insert_one(loc.to_dict())
                    print(f"[DB] Ubicación guardada con _id: {result.inserted_id}")
                except Exception as e:
                    print(f"[ERROR] No se pudo guardar ubicación: {e}")
            else:
                print("[WARN] Formato de ubicación inválido")

        elif topic == settings.MQTT_TOPIC_REQUEST_UNFUMIGATED:
            if db_config.db is None:
                if not db_config.connect():
                    print("[ERROR] No se pudo conectar a la DB")
                    return

            collection_locations = db_config.get_collection("locations")
            collection_detections = db_config.get_collection("detections")

            if collection_locations is None:
                print("[ERROR] Colección 'locations' no encontrada")
                return

            if collection_detections is None:
                print("[ERROR] Colección 'detections' no encontrado")
                return

            try:
                detections = list(collection_detections.find({
                    "$or": [
                        {"fumigado": False},
                        {"fumigado": {"$exists": False}}
                    ]
                }))
                locations = list(collection_locations.find())

                payload = {
                    "locations": locations,
                    "detections": detections
                }
                json_data = json_util.dumps(payload)
                c.publish(settings.MQTT_TOPIC_RESPONSE_UNFUMIGATED, json_data)
                print(f"[MQTT] Enviados {len(locations)} locations y {len(detections)} detections")

            except Exception as e:
                print(f"[ERROR] Al enviar datos no fumigados: {e}")

        elif topic == settings.MQTT_TOPIC_FUMIGATE:
            try:
                # Parsear el payload
                data = json.loads(msg.payload.decode(errors="ignore"))
                detection_id = data.get("detection_id")

                if not detection_id:
                    print("[WARN] No se envió detection_id")
                    return

                collection = db_config.get_collection("detections")
                if collection is None:
                    print("[ERROR] Colección 'detections' no encontrada")
                    return

                from bson import ObjectId
                result = collection.update_one(
                    {"_id": ObjectId(detection_id)},
                    {"$set": {"fumigado": True}}
                )

                if result.modified_count == 1:
                    print(f"[MQTT] Detección {detection_id} marcada como fumigada ✅")
                    client.publish("ack/fumigate", json.dumps({
                        "status": "ok",
                        "detection_id": detection_id
                    }))
                else:
                    print(f"[WARN] No se encontró la detección {detection_id}")
                    client.publish("ack/fumigate", json.dumps({
                        "status": "not_found",
                        "detection_id": detection_id
                    }))

            except Exception as e:
                print(f"[ERROR] Al actualizar detección: {e}")
                client.publish("ack/fumigate", json.dumps({
                    "status": "error",
                    "error": str(e)
                }))


    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
    client.loop_start()
    return client
