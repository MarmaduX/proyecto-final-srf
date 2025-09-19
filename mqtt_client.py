import json
import paho.mqtt.client as mqtt
from config.settings import settings

def setup_mqtt(control):
    client = mqtt.Client()
    client.user_data_set(control)

    def on_connect(c, userdata, flags, rc):
        print("MQTT conectado, rc =", rc)
        c.subscribe(settings.MQTT_TOPIC_COMMANDS)

    def on_message(c, userdata, msg):
        payload = msg.payload.decode(errors="ignore")
        try:
            data = json.loads(payload)
        except:
            data = payload.strip()
        print("MQTT comando:", data)

        if isinstance(data, str) and data == "stop":
            userdata["running"] = False
            c.publish(settings.MQTT_TOPIC_ACK, json.dumps({"status": "stopped"}))

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
    client.loop_start()
    return client
