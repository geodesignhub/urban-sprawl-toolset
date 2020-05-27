import os
import sys
from typing import Optional, Dict, Any

import numpy
from osgeo import gdal
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingAlgorithm, \
    QgsProcessingParameterRasterLayer, QgsProcessingParameterRasterDestination, QgsProcessingParameterNumber

try:
    sys.path.index(os.path.dirname(os.path.abspath(__file__)))
except ValueError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEFAULT_NO_DATA_VALUE = 0
DEFAULT_BUILD_UP_VALUE = 1
DEFAULT_RADIUS = 2000


class CalculateSiProcessingScript(QgsProcessingAlgorithm):  # type: ignore
    NO_DATA_VALUE = 'NO_DATA_VALUE'
    BUILD_UP_VALUE = 'BUILD_UP_VALUE'
    RADIUS = 'RADIUS'

    RASTER = 'RASTER'
    CLIPPED_RASTER = 'CLIPPED_RASTER'

    OUTPUT = 'SI_RASTER'

    @staticmethod
    def tr(string: str) -> str:
        return QCoreApplication.translate('Processing', string)  # type: ignore

    @staticmethod
    def createInstance() -> 'CalculateSiProcessingScript':
        return CalculateSiProcessingScript()

    @staticmethod
    def name() -> str:
        return 'usl_si_calculator'

    def displayName(self) -> str:
        return self.tr('USL SI Calculator')

    def group(self) -> str:
        return self.tr('Urban Sprawl')

    @staticmethod
    def groupId() -> str:
        return 'usl'

    def shortHelpString(self) -> str:
        return self.tr('Calculate SI raster')

    def initAlgorithm(self, _: Optional[Dict[str, Any]] = None) -> None:  # type: ignore
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NO_DATA_VALUE,
                self.tr('Raster no data value'),
                QgsProcessingParameterNumber.Integer,
                defaultValue=DEFAULT_NO_DATA_VALUE
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUILD_UP_VALUE,
                self.tr('Raster build up value'),
                QgsProcessingParameterNumber.Integer,
                defaultValue=DEFAULT_BUILD_UP_VALUE
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.RADIUS,
                self.tr('Horizon of perception'),
                QgsProcessingParameterNumber.Integer,
                defaultValue=DEFAULT_RADIUS
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER,
                self.tr('Raster')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.CLIPPED_RASTER,
                self.tr('Clipped Raster')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Output SI Raster')
            )
        )

    def processAlgorithm(self,  # type: ignore
                         parameters: Dict[str, Any],
                         context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback) -> Dict[str, Any]:
        from urban_sprawl.common.common import Common
        from urban_sprawl.si.si_calculator import SiCalculator

        raster_path = self.parameterAsRasterLayer(parameters, self.RASTER, context).source()
        clipped_raster_path = self.parameterAsRasterLayer(parameters, self.CLIPPED_RASTER, context).source()
        no_data_value = self.parameterAsInt(parameters, self.NO_DATA_VALUE, context)
        build_up_value = self.parameterAsInt(parameters, self.BUILD_UP_VALUE, context)
        radius = self.parameterAsInt(parameters, self.RADIUS, context)
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        feedback.pushInfo('Processing...')

        si_calculator = SiCalculator(raster_path,
                                     clipped_raster_path,
                                     radius,
                                     no_data_value,
                                     build_up_value)

        result_matrix = si_calculator.calculate()

        raster = gdal.Open(raster_path)
        shape = Common.get_shape(result_matrix)

        driver = gdal.GetDriverByName('GTiff')
        si_raster = driver.Create(output_path,
                                  bands=1,
                                  xsize=shape.columns,
                                  ysize=shape.rows,
                                  eType=gdal.GDT_Float32)
        si_raster.GetRasterBand(1).WriteArray(numpy.asarray(result_matrix))
        si_raster.SetGeoTransform(raster.GetGeoTransform())
        si_raster.SetProjection(raster.GetProjection())
        si_raster.FlushCache()

        return {self.OUTPUT: output_path}
