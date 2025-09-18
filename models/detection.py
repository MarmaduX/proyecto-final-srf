from datetime import datetime
from typing import List, Dict, Any

class Detection:
    def __init__(self, confidence: float, timestamp: datetime = None):
        self.confidence = confidence
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'created_at': datetime.now()
        }

class DetectionBatch:
    def __init__(self, detections: List[Detection], frame_info: Dict[str, Any] = None):
        self.detections = detections
        self.frame_info = frame_info or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'detections': [det.to_dict() for det in self.detections],
            'frame_info': self.frame_info,
            'timestamp': self.timestamp,
            'created_at': datetime.now()
        }
