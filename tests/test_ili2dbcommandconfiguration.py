"""
/***************************************************************************
                              -------------------
        begin                : 27.09.2024
        git sha              : :%H$
        copyright            : (C) 2024 by Germán Carrillo
        email                : german at opengis ch
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
from qgis.testing import start_app, unittest

from modelbaker.iliwrapper.ili2dbconfig import (
    BaseConfiguration,
    DeleteConfiguration,
    ExportConfiguration,
    Ili2DbCommandConfiguration,
    ImportDataConfiguration,
    SchemaImportConfiguration,
    UpdateDataConfiguration,
    ValidateConfiguration,
)

start_app()


class TestIli2DbCommandConfiguration(unittest.TestCase):
    GPKG_PATH = "/tmp/data.gpkg"
    MODELS_DIR = "/tmp/models/"

    def test_ili2db_command_configuration_from_an_other(self):
        base_config = BaseConfiguration()
        base_config.custom_model_directories_enabled = True
        base_config.custom_model_directories = self.MODELS_DIR

        configuration = Ili2DbCommandConfiguration()
        configuration.base_configuration = base_config
        configuration.dbfile = self.GPKG_PATH

        delete_config = DeleteConfiguration()
        assert delete_config.dbfile == ""

        delete_config = DeleteConfiguration(configuration)
        self.check_members(delete_config)

        import_config = ImportDataConfiguration(configuration)
        self.check_members(import_config)

        import_schema_config = SchemaImportConfiguration(configuration)
        self.check_members(import_schema_config)

        export_config = ExportConfiguration(configuration)
        self.check_members(export_config)

        update_config = UpdateDataConfiguration(configuration)
        self.check_members(update_config)

        validate_config = ValidateConfiguration(configuration)
        self.check_members(validate_config)

    def check_members(self, config):
        assert config.base_configuration.custom_model_directories_enabled == True
        assert config.base_configuration.custom_model_directories == self.MODELS_DIR
        assert config.dbfile == self.GPKG_PATH
