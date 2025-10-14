import json
import paho.mqtt.client as mqtt
from config.settings import settings 
from models.location import Location
from config.database import db_config 

def setup_mqtt(control):
    client = mqtt.Client()
    client.user_data_set(control)

    def on_connect(c, userdata, flags, rc):
        print("MQTT conectado, rc =", rc)
        c.subscribe(settings.MQTT_TOPIC_COMMANDS)
        c.subscribe(settings.MQTT_TOPIC_LOCATIONS)
        
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
                
        elif topic == "robot/location":
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

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
    client.loop_start()
    return client
