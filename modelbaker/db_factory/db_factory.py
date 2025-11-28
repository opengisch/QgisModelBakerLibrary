"""
Metadata:
    Creation Date: 2019-04-08
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

from ..dataobjects.fields import Field
from ..dbconnector.db_connector import DBConnector
from ..iliwrapper.ili2dbconfig import Ili2DbCommandConfiguration
from .db_command_config_manager import DbCommandConfigManager
from .layer_uri import LayerUri


class DbFactory(ABC):
    """Creates an entire set of objects so that modelbaker supports some database. This is an abstract class."""

    @abstractmethod
    def get_db_connector(self, uri: str, schema: Optional[str]) -> DBConnector:
        """Returns an instance of connector to database (:class:`DBConnector`).

        Args:
            schema (str): Database schema.
            uri (str): Database connection string.

        Returns:
            :class:`DBConnector`: A connector to specific database."""

    @abstractmethod
    def get_db_command_config_manager(
        self, configuration: Ili2DbCommandConfiguration
    ) -> DbCommandConfigManager:
        """Returns an instance of a database command config manager.

        Args:
            configuration (:class:`Ili2DbCommandConfiguration`): Configuration object that will be managed.

        Returns:
            Object that manages a configuration object to return specific information of some database."""

    @abstractmethod
    def get_layer_uri(self, uri: str) -> LayerUri:
        """Returns an instance of a layer uri.

        Args:
            uri (str): Database connection string.

        Returns:
            A object that provides layer uri."""

    @abstractmethod
    def pre_generate_project(
        self, configuration: Ili2DbCommandConfiguration
    ) -> tuple[bool, str]:
        """This method will be called before an operation of generate project is executed.

        Args:
            configuration (:class:`Ili2DbCommandConfiguration`): Configuration parameters with which will be executed the operation of generate project.

        Returns:
            *True* and an empty message if the called method was succeeded, *False* and a warning message otherwise."""

    @abstractmethod
    def post_generate_project_validations(
        self, configuration: Ili2DbCommandConfiguration, fallback_user: str = None
    ) -> tuple[bool, str]:
        """This method will be called after an operation of generate project is executed.

        Args:
            class: `Ili2DbCommandConfiguration` configuration: Configuration parameters with which were executed the operation of generate project.
            fallback_user (str): a username as fallback most possibly used when you want to pass your os account name to connect the database

        Returns:
            *True* and an empty message if the called method was succeeded, *False* and a warning message otherwise."""

    def get_specific_messages(self) -> dict[str, str]:
        """Returns specific words that will be used in warning and error messages."""
        messages = {"db_or_schema": "schema", "layers_source": "schema"}

        return messages

    def customize_widget_editor(self, field: Field, data_type: str) -> None:
        """Allows customizing the way a field is shown in the widget editor.

                For instance, a boolean field can be shown as a checkbox.

        Args:
            data_type: The type of field
            field (:class:`Field`): The field that will be customized"""
