import math
import os
import sys
from typing import Optional, Dict, Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingAlgorithm, \
    QgsProcessingParameterNumber, \
    QgsProcessingOutputNumber, QgsProcessingException

try:
    sys.path.index(os.path.dirname(os.path.abspath(__file__)))
except ValueError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEFAULT_SSA_VALUE = 1


class CalculateWupProcessingScript(QgsProcessingAlgorithm):  # type: ignore
    DIS = 'DIS'
    LUP = 'LUP'
    SSA = 'SSA'

    OUTPUT = 'WUP'

    @staticmethod
    def tr(string: str) -> str:
        return QCoreApplication.translate('Processing', string)  # type: ignore

    @staticmethod
    def createInstance() -> 'CalculateWupProcessingScript':
        return CalculateWupProcessingScript()

    @staticmethod
    def name() -> str:
        return 'usl_wup_calculator'

    def displayName(self) -> str:
        return self.tr('USL WUP Calculator')

    def group(self) -> str:
        return self.tr('Urban Sprawl')

    @staticmethod
    def groupId() -> str:
        return 'usl'

    def shortHelpString(self) -> str:
        return self.tr('Calculate weighted urban proliferation (WUP)'
                       '\nConstraints:'
                       '\n- SSA value needs to be between 0 and 1 or less')

    def initAlgorithm(self, _: Optional[Dict[str, Any]] = None) -> None:  # type: ignore
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DIS,
                self.tr('Degree of urban dispersion (DIS)'),
                QgsProcessingParameterNumber.Double,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.LUP,
                self.tr('Land uptake per person (LUP)'),
                QgsProcessingParameterNumber.Double,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SSA,
                self.tr('Share of settlement area (SSA)'),
                QgsProcessingParameterNumber.Double,
                defaultValue=DEFAULT_SSA_VALUE
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
                         _: QgsProcessingFeedback) -> Dict[str, Any]:
        dis_value = self.parameterAsDouble(parameters, self.DIS, context)
        lup_value = self.parameterAsDouble(parameters, self.LUP, context)
        ssa_value = self.parameterAsDouble(parameters, self.SSA, context)

        if ssa_value < 0 or ssa_value > 1:
            raise QgsProcessingException('SSA value needs to be between 0 and 1 or less')

        up = ssa_value * dis_value

        value1 = math.exp(4.159 - 613.125 / lup_value)
        weight1 = value1 / (1 + value1)

        value2 = math.exp(0.294432 * dis_value - 12.955)
        weight2 = value2 / (1 + value2)

        return {self.OUTPUT: up * dis_value * weight1 * (0.5 + weight2)}
