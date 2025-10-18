import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'detection_system')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'false'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    MODEL_PATH = os.getenv('MODEL_PATH', "../AI/weights/best.pt")
    VIDEO_URL = os.getenv('VIDEO_URL', "http://0.0.0.0:4747/video")

    MQTT_BROKER = os.getenv('MQTT_BROKER', "localhost")
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))

    MQTT_TOPIC_DETECTIONS = os.getenv('MQTT_TOPIC_DETECTIONS', "detections")
    MQTT_TOPIC_COMMANDS   = os.getenv('MQTT_TOPIC_COMMANDS', "commands")
    MQTT_TOPIC_SNAPSHOTS  = os.getenv('MQTT_TOPIC_SNAPSHOTS', "snapshots")
    MQTT_TOPIC_ACK        = os.getenv('MQTT_TOPIC_ACK', "ack")
    MQTT_TOPIC_LOCATIONS   = os.getenv('MQTT_TOPIC_LOCATIONS', "locations")
    MQTT_TOPIC_REQUEST_UNFUMIGATED   = os.getenv('MQTT_TOPIC_REQUEST_UNFUMIGATED', "request/unfumigated")
    MQTT_TOPIC_RESPONSE_UNFUMIGATED   = os.getenv('MQTT_TOPIC_RESPONSE_UNFUMIGATED', "response/unfumigated")
    MQTT_TOPIC_FUMIGATE   = os.getenv('MQTT_TOPIC_FUMIGATE', "command/fumigate")
    MQTT_TOPIC_ACK_FUMIGATE   = os.getenv('MQTT_TOPIC_ACK_FUMIGATE', "ack/fumigate")


settings = Settings()
