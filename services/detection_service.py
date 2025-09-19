from config.database import db_config
from models.detection import Detection, DetectionBatch
from typing import List, Dict, Any

class DetectionService:
    def __init__(self):
        self.collection_name = "detections"
        self.collection = None
    
    def initialize(self):
        if db_config.connect():
            self.collection = db_config.get_collection(self.collection_name)
            print(f"Conectado a la colección: {self.collection}")
            return True
        print("No se pudo conectar a MongoDB")
        return False
    
    def store_detection_batch(self, detection_batch: DetectionBatch) -> bool:
        try:
            if self.collection is not None:
                data = detection_batch.to_dict()
                print("Guardando en Mongo:", data)
                result = self.collection.insert_one(data)
                print("Insert result:", result.inserted_id)
                return result.inserted_id is not None
            else:
                print("self.collection es None")
                return False
        except Exception as e:
            print(f"Error storing detection batch: {e}")
            return False
    
    def store_detections(self, detections: List[Dict[str, Any]]) -> bool:
        try:
            if not detections:
                print("No hay detecciones para guardar")
                return False
            detection_objects = []

            for d in detections:
                class_name = d.get("class_name", "unknown")
                confidence = d.get("confidence", 0.5)
                distance_cm = d.get("distance_cm")
                bbox = d.get("bbox", [])

                detection = Detection(class_name=class_name, distance_cm=distance_cm, confidence=confidence, bbox=bbox, timestamp=det.get("timestamp"))
                detection_objects.append(detection)

            batch = DetectionBatch(detection_objects)
            return self.store_detection_batch(batch)
        except Exception as e:
            print(f"Error storing detections: {e}")
            return False
    
    def get_recent_detections(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            if self.collection is not None:
                cursor = self.collection.find().sort("timestamp", -1).limit(limit)
                return list(cursor)
            return []
        except Exception as e:
            print(f"Error retrieving detections: {e}")
            return []
detection_service = DetectionService()