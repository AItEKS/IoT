from typing import List, Tuple, Dict
import cv2
import numpy as np

from Detection.ArUco import MarkersDetector, BoardCorners
from Detection.Geometry import GeometryUtils

class BoardCalibrator:
    def __init__(self, detector: MarkersDetector):
        self.detector = detector

    def find_board_corners(self, markers: List[np.ndarray], 
                          image_shape: Tuple[int, int]) -> BoardCorners:
        height, width = image_shape
        corners = [
            np.array([0, 0]),           # upper_left
            np.array([width, 0]),       # upper_right
            np.array([0, height])       # bottom_left
        ]
        
        closest_markers = [None, None, None]
        min_distances = [float('inf')] * 3

        for marker in markers:
            center = np.mean(marker[0], axis=0)
            for i, corner in enumerate(corners):
                distance = GeometryUtils.calculate_distance(corner, center)
                if distance < min_distances[i]:
                    min_distances[i] = distance
                    closest_markers[i] = marker

        return BoardCorners(*closest_markers)

    def calculate_grid_dimensions(self, warped_image: np.ndarray) -> Tuple[Dict[float, np.ndarray], Dict[float, np.ndarray]]:
        detection = self.detector.detect(warped_image)
        if detection.ids is None:
            return 0, 0

        corners = self.find_board_corners(
            detection.corners, 
            (warped_image.shape[0], warped_image.shape[1])
        )

        first_col_rect = GeometryUtils.get_min_area_rect_points(
            np.vstack([corners.upper_left[0], corners.upper_right[0]])
        )
        first_row_rect = GeometryUtils.get_min_area_rect_points(
            np.vstack([corners.upper_left[0], corners.bottom_left[0]])
        )

        cols = {}
        rows = {}
        for marker in detection.corners:
            center = np.mean(marker[0], axis=0)
            if cv2.pointPolygonTest(first_col_rect, center, False) > 0:
                cols[center[0]] = marker[0]
            if cv2.pointPolygonTest(first_row_rect, center, False) > 0:
                rows[center[1]] = marker[0]

        return cols, rows
    
    def calculate_coordinate_grid(
        self, 
        rows_dict: Dict[Tuple[float, float], Tuple[int, int]], 
        cols_dict: Dict[Tuple[float, float], Tuple[int, int]]
    ) -> Dict[Tuple[float,float],Tuple[float,float]]:
        rows_keys = list(rows_dict.keys())
        rows_keys.sort()
        cols_keys = list(cols_dict.keys())
        cols_keys.sort()
        coordinate_grid = {}
        for col_index,col in enumerate(cols_keys):
            for row_index,row in enumerate(rows_keys):
                coordinate_grid[(col,row)] = (col_index, row_index)
        return coordinate_grid
                
