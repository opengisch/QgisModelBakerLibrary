"""
Metadata:
    Creation Date: 2019-05-13
    Copyright: (C) 2019 by Yesid Polania
    Contact: yesidpol.3@gmail.com

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
    SchemaImportConfiguration,
)


class DbCommandConfigManager(ABC):
    """Manages a configuration object to return specific information of some database. This is a abstract class.

    Provides database uri, arguments to ili2db and a way to save and load configurations parameters
    based on a object configuration.
    """

    def __init__(self, configuration: Ili2DbCommandConfiguration) -> None:
        self.configuration = configuration

    @abstractmethod
    def get_uri(
        self, su: bool = False, qgis: bool = False, fallback_user: Optional[str] = None
    ) -> str:
        """Gets database uri (connection string) for db connectors (DBConnector).

        Args:
            su (bool): *True* to use super user credentials, *False* otherwise.
            qgis (bool): *True* to use qgis specific credentials (e.g. authcfg), *False* otherwise.
            fallback_user (str): a username as fallback most possibly used when you want to pass your os account name to connect the database

        Returns:
            str: Database uri (connection string)."""

    @abstractmethod
    def get_db_args(self, hide_password: bool = False, su: bool = False) -> list[str]:
        """Gets a list of ili2db arguments related to database.

        Args:
            hide_password (bool): *True* to mask the password, *False* otherwise.
            su (bool): *True* to use super user password, *False* otherwise. Default is False.

        Returns:
            list: ili2db arguments list."""

    def get_schema_import_args(self) -> list[str]:
        """Gets a list of ili2db arguments to use in operation schema import.

        Returns:
            list: ili2db arguments list."""
        return list()

    def get_ili2db_args(self, hide_password: bool = False) -> list[str]:
        """Gets a complete list of ili2db arguments in order to execute the app.

        Args:
            hide_password (bool): *True* to mask the password, *False* otherwise.

        Returns:
            list: ili2db arguments list."""
        db_args = self.get_db_args(hide_password, self.configuration.db_use_super_login)

        if type(self.configuration) is SchemaImportConfiguration:
            db_args += self.get_schema_import_args()

        ili2dbargs = self.configuration.to_ili2db_args(db_args)

        return ili2dbargs

    @abstractmethod
    def save_config_in_qsettings(self) -> None:
        """Saves configuration values related to database in QSettings."""

    @abstractmethod
    def load_config_from_qsettings(self) -> None:
        """Loads configuration values related to database from Qsettings."""
