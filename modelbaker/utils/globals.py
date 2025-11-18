"""
Metadata:
    Creation Date: 2022-03-07
    Copyright: (C) 2022 by Matthias Kuhn
    Contact: david@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""

from enum import Enum, IntEnum

MODELS_BLACKLIST = [
    "CHBaseEx_MapCatalogue_V1",
    "CHBaseEx_WaterNet_V1",
    "CHBaseEx_Sewage_V1",
    "CHAdminCodes_V1",
    "AdministrativeUnits_V1",
    "AdministrativeUnitsCH_V1",
    "WithOneState_V1",
    "WithLatestModification_V1",
    "WithModificationObjects_V1",
    "GraphicCHLV03_V1",
    "GraphicCHLV95_V1",
    "NonVector_Base_V2",
    "NonVector_Base_V3",
    "NonVector_Base_LV03_V3_1",
    "NonVector_Base_LV95_V3_1",
    "GeometryCHLV03_V1",
    "GeometryCHLV95_V1",
    "Geometry_V1",
    "InternationalCodes_V1",
    "Localisation_V1",
    "LocalisationCH_V1",
    "Dictionaries_V1",
    "DictionariesCH_V1",
    "CatalogueObjects_V1",
    "CatalogueObjectTrees_V1",
    "AbstractSymbology",
    "CodeISO",
    "CoordSys",
    "GM03_2_1Comprehensive",
    "GM03_2_1Core",
    "GM03_2Comprehensive",
    "GM03_2Core",
    "GM03Comprehensive",
    "GM03Core",
    "IliRepository09",
    "IliSite09",
    "IlisMeta07",
    "IliVErrors",
    "INTERLIS_ext",
    "RoadsExdm2ben",
    "RoadsExdm2ben_10",
    "RoadsExgm2ien",
    "RoadsExgm2ien_10",
    "StandardSymbology",
    "StandardSymbology",
    "Time",
    "Units",
    "",
    "CHAdminCodes_V2",
    "AdministrativeUnits_V2",
    "AdministrativeUnitsCH_V2",
    "WithOneState_V2",
    "WithLatestModification_V2",
    "WithModificationObjects_V2",
    "GraphicCHLV03_V2",
    "GraphicCHLV95_V2",
    "GeometryCHLV03_V2",
    "GeometryCHLV95_V2",
    "Geometry_V2",
    "InternationalCodes_V2",
    "Localisation_V2",
    "LocalisationCH_V2",
    "Dictionaries_V2",
    "DictionariesCH_V2",
    "CatalogueObjects_V2",
    "CatalogueObjectTrees_V2",
]


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
