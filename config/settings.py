import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'detection_system')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    MODEL_PATH = "../AI/weights/best.pt"
    VIDEO_URL = "http://192.168.1.10:4747/video"

    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883

    MQTT_TOPIC_DETECTIONS = "yolo/detections"
    MQTT_TOPIC_COMMANDS   = "yolo/commands"
    MQTT_TOPIC_SNAPSHOTS  = "yolo/snapshots"
    MQTT_TOPIC_ACK        = "yolo/ack"


settings = Settings()
