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

import datetime
import logging
import os
import shutil
import tempfile

from qgis.testing import start_app, unittest

import modelbaker.utils.db_utils as db_utils
from modelbaker.iliwrapper import ilideleter, iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import (
    ilidataimporter_config,
    ilideleter_config,
    iliimporter_config,
    testdata_path,
)

start_app()


class TestDelete(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_delete_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbschema = "any_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.dataset = "Winti"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Expected datasets and baskets
        db_connector = db_utils.get_db_connector(importer.configuration)

        # Basket handling is active
        assert db_connector.get_basket_handling()

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # One dataset is created (by schema import)
        assert len(db_connector.get_datasets_info()) == 1
        # Means we have two baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 2

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_seuzach.xtf"
        )
        dataImporter.configuration.dataset = "Seuzach"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # Two datasets are created (by schema import)
        assert len(db_connector.get_datasets_info()) == 2
        # Means we have four baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 4

        # Delete dataset
        datasetDeleter = ilideleter.Deleter()
        datasetDeleter.tool = DbIliMode.ili2pg
        datasetDeleter.configuration = ilideleter_config(importer.tool)
        datasetDeleter.configuration.dbschema = importer.configuration.dbschema
        datasetDeleter.configuration.dataset = "Winti"
        datasetDeleter.stdout.connect(self.print_info)
        datasetDeleter.stderr.connect(self.print_error)
        assert datasetDeleter.run() == ilideleter.Deleter.SUCCESS

        # One remaining dataset
        datasets_info = db_connector.get_datasets_info()
        assert len(db_connector.get_datasets_info()) == 1
        # Means only two remaining baskets
        assert len(db_connector.get_baskets_info()) == 2

        # Check existent dataset name
        assert datasets_info[0]["datasetname"] == "Seuzach"

    def test_delete_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, "tmp_delete_dataset_gpkg.gpkg"
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.dataset = "Winti"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Expected datasets and baskets
        db_connector = db_utils.get_db_connector(importer.configuration)

        # Basket handling is active
        assert db_connector.get_basket_handling()

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # One dataset is created (by schema import)
        assert len(db_connector.get_datasets_info()) == 1
        # Means we have two baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 2

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_seuzach.xtf"
        )
        dataImporter.configuration.dataset = "Seuzach"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # Two datasets are created (by schema import)
        assert len(db_connector.get_datasets_info()) == 2
        # Means we have four baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 4

        # Delete dataset
        datasetDeleter = ilideleter.Deleter()
        datasetDeleter.tool = DbIliMode.ili2gpkg
        datasetDeleter.configuration = ilideleter_config(importer.tool)
        datasetDeleter.configuration.dbfile = importer.configuration.dbfile
        datasetDeleter.configuration.dataset = "Winti"
        datasetDeleter.stdout.connect(self.print_info)
        datasetDeleter.stderr.connect(self.print_error)
        assert datasetDeleter.run() == ilideleter.Deleter.SUCCESS

        # One remaining dataset
        datasets_info = db_connector.get_datasets_info()
        assert len(db_connector.get_datasets_info()) == 1
        # Means only two remaining baskets
        assert len(db_connector.get_baskets_info()) == 2

        # Check existent dataset name
        assert datasets_info[0]["datasetname"] == "Seuzach"

    def _test_delete_mssql(self):

        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbschema = "baskets_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_winti.xtf"
        )
        dataImporter.configuration.dataset = "Winti"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Expected datasets and baskets
        db_connector = db_utils.get_db_connector(importer.configuration)

        # Basket handling is active
        assert db_connector.get_basket_handling()

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # One dataset is created (by schema import)
        assert len(db_connector.get_datasets_info()) == 1
        # Means we have two baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 2

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(importer.tool)
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_pipebaskettest_v1_seuzach.xtf"
        )
        dataImporter.configuration.dataset = "Seuzach"
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Two topics are created (by schema import)
        assert len(db_connector.get_topics_info()) == 2
        # One dataset is created (by schema import)
        assert len(db_connector.get_datasets_info()) == 2
        # Means we have two baskets created (by schema import)
        assert len(db_connector.get_baskets_info()) == 4

        # Delete dataset
        datasetDeleter = ilideleter.Deleter()
        datasetDeleter.tool = DbIliMode.ili2mssql
        datasetDeleter.configuration = ilideleter_config(importer.tool)
        datasetDeleter.configuration.dbschema = importer.configuration.dbschema
        datasetDeleter.configuration.dataset = "Winti"
        datasetDeleter.stdout.connect(self.print_info)
        datasetDeleter.stderr.connect(self.print_error)
        assert datasetDeleter.run() == ilideleter.Deleter.SUCCESS

        # One remaining dataset
        datasets_info = db_connector.get_datasets_info()
        assert len(db_connector.get_datasets_info()) == 1
        # Means only two remaining baskets
        assert len(db_connector.get_baskets_info()) == 2

        # Check existent dataset name
        assert datasets_info[0]["datasetname"] == "Seuzach"

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
