"""
/***************************************************************************
                              -------------------
        begin                : 10.08.2021
        git sha              : :%H$
        copyright            : (C) 2021 by Dave Signer
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
import shutil
import tempfile

from qgis.testing import start_app, unittest

import modelbaker.utils.db_utils as db_utils
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import ilidataimporter_config, iliimporter_config, testdata_path

start_app()


class TestDatasetHandling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_import_and_mutation_postgis(self):
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

        # make mutations
        self.check_dataset_mutations(db_connector)

    def test_import_and_mutation_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, "tmp_basket_gpkg.gpkg"
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

        # make mutations
        self.check_dataset_mutations(db_connector)

    def test_import_and_mutation_mssql(self):

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

        # make mutations
        self.check_dataset_mutations(db_connector)

    def check_dataset_mutations(self, db_connector):
        # Create new dataset
        assert {
            record["datasetname"] for record in db_connector.get_datasets_info()
        } == {"Winti", "Seuzach"}
        result = db_connector.create_dataset("Glarus Nord")
        assert result[0]
        assert len(db_connector.get_datasets_info()) == 3
        assert len(db_connector.get_baskets_info()) == 4
        assert {
            record["datasetname"] for record in db_connector.get_datasets_info()
        } == {"Winti", "Seuzach", "Glarus Nord"}

        # Get tid of 'Glarus Nord'
        glarus_nord_tid = [
            record["t_id"]
            for record in db_connector.get_datasets_info()
            if record["datasetname"] == "Glarus Nord"
        ][0]

        # Get topics
        topics = db_connector.get_topics_info()
        assert len(topics) == 2

        # check the bid_domain
        count = 0
        for topic in topics:
            if topic["topic"] == "Infrastructure":
                assert topic["bid_domain"] == "INTERLIS.UUIDOID"
                count += 1
            if topic["topic"] == "Lines":
                assert topic["bid_domain"] == "INTERLIS.UUIDOID"
                count += 1
        assert count == 2

        # Generate the basket for 'Glarus Nord' and the first topic
        result = db_connector.create_basket(
            glarus_nord_tid, f"{topics[0]['model']}.{topics[0]['topic']}"
        )
        # Generate the basketsfor 'Glarus Nord' and the second topic
        result = db_connector.create_basket(
            glarus_nord_tid, f"{topics[1]['model']}.{topics[1]['topic']}"
        )
        assert len(db_connector.get_datasets_info()) == 3
        assert len(db_connector.get_baskets_info()) == 6

        # Rename dataset
        result = db_connector.rename_dataset(glarus_nord_tid, "Glarus West")
        assert len(db_connector.get_datasets_info()) == 3
        assert len(db_connector.get_baskets_info()) == 6
        assert {
            record["datasetname"] for record in db_connector.get_datasets_info()
        } == {"Winti", "Seuzach", "Glarus West"}

        # Edit basket for topic PipeBasketTest.Infrastructure and dataset Glarus West
        baskets_info = db_connector.get_baskets_info()
        for record in baskets_info:
            if (
                record["topic"] == "PipeBasketTest.Infrastructure"
                and record["datasetname"] == "Glarus West"
            ):
                basket_info = record
                break
        basket_t_id = basket_info["basket_t_id"]
        dataset_t_id = basket_info["dataset_t_id"]

        # Info to be set to existing basket
        basket_config = {
            "topic": "PipeBasketTest.Infrastructure",
            "basket_t_id": basket_t_id,
            "bid_value": "3aa70ca6-13c6-482f-a415-a59694cfd658",
            "attachmentkey": "my own attachment key",
            "dataset_t_id": dataset_t_id,
            "datasetname": "Glarus West",
        }
        res, msg = db_connector.edit_basket(basket_config)
        assert res, msg

        baskets_info = db_connector.get_baskets_info()
        assert len(baskets_info) == 6
        for record in baskets_info:
            if record["basket_t_id"] == basket_t_id:
                edited_basket_info = record
                break
        assert edited_basket_info["basket_t_id"] == basket_t_id
        assert edited_basket_info["dataset_t_id"] == dataset_t_id
        assert (
            edited_basket_info["basket_t_ili_tid"]
            == "3aa70ca6-13c6-482f-a415-a59694cfd658"
        )
        assert edited_basket_info["attachmentkey"] == "my own attachment key"
        assert edited_basket_info["datasetname"] == "Glarus West"
        assert edited_basket_info["topic"] == "PipeBasketTest.Infrastructure"

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
