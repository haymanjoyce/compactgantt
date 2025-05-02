from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TimeFrame:
    time_frame_id: int
    finish_date: str
    width_proportion: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeFrame':
        return cls(
            time_frame_id=data["time_frame_id"],
            finish_date=data["finish_date"],
            width_proportion=data["width_proportion"]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time_frame_id": self.time_frame_id,
            "finish_date": self.finish_date,
            "width_proportion": self.width_proportion
        }