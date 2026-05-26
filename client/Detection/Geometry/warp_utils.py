import cv2
import numpy as np

from Detection.Geometry import GeometryUtils

class AffineTransformer:
    @staticmethod
    def transform_board(image: np.ndarray, transform_params: np.ndarray, width: int, height: int) -> np.ndarray:

        warped = cv2.warpAffine(image, transform_params, (width, height))
        return cv2.copyMakeBorder(warped, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(100, 100, 100))

    @staticmethod
    def get_transform_params(source_corners: np.ndarray) -> np.ndarray:
        source_corners = source_corners.astype(np.float32)
        
        width = int(GeometryUtils.calculate_distance(source_corners[0], source_corners[1]))
        height = int(GeometryUtils.calculate_distance(source_corners[0], source_corners[2]))
        
        dst_corners = np.array([
            [0, 0],
            [width, 0],
            [0, height]
        ], dtype=np.float32)

        transform_matrix = cv2.getAffineTransform(source_corners, dst_corners)
        return transform_matrix,width,height