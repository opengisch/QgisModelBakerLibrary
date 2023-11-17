"""
/***************************************************************************
                              -------------------
        begin                : 10.11.2023
        git sha              : :%H$
        copyright            : (C) 2023 by Dave Signer
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

import datetime
import logging
import os
import tempfile

from qgis.testing import start_app, unittest

import modelbaker.utils.db_utils as db_utils
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import ilidataimporter_config, iliimporter_config, testdata_path

start_app()


class TestSequenceReset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_reset_seq_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "road_simple{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        db_connector = db_utils.get_db_connector(importer.configuration)

        assert db_connector.get_ili2db_sequence_value() == 8

        success, _ = db_connector.set_ili2db_sequence_value(2000)
        assert success

        # Import 31 entries
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.dataset = "Baseset"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        assert db_connector.get_ili2db_sequence_value() == 2032  # entries + basket

        success, _ = db_connector.set_ili2db_sequence_value(1000)
        assert success

        assert db_connector.get_ili2db_sequence_value() == 1000

    def test_reset_seq_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_roads_simple_resetseq_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        db_connector = db_utils.get_db_connector(importer.configuration)

        # not exiting yet, so it's none
        assert db_connector.get_ili2db_sequence_value() == None
        success, _ = db_connector.set_ili2db_sequence_value(2000)
        assert success

        # Import 31 entries
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.dataset = "Baseset"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        assert db_connector.get_ili2db_sequence_value() == 2042

        success, _ = db_connector.set_ili2db_sequence_value(1000)
        assert success

        assert db_connector.get_ili2db_sequence_value() == 1000

    def test_reset_seq_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        db_connector = db_utils.get_db_connector(importer.configuration)

        # not sure what mssql produces but in the end it's 9
        assert db_connector.get_ili2db_sequence_value() == 9
        success, _ = db_connector.set_ili2db_sequence_value(2000)
        assert success

        # Import 31 entries
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.dataset = "Baseset"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        assert db_connector.get_ili2db_sequence_value() == 2033

        success, _ = db_connector.set_ili2db_sequence_value(1000)
        assert success

        assert db_connector.get_ili2db_sequence_value() == 1000

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)
