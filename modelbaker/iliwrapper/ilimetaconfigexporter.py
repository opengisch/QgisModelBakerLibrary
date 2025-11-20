"""
Metadata:
    Creation Date: 2024-11-20
    Copyright: (C) 2024 by Germán Carrillo
    Contact: german@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""
from .ili2dbconfig import ExportMetaConfigConfiguration, Ili2DbCommandConfiguration
from .iliexecutable import IliExecutable


class MetaConfigExporter(IliExecutable):
    def __init__(self, parent=None):
        """
        Description to do

        Args:
            parent (TYPE): Description to do.

        Returns:
            TYPE: Description to do.
        """

        super().__init__(parent)
        self.version = 4

    def _create_config(self) -> Ili2DbCommandConfiguration:
        """
        Description to do

        Returns:
            Ili2DbCommandConfiguration: Description to do.
        """

        return ExportMetaConfigConfiguration()

    def _get_ili2db_version(self):
        """
        Description to do

        Returns:
            TYPE: Description to do.
        """

        return self.version
