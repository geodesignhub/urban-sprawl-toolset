from typing import Callable

import gdal
import numpy

from ..common.gdal_geo_transform import GdalGeoTransform
from ..common.numpy_shape import NumpyShape


class Common:
    @staticmethod
    def get_geo_transform(raster: gdal.Dataset) -> GdalGeoTransform:
        return GdalGeoTransform.parse(raster.GetGeoTransform())

    @staticmethod
    def get_shape(matrix: numpy.ndarray) -> NumpyShape:
        return NumpyShape.parse(matrix.shape)

    @staticmethod
    def get_pixel_size(raster: gdal.Dataset) -> float:
        geo_transform = Common.get_geo_transform(raster)

        if geo_transform.pixel_size_x == geo_transform.pixel_size_y:
            return geo_transform.pixel_size_x
        else:
            raise ValueError('Pixels are not square')

    @staticmethod
    def get_matrix_from_path(path: str) -> numpy.ndarray:
        raster = gdal.Open(path)

        return numpy.array(raster.GetRasterBand(1).ReadAsArray())

    @staticmethod
    def get_area(raster: gdal.Dataset, selection_function: Callable[[float], bool]) -> float:
        matrix = numpy.array(raster.GetRasterBand(1).ReadAsArray())

        shape = Common.get_shape(matrix)
        pixel_size = Common.get_pixel_size(raster)

        count = 0
        for x in range(0, shape.rows):
            for y in range(0, shape.columns):
                if selection_function(matrix[x, y]):
                    count += 1

        return (pixel_size ** 2) * count
