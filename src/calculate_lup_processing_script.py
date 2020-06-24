from typing import Optional, Dict, Any, cast

from osgeo import gdal
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingAlgorithm, \
    QgsProcessingParameterRasterLayer, QgsProcessingParameterNumber, \
    QgsProcessingOutputNumber, QgsProcessingException

from . import constants
from .urban_sprawl.common.common import Common


class CalculateLupProcessingScript(QgsProcessingAlgorithm):  # type: ignore
    BUILD_UP_VALUE = 'BUILD_UP_VALUE'

    RESIDENT_COUNT = 'RESIDENT_COUNT'
    EMPLOYEE_COUNT = 'EMPLOYEE_COUNT'

    CLIPPED_RASTER = 'CLIPPED_RASTER'

    OUTPUT = 'LUP'

    @staticmethod
    def tr(string: str) -> str:
        return QCoreApplication.translate('Processing', string)  # type: ignore

    @staticmethod
    def createInstance() -> 'CalculateLupProcessingScript':
        return CalculateLupProcessingScript()

    @staticmethod
    def name() -> str:
        return 'usl_lup_calculator'

    def displayName(self) -> str:
        return self.tr('USL LUP Calculator')

    def group(self) -> str:
        return self.tr(constants.GROUP_NAME)

    @staticmethod
    def groupId() -> str:
        return constants.GROUP_ID

    def shortHelpString(self) -> str:
        return self.tr('Calculate land uptake per person (LUP)'
                       '\nConstraints:'
                       '\n- Sum of resident and employee count can not equal 0 or less')

    def initAlgorithm(self, _: Optional[Dict[str, Any]] = None) -> None:  # type: ignore
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RESIDENT_COUNT,
                self.tr('Resident count'),
                QgsProcessingParameterNumber.Integer,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.EMPLOYEE_COUNT,
                self.tr('Employee count'),
                QgsProcessingParameterNumber.Integer,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUILD_UP_VALUE,
                self.tr('Raster build up value'),
                QgsProcessingParameterNumber.Integer,
                defaultValue=constants.BUILD_UP_VALUE
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.CLIPPED_RASTER,
                self.tr('Clipped Raster')
            )
        )

        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT,
                self.tr('Land uptake per person (LUP)')
            )
        )

    def processAlgorithm(self,  # type: ignore
                         parameters: Dict[str, Any],
                         context: QgsProcessingContext,
                         _: QgsProcessingFeedback) -> Dict[str, Any]:
        clipped_raster_path = self.parameterAsRasterLayer(parameters, self.CLIPPED_RASTER, context).source()
        resident_count = self.parameterAsInt(parameters, self.RESIDENT_COUNT, context)
        employee_count = self.parameterAsInt(parameters, self.EMPLOYEE_COUNT, context)
        build_up_value = self.parameterAsInt(parameters, self.BUILD_UP_VALUE, context)

        resident_employee_count = resident_count + employee_count
        if resident_employee_count <= 0:
            raise QgsProcessingException('Sum of resident and employee count can not equal 0 or less')

        build_up_area = Common.get_area(gdal.Open(clipped_raster_path), lambda x: cast(bool, x == build_up_value))

        return {self.OUTPUT: build_up_area / resident_employee_count}
