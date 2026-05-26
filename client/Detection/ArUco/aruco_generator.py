import cv2

class ArucoGenerator:
    @staticmethod
    def generate_markers(output_dir: str = ".", dict_type: int = cv2.aruco.DICT_6X6_250, 
                        count: int = 36, size: int = 200) -> None:
        dictionary = cv2.aruco.getPredefinedDictionary(dict_type)
        for i in range(count):
            marker_image = cv2.aruco.generateImageMarker(dictionary, i, size, 1)
            cv2.imwrite(f"{output_dir}/marker{i}.png", marker_image)