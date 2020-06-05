import os
import sys
from typing import Optional, Dict, Any

import numpy
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingAlgorithm, \
    QgsProcessingParameterRasterLayer, QgsProcessingException, QgsProcessingOutputNumber

try:
    sys.path.index(os.path.dirname(os.path.abspath(__file__)))
except ValueError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class CalculateDisProcessingScript(QgsProcessingAlgorithm):  # type: ignore
    SI_RASTER = 'SI_RASTER'

    OUTPUT = 'DIS'

    @staticmethod
    def tr(string: str) -> str:
        return QCoreApplication.translate('Processing', string)  # type: ignore

    @staticmethod
    def createInstance() -> 'CalculateDisProcessingScript':
        return CalculateDisProcessingScript()

    @staticmethod
    def name() -> str:
        return 'usl_dis_calculator'

    def displayName(self) -> str:
        return self.tr('USL DIS Calculator')

    def group(self) -> str:
        return self.tr('Urban Sprawl')

    @staticmethod
    def groupId() -> str:
        return 'usl'

    def shortHelpString(self) -> str:
        return self.tr('Calculate degree of urban dispersion (DIS)')

    def initAlgorithm(self, _: Optional[Dict[str, Any]] = None) -> None:  # type: ignore
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.SI_RASTER,
                self.tr('SI Raster')
            )
        )

        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT,
                self.tr('Degree of urban dispersion (DIS)')
            )
        )

    def processAlgorithm(self,  # type: ignore
                         parameters: Dict[str, Any],
                         context: QgsProcessingContext,
                         _: QgsProcessingFeedback) -> Dict[str, Any]:
        from urban_sprawl.common.common import Common

        si_raster_path = self.parameterAsRasterLayer(parameters, self.SI_RASTER, context).source()

        si_matrix = Common.get_matrix_from_path(si_raster_path)

        shape = Common.get_shape(si_matrix)

        count = 0
        for x in range(0, shape.rows):
            for y in range(0, shape.columns):
                if si_matrix[x, y] > 0:
                    count += 1

        if count != 0:
            dis = numpy.sum(si_matrix) / count
        else:
            raise QgsProcessingException('Si Values cant be found')

        return {self.OUTPUT: dis.item()}
