"""
/***************************************************************************
                              -------------------
        begin                : 28.10.2024
        git sha              : :%H$
        copyright            : (C) 2024 by Dave Signer
        email                : david@opengis.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import datetime
import logging
import os
import pathlib
import tempfile

from osgeo import gdal
from qgis.core import QgsProject
from qgis.testing import start_app, unittest

import modelbaker.utils.db_utils as db_utils
from modelbaker.dataobjects.project import Project
from modelbaker.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import iliimporter_config, testdata_path

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestMultipleGeometriesPerTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_multiple_geom_geopackage(self):
        """
        Checks when the gdal version is sufficient (means >=3.8) if tables are created with multiple geometries and the correct layers are generated.
        This of course depends with what gdal version the current images are built.
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/MultipleGeom.ili")
        importer.configuration.ilimodels = "MultipleGeom"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_multiple_geom_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True

        # create it when there's a sufficient gdal version
        importer.configuration.create_gpkg_multigeom = self._sufficient_gdal()

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # check geometry table
        # check if there are multiple geometry columns of the same table
        db_connector = db_utils.get_db_connector(importer.configuration)
        tables_with_multiple_geometries = db_connector.multiple_geometry_tables()

        # should have multiple when having a sufficient gdal and otherwise not
        if self._sufficient_gdal():
            assert len(tables_with_multiple_geometries) > 0
        else:
            assert len(tables_with_multiple_geometries) == 0

        # create project
        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            consider_basket_handling=True,
        )

        project = Project()

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        tree_layers = root.findLayers()
        assert len(tree_layers) == 7

        {layer.name() for layer in tree_layers}
        expected_layer_names_with_multigeometry = {
            "NoGeomClass",
            "POI",
            "GOI (Point)",
            "T_ILI2DB_BASKET",
            "T_ILI2DB_DATASET",
            "GOI (Line)",
            "GOI (Surface)",
        }
        expected_layer_names_without_multigeometry = {
            "NoGeomClass",
            "GOI",
            "POI",
            "GOI (Line)",
            "GOI (Surface)",
            "T_ILI2DB_BASKET",
            "T_ILI2DB_DATASET",
        }

        if self._sufficient_gdal():
            assert {
                layer.name() for layer in tree_layers
            } == expected_layer_names_with_multigeometry
        else:
            assert {
                layer.name() for layer in tree_layers
            } == expected_layer_names_without_multigeometry

    def _sufficient_gdal(self):
        return bool(int(gdal.VersionInfo("VERSION_NUM")) >= 3080000)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()
        QgsProject.instance().clear()
