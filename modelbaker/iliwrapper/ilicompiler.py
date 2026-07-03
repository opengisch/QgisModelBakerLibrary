"""
/***************************************************************************
        begin                : 2026-07-03
        git sha              : :%H$
        copyright            : (C) 2026 by Dave Signer
        email                : david at opengis ch
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
from .iliexecutable import Ili2CExecutable


class IliCompiler(Ili2CExecutable):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_config(self) -> Ili2CCommandConfiguration:
        """Creates the configuration that will be used by *run* method.
        :return: ili2c configuration"""
        return Ili2CCommandConfiguration()
