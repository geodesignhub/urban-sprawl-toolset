from typing import Dict, Any, Optional

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessingOutputNumber, QgsProcessingParameterVectorLayer, \
    QgsProcessingContext, QgsProcessingFeedback, QgsProcessing, QgsProcessingAlgorithm, \
    QgsProcessingParameterRasterLayer, QgsProcessingParameterNumber, QgsProcessingParameterRasterDestination, \
    QgsProcessingException

from . import constants


class UrbanSprawlCalculatorProcessingScript(QgsProcessingAlgorithm):  # type: ignore
    SSA = 'SSA'
    NO_DATA_VALUE = 'NO_DATA_VALUE'
    BUILD_UP_VALUE = 'BUILD_UP_VALUE'

    RESIDENT_COUNT = 'RESIDENT_COUNT'
    EMPLOYEE_COUNT = 'EMPLOYEE_COUNT'

    RASTER = 'RASTER'
    VECTOR = 'VECTOR'

    OUTPUT_RASTER = 'SI_RASTER'
    OUTPUT = 'WUP'

    @staticmethod
    def tr(string: str) -> str:
        return QCoreApplication.translate('Processing', string)  # type: ignore

    @staticmethod
    def createInstance() -> 'UrbanSprawlCalculatorProcessingScript':
        return UrbanSprawlCalculatorProcessingScript()

    @staticmethod
    def name() -> str:
        return 'usl_urban_sprawl_calculator'

    def displayName(self) -> str:
        return self.tr('USL Urban Sprawl Calculator')

    def group(self) -> str:
        return self.tr(constants.GROUP_NAME)

    @staticmethod
    def groupId() -> str:
        return constants.GROUP_ID

    def shortHelpString(self) -> str:
        return self.tr(
            'This calculator simplifies the calculation of weighted urban proliferation (WUP).'
            '\nConstraints:'
            '\n- Sum of resident and employee count can not equal 0 or less'
            '\n- SSA value needs to be between 0 and 1 or less'
            '\nExecution order:'
            '\n1. USL Clip Raster (usl_clip_raster)'
            '\n2. USL SI Calculator (usl_si_calculator)'
            '\n3. USL DIS Calculator (usl_dis_calculator)'
            '\n4. USL LUP Calculator (usl_lup_calculator)'
            '\n5. USL WUP Calculator (usl_wup_calculator)'
        )

    def initAlgorithm(self, _: Optional[Dict[str, Any]] = None) -> None:  # type: ignore
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RESIDENT_COUNT,
                self.tr('Resident count in vector boundary'),
                QgsProcessingParameterNumber.Integer,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.EMPLOYEE_COUNT,
                self.tr('Employee count in vector boundary'),
                QgsProcessingParameterNumber.Integer,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SSA,
                self.tr('Share of settlement area (SSA)'),
                QgsProcessingParameterNumber.Double,
                defaultValue=constants.SSA_VALUE
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER,
                self.tr('Raster with build up area')
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.VECTOR,
                self.tr('Vector with boundaries for calculations'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_RASTER,
                self.tr('Output SI Raster')
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.NO_DATA_VALUE,
                self.tr('Raster no data value'),
                QgsProcessingParameterNumber.Integer,
                defaultValue=constants.NO_DATA_VALUE
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

        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT,
                self.tr('Weighted urban proliferation (WUP)')
            )
        )

    def processAlgorithm(self,  # type: ignore
                         parameters: Dict[str, Any],
                         context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback) -> Dict[str, Any]:
        resident_count = self.parameterAsInt(parameters, self.RESIDENT_COUNT, context)
        employee_count = self.parameterAsInt(parameters, self.EMPLOYEE_COUNT, context)
        ssa_value = self.parameterAsDouble(parameters, self.SSA, context)

        resident_employee_count = resident_count + employee_count
        if resident_employee_count <= 0:
            raise QgsProcessingException('Sum of resident and employee count can not equal 0 or less')

        if ssa_value < 0 or ssa_value > 1:
            raise QgsProcessingException('SSA value needs to be between 0 and 1 or less')

        outputs = {}

        # USL Clip Raster
        alg_params = {
            'NO_DATA_VALUE': parameters[self.NO_DATA_VALUE],
            'RASTER': parameters[self.RASTER],
            'VECTOR': parameters[self.VECTOR],
            'CLIPPED_RASTER': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UslClipRaster'] = processing.run('usl:usl_clip_raster', alg_params, context=context,
                                                  feedback=feedback, is_child_algorithm=True)
        if feedback.isCanceled():
            return {}

        # USL SI Calculator
        alg_params = {
            'BUILD_UP_VALUE': parameters[self.BUILD_UP_VALUE],
            'CLIPPED_RASTER': outputs['UslClipRaster']['CLIPPED_RASTER'],
            'NO_DATA_VALUE': parameters[self.NO_DATA_VALUE],
            'RADIUS': constants.RADIUS_VALUE,
            'RASTER': parameters[self.RASTER],
            'SI_RASTER': parameters[self.OUTPUT_RASTER]
        }
        outputs['UslSiCalculator'] = processing.run('usl:usl_si_calculator', alg_params, context=context,
                                                    feedback=feedback, is_child_algorithm=True)
        if feedback.isCanceled():
            return {}

        # USL DIS Calculator
        alg_params = {
            'SI_RASTER': outputs['UslSiCalculator']['SI_RASTER']
        }
        outputs['UslDisCalculator'] = processing.run('usl:usl_dis_calculator', alg_params, context=context,
                                                     feedback=feedback, is_child_algorithm=True)

        if feedback.isCanceled():
            return {}

        # USL LUP Calculator
        alg_params = {
            'BUILD_UP_VALUE': parameters[self.BUILD_UP_VALUE],
            'CLIPPED_RASTER': outputs['UslClipRaster']['CLIPPED_RASTER'],
            'EMPLOYEE_COUNT': employee_count,
            'RESIDENT_COUNT': resident_count
        }
        outputs['UslLupCalculator'] = processing.run('usl:usl_lup_calculator', alg_params, context=context,
                                                     feedback=feedback, is_child_algorithm=True)

        if feedback.isCanceled():
            return {}

        # USL WUP Calculator
        alg_params = {
            'DIS': outputs['UslDisCalculator']['DIS'],
            'LUP': outputs['UslLupCalculator']['LUP'],
            'SSA': ssa_value
        }
        outputs['UslWupCalculator'] = processing.run('usl:usl_wup_calculator', alg_params, context=context,
                                                     feedback=feedback, is_child_algorithm=True)

        return {self.OUTPUT: outputs['UslWupCalculator']['WUP']}
