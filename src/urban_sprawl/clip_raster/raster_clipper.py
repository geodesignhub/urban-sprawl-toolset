import gdal
import numpy

from ...urban_sprawl.common.common import Common


class RasterClipper:
    @staticmethod
    def get_clipped_normalized_matrix(raster_path: str,
                                      clipped_raster_path: str,
                                      pixel_size: float,
                                      no_data: int) -> numpy.ndarray:
        raster = gdal.Open(raster_path)
        clipped_raster = gdal.Open(clipped_raster_path)

        return RasterClipper._join_matrices(raster, clipped_raster, pixel_size, no_data)

    @staticmethod
    def _join_matrices(raster: gdal.Dataset,
                       clipped_raster: gdal.Dataset,
                       pixel_size: float,
                       no_data: int) -> numpy.ndarray:
        matrix = numpy.array(raster.GetRasterBand(1).ReadAsArray())
        clipped_matrix = numpy.array(clipped_raster.GetRasterBand(1).ReadAsArray())

        raster_geo_transform = Common.get_geo_transform(raster)
        clipped_raster_geo_transform = Common.get_geo_transform(clipped_raster)

        x_index = int((raster_geo_transform.position_y - clipped_raster_geo_transform.position_y) / pixel_size)
        y_index = int((clipped_raster_geo_transform.position_x - raster_geo_transform.position_x) / pixel_size)

        matrix_shape = Common.get_shape(matrix)
        clipped_matrix_shape = Common.get_shape(clipped_matrix)

        return_matrix = numpy.full((matrix_shape.rows, matrix_shape.columns), no_data)

        # @formatter:off
        return_matrix[x_index:x_index + clipped_matrix_shape.rows,
                      y_index:y_index + clipped_matrix_shape.columns] = clipped_matrix
        # @formatter:on

        return return_matrix
