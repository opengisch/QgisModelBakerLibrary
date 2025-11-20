"""
Metadata:
    Creation Date: 2017-05-30
    Copyright: (C) 2017 by Germán Carrillo (BSF-Swissphoto)
    Contact: gcarrillo@linuxmail.org

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""
from .ili2dbconfig import ExportConfiguration, Ili2DbCommandConfiguration
from .iliexecutable import IliExecutable


class Exporter(IliExecutable):
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

        return ExportConfiguration()

    def _get_ili2db_version(self):
        """
        Description to do

        Returns:
            TYPE: Description to do.
        """

        return self.version

    def _args(self, hide_password):
        """
        Description to do

        Args:
            hide_password (TYPE): Description to do.

        Returns:
            TYPE: Description to do.
        """

        args = super()._args(hide_password)

        if self.version == 3 and "--export3" in args:
            args.remove("--export3")

        return args
