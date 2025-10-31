import os

from qgis.core import QgsProcessingAlgorithm
from qgis.PyQt.QtGui import QIcon


class UtilAlgorithm(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()

    def group(self):
        return self.tr("Utils")

    def groupId(self):
        return "utils"
