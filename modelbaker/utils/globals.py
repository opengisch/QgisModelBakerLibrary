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
from enum import Enum, IntEnum


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


class LogLevel(IntEnum):
    INFO = 0
    WARNING = 1
    FAIL = 2
    SUCCESS = 3
    TOPPING = 4


def default_log_function(text, level=LogLevel.INFO, silent=False):
    if silent:
        return
    if level == LogLevel.INFO:
        print(f"INFO    : {text}")
    if level == LogLevel.WARNING:
        print(f"WARNING : {text}")
    if level == LogLevel.FAIL:
        print(f"FAIL    : {text}")
    if level == LogLevel.SUCCESS:
        print(f"SUCCESS : {text}")
    if level == LogLevel.TOPPING:
        print(f"TOPPING : {text}")
