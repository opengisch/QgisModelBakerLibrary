"""
/***************************************************************************
                              -------------------
        begin                : 07.03.2022
        git sha              : :%H$
        copyright            : (C) 2022 by Matthias Kuhn
        email                : david@opengis.ch
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
from enum import Enum


class DbActionType(Enum):
    """Defines constants for generate, schema_import, import data, or export actions of modelbaker."""

    GENERATE = 1
    IMPORT_DATA = 2
    EXPORT = 3
    SCHEMA_IMPORT = 4


class OptimizeStrategy(Enum):
    """Defines the strategy that should be used for extended models."""

    NONE = 0
    GROUP = 1
    HIDE = 2
