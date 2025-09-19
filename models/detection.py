from datetime import datetime
from typing import List, Dict, Any, Optional

class Detection:
    def __init__(self, 
                 class_name: str, 
                 confidence: float, 
                 bbox: Optional[List[int]] = None, 
                 distance_cm: Optional[float] = None, 
                 timestamp: Optional[float] = None):
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox or []
        self.distance_cm = distance_cm
        self.timestamp = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "class": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox,
            "distance_cm": self.distance_cm,
            "timestamp": self.timestamp,
            "created_at": datetime.now()
        }

class DetectionBatch:
    def __init__(self, detections: List[Detection], frame_info: Dict[str, Any] = None):
        self.detections = detections
        self.frame_info = frame_info or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detections": [det.to_dict() for det in self.detections],
            "frame_info": self.frame_info,
            "timestamp": self.timestamp,
            "created_at": datetime.now()
        }