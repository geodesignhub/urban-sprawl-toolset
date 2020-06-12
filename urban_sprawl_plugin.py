import inspect
import os
import sys

from qgis.core import QgsApplication

from .urban_sprawl_provider import UrbanSprawlProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

try:
    sys.path.index(cmd_folder)
except ValueError:
    sys.path.insert(0, cmd_folder)


class UrbanSprawlPlugin(object):
    def __init__(self):
        self.provider = None

    def initProcessing(self) -> None:
        self.provider = UrbanSprawlProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self) -> None:
        self.initProcessing()

    def unload(self) -> None:
        try:
            QgsApplication.processingRegistry().removeProvider(self.provider)
        except:
            pass
