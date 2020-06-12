from qgis.core import QgsProcessingProvider

from .src import constants
from .src.calculate_dis_processing_script import CalculateDisProcessingScript
from .src.calculate_lup_processing_script import CalculateLupProcessingScript
from .src.calculate_si_processing_script import CalculateSiProcessingScript
from .src.calculate_wup_processing_script import CalculateWupProcessingScript
from .src.clip_raster_processing_script import ClipRasterProcessingScript
from .src.urban_sprawl_calculator_processing_script import UrbanSprawlCalculatorProcessingScript


class UrbanSprawlProvider(QgsProcessingProvider):
    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self) -> None:
        pass

    def loadAlgorithms(self) -> None:
        self.addAlgorithm(CalculateDisProcessingScript())
        self.addAlgorithm(CalculateLupProcessingScript())
        self.addAlgorithm(CalculateSiProcessingScript())
        self.addAlgorithm(CalculateWupProcessingScript())
        self.addAlgorithm(ClipRasterProcessingScript())
        self.addAlgorithm(UrbanSprawlCalculatorProcessingScript())

    def id(self) -> str:
        return constants.GROUP_ID

    def name(self) -> str:
        return self.tr(constants.GROUP_NAME)

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def longName(self) -> str:
        return self.name()
