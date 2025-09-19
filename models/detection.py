from datetime import datetime
from typing import List, Dict, Any, Optional

class Detection:
    def __init__(self,
                class_name: str, 
                confidence: float, 
                distance_cm: Optional[float] = None, 
                bbox: Optional[List[int]] = None, 
                timestamp: Optional[float] = None):
        self.class_name = class_name
        self.confidence = confidence
        self.distance_cm = distance_cm
        self.bbox = bbox or []
        self.timestamp = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'class_name': self.class_name,
            'confidence': self.confidence,
            "distance_cm": self.distance_cm,
            'bbox': self.bbox,
            'timestamp': self.timestamp,
            'created_at': datetime.now()
        }

class DetectionBatch:
    def __init__(self, detections: List[Detection], frame_info: Optional[Dict[str, Any]] = None):
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
