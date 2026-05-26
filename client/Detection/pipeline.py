import cv2
import numpy as np
import json
import os
from typing import Tuple, Dict, List

from Detection.Geometry import GeometryUtils, AffineTransformer
from Detection.ArUco import MarkersDetector, MarkerData, Direction
from Detection import BoardCalibrator

class CalibrationPipeline:
    _grid: Dict[Tuple[float,float],Tuple[float,float]] = None
    _transform_params: np.ndarray = None
    _width = 0
    _height = 0

    def __init__(self):
        self.detector = MarkersDetector()
        self.calibrator = BoardCalibrator(self.detector)
        self.transformer = AffineTransformer()
        self._grid: Dict[Tuple[float,float],Tuple[float,float]] = None
        self._transform_params: np.ndarray = None
        self._width = 0
        self._height = 0
        self._cols = 0
        self._rows = 0

    def process_image(self, image: np.ndarray) -> None:
        detection = self.detector.detect(image)

        if detection.ids is None:
            print("Маркеры не обнаружены")
            return

        # Поиск общего ограничивающего прямоугольника
        all_corners=[]
        for corner in detection.corners:
            for point in corner[0]:
                all_corners.append(point)
        all_corners = np.array(all_corners)

        board_rect = GeometryUtils.get_min_area_rect_points(all_corners)
        center = board_rect.mean(axis=0)
        expanded_rect = center + (board_rect - center) * 1.15
        
        # Выбор трех ключевых углов
        source_corners = np.array([expanded_rect[0], expanded_rect[1], expanded_rect[3]])

        # Перспективная коррекция
        self._transform_params, self._width, self._height = self.transformer.get_transform_params(source_corners)
        warped = self.transformer.transform_board(image, self._transform_params, self._width, self._height)

        # Расчет сетки
        cols_centers, rows_centers = self.calibrator.calculate_grid_dimensions(warped)
        self._grid = self.calibrator.calculate_coordinate_grid(rows_centers, cols_centers)

        # print(f"Calibration Finished, grid size: {len(cols_centers)}x{len(rows_centers)}")
        self._rows = len(rows_centers)
        self._cols = len(cols_centers)
        return self._grid != {}

    def get_board_data(self, image: np.ndarray) -> List[MarkerData]:
        warped = self.transformer.transform_board(image, self._transform_params, self._width, self._height)
        detection = self.detector.detect(warped)
        result = []

        for index,cord in enumerate(detection.corners):
            grid = self.find_closest_grid(cord)

            center = cord[0].mean(axis=0)
            alignment = GeometryUtils.get_rotation_degree(cord[0][0], center)

            data = MarkerData(int(detection.ids[index][0]), grid, alignment)
            result.append(data)
            tmp = warped.copy()
            cv2.circle(tmp, center.astype(int), 10, (255,0,0), 3)
            # print(data)
            cv2.aruco.drawDetectedMarkers(tmp, detection.corners, detection.ids)

            # visualized
            cv2.imwrite('Calibrated.jpg', tmp)
            cv2.waitKey()
        return result

    def find_closest_grid(self, coordinate: np.ndarray) -> Tuple[int, int]:
        center = coordinate[0].mean(axis=0)
        min_dist = 1e10
        closest_grid=(1e10,1e10)
        # print(center)

        for cord in self._grid:
            dist = GeometryUtils.calculate_distance(cord,center)
            if dist < min_dist:
                min_dist = dist
                closest_grid = self._grid[cord]

        return closest_grid

    def get_json_data(self, image: np.ndarray) -> List[Dict]:
        result = {}
        result["rows"] = self._rows
        result["cols"] = self._cols

        matrix_data = []
        out = self.get_board_data(image)
        for marker_data in out:
            matrix_data.append(marker_data.dict())

        result["matrix"] = matrix_data
        return json.dumps(result)

    def save_calibration(self, filepath: str = "calibration_data.json"):
            """Сохраняет данные калибровки в JSON файл"""
            # JSON не поддерживает кортежи (tuple) в качестве ключей словаря,
            # поэтому преобразуем _grid в удобный список словарей
            grid_list = [{"px": list((float(k[0]),float(k[1]))), "grid": list(v)} for k, v in self._grid.items()]

            data = {
                "transform_params": self._transform_params.tolist() if self._transform_params is not None else None,
                "width": self._width,
                "height": self._height,
                "rows": self._rows,
                "cols": self._cols,
                "grid": grid_list
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Калибровка успешно сохранена в {filepath}")

    def load_calibration(self, filepath: str = "calibration_data.json") -> bool:
        """Загружает данные калибровки из JSON файла"""
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            self._transform_params = np.array(data["transform_params"], dtype=np.float32)
            self._width = data["width"]
            self._height = data["height"]
            self._rows = data["rows"]
            self._cols = data["cols"]

            # Восстанавливаем словарь _grid с ключами-кортежами (tuple)
            self._grid = {tuple(item["px"]): tuple(item["grid"]) for item in data["grid"]}

            return True
        except Exception as e:
            print(f"Ошибка при чтении файла калибровки: {e}")
            return False