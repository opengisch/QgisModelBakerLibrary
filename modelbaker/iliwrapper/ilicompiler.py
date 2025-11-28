"""
/***************************************************************************
                              -------------------
        begin                : 25/11/11
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from .ili2dbconfig import Ili2CCommandConfiguration
from .ili2dbutils import get_ili2c_bin
from .iliexecutable import IliExecutable


class IliCompiler(IliExecutable):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_config(self) -> Ili2CCommandConfiguration:
        """Creates the configuration that will be used by *run* method.
        :return: ili2c configuration"""
        return Ili2CCommandConfiguration()

    def _args(self, param):
        """Gets the list of ili2c arguments from configuration.
        :return: ili2c arguments list.
        :rtype: list
        """
        # todo care about param (it should not be considered)
        return self.configuration.to_ili2c_args()

    def _ili2_jar_arg(self):
        ili2c_bin = get_ili2c_bin(self.stdout, self.stderr)
        if not ili2c_bin:
            return self.ILI2C_NOT_FOUND
        return ["-jar", ili2c_bin]
