"""
/***************************************************************************
                              -------------------
        begin                : 2022-07-17
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
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
import configparser
from pathlib import Path


class Ili2dbSettings(dict):
    """
    Class keeping settings to be performed on ili2db.
    As well as the files like pre-/postscript and metaattributefile (TOML/INI).

    With the method parse_parameter_from_db we can fill it up according to a existing database schema (passing the specific extension of DBConnector).
    """

    def __init__(self):
        self.parameters = {}
        self.metaattr_path = None
        self.postscript_path = None
        self.prescript_path = None
        self.models = []

    def parse_parameters_from_ini_file(self, ini_file: str) -> bool:
        p = Path(ini_file)
        if p.exists():
            config = configparser.ConfigParser()
            config.optionxform = str  # To preserve case
            config.read(ini_file)
            if not "CONFIGURATION" in config or not "ch.ehi.ili2db" in config:
                return False

            def parse_boolean(v):
                return True if v == "true" else (False if v == "false" else v)

            params = dict(config["ch.ehi.ili2db"])
            self.parameters = {k: parse_boolean(v) for k, v in params.items()}
            return True

        return False
