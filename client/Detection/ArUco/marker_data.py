from dataclasses import dataclass
from typing import Tuple
from enum import Enum

class Direction(Enum):
    NOT_TURNED = 0
    TURNED_90_DEG = 1
    TURNED_180_DEG = 2
    TURNED_270_DEG  = 3

@dataclass
class MarkerData:
    id: int
    cords: Tuple[int,int]
    turn: Direction

    def dict(self):
        return { 'id': self.id, 'cords': self.cords, 'turn': self.turn.value }