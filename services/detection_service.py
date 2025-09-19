from config.database import db_config
from models.detection import Detection, DetectionBatch
from typing import List, Dict, Any
import json

class DetectionService:
    def __init__(self):
        self.collection_name = "detections"
        self.collection = None
    
    def initialize(self):
        if db_config.connect():
            self.collection = db_config.get_collection(self.collection_name)
            return True
        return False
    
    def store_detection_batch(self, detection_batch: DetectionBatch) -> bool:
        try:
            if self.collection is not None:
                result = self.collection.insert_one(detection_batch.to_dict())
                return result.inserted_id is not None
            return False
        except Exception as e:
            print(f"Error storing detection batch: {e}")
            return False
    
    def store_detections(self, detections: List[tuple]) -> bool:
        try:
            detection_objects = []
            for class_name, confidence in detections:
                detection = Detection(confidence)
                detection_objects.append(detection)
            
            if detection_objects:
                batch = DetectionBatch(detection_objects)
                return self.store_detection_batch(batch)
            return False
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
