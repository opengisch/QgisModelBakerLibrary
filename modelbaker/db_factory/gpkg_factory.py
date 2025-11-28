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

from typing import Optional

from ..dbconnector.gpkg_connector import GPKGConnector
from .db_command_config_manager import Ili2DbCommandConfiguration
from .db_factory import DbFactory
from .gpkg_command_config_manager import GpkgCommandConfigManager
from .gpkg_layer_uri import GpkgLayerUri


class GpkgFactory(DbFactory):
    """Creates an entire set of objects so that QgisMmodelbakerodelBaker supports Geopackage database."""

    def get_db_connector(self, uri: str, schema: Optional[str]) -> GPKGConnector:
        return GPKGConnector(uri, None)

    def get_db_command_config_manager(
        self, configuration: Ili2DbCommandConfiguration
    ) -> GpkgCommandConfigManager:
        return GpkgCommandConfigManager(configuration)

    def get_layer_uri(self, uri: str) -> GpkgLayerUri:
        return GpkgLayerUri(uri)

    def pre_generate_project(
        self, configuration: Ili2DbCommandConfiguration
    ) -> tuple[bool, str]:
        return True, ""

    def post_generate_project_validations(
        self,
        configuration: Ili2DbCommandConfiguration,
        fallback_user: Optional[str] = None,
    ) -> tuple[bool, str]:
        return True, ""

    def get_specific_messages(self) -> dict[str, str]:
        messages = {"db_or_schema": "database", "layers_source": "GeoPackage"}

        return messages
