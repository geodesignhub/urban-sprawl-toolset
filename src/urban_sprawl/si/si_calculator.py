import math
from typing import Optional

import gdal
import numpy
from qgis.core import QgsPoint

from ...urban_sprawl.common.common import Common


class SiCalculator:
    def __init__(self,
                 raster_path: str,
                 clipped_raster_path: str,
                 radius: int,
                 no_data_value: int,
                 build_up_value: int):
        self._matrix = Common.get_matrix_from_path(raster_path)
        self._clipped_matrix = Common.get_matrix_from_path(clipped_raster_path)

        self._radius = radius
        self._no_data_value = no_data_value
        self._build_up_value = build_up_value

        self._pixel_size = Common.get_pixel_size(gdal.Open(raster_path))
        self._wcc = self._calculate_wcc(self._pixel_size)

    @staticmethod
    def _calculate_wcc(pixel_size: float) -> float:
        return math.sqrt(0.97428 * pixel_size + 1.046) - 0.996249

    def _calculate_point(self,
                         center_x: int,
                         center_y: int) -> Optional[float]:
        shape = Common.get_shape(self._matrix)
        offset = round(self._radius / self._pixel_size)

        count = 0
        distance_sum = float(0)

        for x in range(max(0, center_x - offset), min(shape.rows, center_x + offset + 1)):
            for y in range(max(0, center_y - offset), min(shape.columns, center_y + offset + 1)):
                if self._matrix[x, y] == self._build_up_value:
                    distance = QgsPoint(center_x, center_y).distance(QgsPoint(x, y)) * self._pixel_size

                    if distance <= self._radius:
                        count += 1
                        distance_sum += math.sqrt((distance * 2) + 1) - 1

        if count > 0:
            return (distance_sum + self._wcc) / count
        else:
            return None

    def calculate(self) -> numpy.ndarray:
        shape = Common.get_shape(self._clipped_matrix)

        result_matrix = numpy.full(shape=(shape.rows, shape.columns), fill_value=self._no_data_value, dtype=float)

        for x in range(0, shape.rows):
            for y in range(0, shape.columns):
                if self._clipped_matrix[x, y] == self._build_up_value:
                    result = self._calculate_point(x, y)

                    if result:
                        result_matrix[x, y] = result

        return result_matrix
