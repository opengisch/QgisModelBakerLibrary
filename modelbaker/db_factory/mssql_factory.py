"""
/***************************************************************************
    begin                :    10/05/19
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

from ..dataobjects.fields import Field
from ..dbconnector.mssql_connector import MssqlConnector
from .db_command_config_manager import Ili2DbCommandConfiguration
from .db_factory import DbFactory
from .mssql_command_config_manager import MssqlCommandConfigManager
from .mssql_layer_uri import MssqlLayerUri


class MssqlFactory(DbFactory):
    def get_db_connector(self, uri: str, schema: Optional[str]) -> MssqlConnector:
        return MssqlConnector(uri, schema)

    def get_db_command_config_manager(
        self, configuration: Ili2DbCommandConfiguration
    ) -> MssqlCommandConfigManager:
        return MssqlCommandConfigManager(configuration)

    def get_layer_uri(self, uri: str) -> MssqlLayerUri:
        return MssqlLayerUri(uri)

    def pre_generate_project(
        self, configuration: Ili2DbCommandConfiguration
    ) -> tuple[bool, str]:
        return True, ""

    def post_generate_project_validations(
        self, configuration: Ili2DbCommandConfiguration, fallback_user: str = None
    ) -> tuple[bool, str]:
        return True, ""

    def customize_widget_editor(self, field: Field, data_type: str) -> None:
        if "bit" in data_type:
            field.widget = "CheckBox"
            field.widget_config["CheckedState"] = "1"
            field.widget_config["UncheckedState"] = "0"
