"""
/***************************************************************************
    begin                :    08/04/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
    email                :    yesidpol.3@gmail.com
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
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import QCoreApplication

from ..dbconnector.db_connector import DBConnectorError
from ..dbconnector.pg_connector import PGConnector
from .db_command_config_manager import Ili2DbCommandConfiguration
from .db_factory import DbFactory
from .pg_command_config_manager import PgCommandConfigManager
from .pg_layer_uri import PgLayerUri


class PgFactory(DbFactory):
    """Creates an entire set of objects so that modelbaker supports Postgres/Postgis database."""

    def get_db_connector(self, uri: str, schema: Optional[str]) -> PGConnector:
        return PGConnector(uri, schema)

    def get_db_command_config_manager(
        self, configuration: Ili2DbCommandConfiguration
    ) -> PgCommandConfigManager:
        return PgCommandConfigManager(configuration)

    def get_layer_uri(self, uri: str) -> PgLayerUri:
        return PgLayerUri(uri)

    def pre_generate_project(
        self, configuration: Ili2DbCommandConfiguration
    ) -> tuple[bool, str]:
        result = not configuration.db_use_super_login
        message = ""

        if configuration.db_use_super_login:
            try:
                config_manager = self.get_db_command_config_manager(configuration)
                uri = config_manager.get_uri(True)

                _db_connector = self.get_db_connector(uri, configuration.dbschema)

                result = schema_exist = _db_connector.db_or_schema_exists()

                if not schema_exist:
                    _db_connector.create_db_or_schema(configuration.dbusr)
                    result = True

            except (DBConnectorError, FileNotFoundError) as e:
                message = QCoreApplication.translate(
                    "PgFactory",
                    "There was an error generating schema with superuser. Check superuser login parameters from settings > General.\n\nReason:\n\n{}",
                ).format(str(e))

        return result, message

    def post_generate_project_validations(
        self, configuration: Ili2DbCommandConfiguration, fallback_user: str = None
    ) -> tuple[bool, str]:
        result = False
        message = ""

        config_manager = self.get_db_command_config_manager(configuration)
        uri = config_manager.get_uri(
            su=configuration.db_use_super_login, fallback_user=fallback_user
        )

        connector = self.get_db_connector(uri, configuration.dbschema)

        if not connector._postgis_exists():
            message = QCoreApplication.translate(
                "PgFactory",
                "The current database does not have PostGIS installed! Please install it by running `CREATE EXTENSION postgis;` on the database before proceeding.",
            )
        else:
            result = True

        return result, message
