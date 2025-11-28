from qgis.core import QgsProcessingAlgorithm


class UtilAlgorithm(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()

    def group(self):
        return self.tr("Utils")

    def groupId(self):
        return "utils"
