"""
/***************************************************************************
                              -------------------
        begin                : 20/11/24
        git sha              : :%H$
        copyright            : (C) 2024 by Germán Carrillo
        email                : german@opengis.ch
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
from .ili2dbconfig import ExportMetaConfigConfiguration, Ili2DbCommandConfiguration
from .iliexecutable import IliExecutable


class MetaConfigExporter(IliExecutable):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.version = 4

    def _create_config(self) -> Ili2DbCommandConfiguration:
        return ExportMetaConfigConfiguration()

    def _get_ili2db_version(self):
        return self.version
