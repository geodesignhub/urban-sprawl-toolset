from typing import Dict, Any, Optional

import gdal
import numpy
from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingAlgorithm, \
    QgsProcessingParameterRasterLayer, QgsProcessingParameterRasterDestination, \
    QgsProcessingParameterNumber, QgsProcessingParameterFeatureSource

from . import constants
from .urban_sprawl.clip_raster.raster_clipper import RasterClipper
from .urban_sprawl.common.common import Common


class ClipRasterProcessingScript(QgsProcessingAlgorithm):  # type: ignore
    NO_DATA_VALUE = 'NO_DATA_VALUE'

    RASTER = 'RASTER'
    VECTOR = 'VECTOR'

    OUTPUT = 'CLIPPED_RASTER'

    @staticmethod
    def tr(string: str) -> str:
        return QCoreApplication.translate('Processing', string)  # type: ignore

    @staticmethod
    def createInstance() -> 'ClipRasterProcessingScript':
        return ClipRasterProcessingScript()

    @staticmethod
    def name() -> str:
        return 'usl_clip_raster'

    def displayName(self) -> str:
        return self.tr('USL Clip Raster')

    def group(self) -> str:
        return self.tr(constants.GROUP_NAME)

    @staticmethod
    def groupId() -> str:
        return constants.GROUP_ID

    def shortHelpString(self) -> str:
        return self.tr('Clip raster with the provided polygon.'
                       ' This processing script normalizes the raster and speeds up the SI calculation.')

    def initAlgorithm(self, _: Optional[Dict[str, Any]] = None) -> None:  # type: ignore
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NO_DATA_VALUE,
                self.tr('Raster no data value'),
                QgsProcessingParameterNumber.Integer,
                defaultValue=constants.NO_DATA_VALUE
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER,
                self.tr('Raster')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.VECTOR,
                self.tr('Polygon to clip')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Output Clipped Raster')
            )
        )

    def processAlgorithm(self,  # type: ignore
                         parameters: Dict[str, Any],
                         context: QgsProcessingContext,
                         _: QgsProcessingFeedback) -> Dict[str, Any]:
        raster_path = self.parameterAsRasterLayer(parameters, self.RASTER, context).source()
        no_data_value = self.parameterAsInt(parameters, self.NO_DATA_VALUE, context)

        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        clipped_raster_path = processing.run(
            'gdal:cliprasterbymasklayer',
            {
                'INPUT': parameters[self.RASTER],
                'MASK': parameters[self.VECTOR],
                'OUTPUT': parameters[self.OUTPUT]
            }
        )['OUTPUT']

        raster = gdal.Open(raster_path)

        pixel_size = Common.get_pixel_size(raster)

        clipped_normalized_matrix = RasterClipper.get_clipped_normalized_matrix(raster_path,
                                                                                clipped_raster_path,
                                                                                pixel_size,
                                                                                no_data_value)
        shape = Common.get_shape(clipped_normalized_matrix)

        driver = gdal.GetDriverByName('GTiff')
        clipped_normalized_raster = driver.Create(output_path,
                                                  bands=1,
                                                  xsize=shape.columns,
                                                  ysize=shape.rows,
                                                  eType=gdal.GDT_Int16)
        clipped_normalized_raster.GetRasterBand(1).WriteArray(numpy.asarray(clipped_normalized_matrix))
        clipped_normalized_raster.SetGeoTransform(raster.GetGeoTransform())
        clipped_normalized_raster.SetProjection(raster.GetProjection())
        clipped_normalized_raster.FlushCache()

        return {self.OUTPUT: output_path}
