from dataclasses import dataclass
from typing import List, Optional
import cv2 
import numpy as np

@dataclass
class DetectionResult:
    corners: List[np.ndarray]
    ids: Optional[List[int]]
    rejected: List[np.ndarray]

@dataclass
class BoardCorners:
    upper_left: np.ndarray
    upper_right: np.ndarray
    bottom_left: np.ndarray

class MarkersDetector:

    def __init__(self, dict_type: int = cv2.aruco.DICT_6X6_250):
        self.dictionary = cv2.aruco.getPredefinedDictionary(dict_type)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)

    def detect(self, image: np.ndarray) -> DetectionResult:
        corners, ids, rejected = self.detector.detectMarkers(image)
        return DetectionResult(corners, ids, rejected)