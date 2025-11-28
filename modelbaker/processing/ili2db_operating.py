"""
Metadata:
    Creation Date: 2025-10-10
    Copyright: (C) 2025 by Dave Signer
    Contact: david@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""

from qgis.PyQt.QtCore import QCoreApplication, QObject

from ..utils.db_utils import get_db_connector
from ..utils.globals import MODELS_BLACKLIST


class ProcessOperatorBase(QObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def _get_tid_handling(self, configuration):
        db_connector = get_db_connector(configuration)
        if db_connector:
            return db_connector.get_tid_handling()
        return False

    def _basket_handling(self, configuration):
        db_connector = get_db_connector(configuration)
        if db_connector:
            return db_connector.get_basket_handling()
        return False

    def _get_model_names(self, configuration):
        modelnames = []

        db_connector = get_db_connector(configuration)
        if (
            db_connector
            and db_connector.db_or_schema_exists()
            and db_connector.metadata_exists()
        ):
            db_models = db_connector.get_models()
            for db_model in db_models:
                name = db_model["modelname"]
                if name and name not in modelnames and name not in MODELS_BLACKLIST:
                    modelnames.append(name)
        return modelnames

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)
