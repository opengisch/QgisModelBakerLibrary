"""
Metadata:
    Creation Date: 2019-05-10
    Copyright: (C) 2019 by Yesid Polania
    Contact: yesidpol.3@gmail.com

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
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
        """
        Description to do

        Args:
            uri (str): Description to do.
            schema (Optional[str]): Description to do.

        Returns:
            MssqlConnector: Description to do.
        """

        return MssqlConnector(uri, schema)

    def get_db_command_config_manager(
        self, configuration: Ili2DbCommandConfiguration
    ) -> MssqlCommandConfigManager:
        """
        Description to do

        Args:
            configuration (Ili2DbCommandConfiguration): Description to do.

        Returns:
            MssqlCommandConfigManager: Description to do.
        """

        return MssqlCommandConfigManager(configuration)

    def get_layer_uri(self, uri: str) -> MssqlLayerUri:
        """
        Description to do

        Args:
            uri (str): Description to do.

        Returns:
            MssqlLayerUri: Description to do.
        """

        return MssqlLayerUri(uri)

    def pre_generate_project(
        self, configuration: Ili2DbCommandConfiguration
    ) -> tuple[bool, str]:
        """
        Description to do

        Args:
            configuration (Ili2DbCommandConfiguration): Description to do.

        Returns:
            tuple[bool, str]: Description to do.
        """

        return True, ""

    def post_generate_project_validations(
        self, configuration: Ili2DbCommandConfiguration, fallback_user: str = None
    ) -> tuple[bool, str]:
        """
        Description to do

        Args:
            configuration (Ili2DbCommandConfiguration): Description to do.
            fallback_user (str): Description to do.

        Returns:
            tuple[bool, str]: Description to do.
        """

        return True, ""

    def customize_widget_editor(self, field: Field, data_type: str) -> None:
        """
        Description to do

        Args:
            field (Field): Description to do.
            data_type (str): Description to do.

        Returns:
            None: Description to do.
        """

        if "bit" in data_type:
            field.widget = "CheckBox"
            field.widget_config["CheckedState"] = "1"
            field.widget_config["UncheckedState"] = "0"
