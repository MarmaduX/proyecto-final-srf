from datetime import datetime
from typing import Optional, Dict, Any


class Location:
    def __init__(
        self,
        mesa: float,
        pata: float,
        source: Optional[str] = None,  # por ejemplo, 'robot' o 'gps'
        accuracy: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        self.mesa = mesa
        self.pata = pata
        self.source = source
        self.accuracy = accuracy
        self.extra = extra or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mesa": self.mesa,
            "pata": self.pata,
            "source": self.source,
            "accuracy": self.accuracy,
            "extra": self.extra,
            "timestamp": self.timestamp,
            "created_at": datetime.utcnow(),
        }
