"""
/***************************************************************************
    begin                :    27/09/2025
    git sha              :    :%H$
    copyright            :    (C) 2025 by Dave Signer
    email                :    david@opengis.ch
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

from qgis.core import QgsProcessingContext, QgsProcessingFeedback
from qgis.testing import start_app, unittest

from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.processing.ili2db_exporting import ExportingGPKGAlgorithm
from modelbaker.processing.ili2db_importing import ImportingGPKGAlgorithm
from modelbaker.processing.ili2db_validating import ValidatingGPKGAlgorithm
from tests.utils import iliimporter_config, testdata_path

start_app()


class TestProcessingAlgorithms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def iliimporter_pg_config_params(self):
        configuration = iliimporter_config(DbIliMode.ili2pg)
        params = {
            "HOST": configuration.dbhost,
            "DBNAME": configuration.database,
            "USERNAME": configuration.dbusr,
            "PASSWORD": configuration.dbpwd,
        }
        return params

    def gpkg_file(self, basket_col):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_roads_simple_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.create_basket_col = basket_col
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        return importer.configuration.dbfile

    def pg_schema(self, basket_col):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = basket_col
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        return importer.configuration.dbschema

    def test_algs_gpkg_with_baskets(self):

        conn_parameters = {}
        conn_parameters["DBPATH"] = self.gpkg_file(True)

        # validate empty file without specific parameters
        validation_parameters = {}
        validation_parameters.update(conn_parameters)
        alg = ValidatingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(validation_parameters, context, feedback)
        assert output["ISVALID"]

        # import valid data now to a dataset called 'validdata'
        import_parameters = {
            "XTFFILEPATH": testdata_path("xtf/test_roads_simple.xtf"),
            "DATASET": "validdata",
        }
        import_parameters.update(conn_parameters)
        alg = ImportingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(import_parameters, context, feedback)
        assert output["ISVALID"]

        # import invalid data now to a dataset called 'invaliddata'
        import_parameters = {
            "XTFFILEPATH": testdata_path("xtf/test_roads_simple_invalid.xtf"),
            "DATASET": "invaliddata",
        }
        import_parameters.update(conn_parameters)
        alg = ImportingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(import_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # import invalid data now to a dataset called 'invaliddata'
        # this time we disable the validation
        import_parameters = {
            "XTFFILEPATH": testdata_path("xtf/test_roads_simple_invalid.xtf"),
            "DATASET": "invaliddata",
            "DISABLEVALIDATION": True,
        }
        import_parameters.update(conn_parameters)
        alg = ImportingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(import_parameters, context, feedback)
        assert output["ISVALID"]

        # validate without specific parameters
        validation_parameters = {}
        validation_parameters.update(conn_parameters)
        alg = ValidatingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(validation_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # validate again only the dataset 'validdata'
        validation_parameters = {"FILTER": "Dataset", "FILTERS": "validdata"}
        validation_parameters.update(conn_parameters)
        alg = ValidatingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(validation_parameters, context, feedback)
        assert output["ISVALID"]

        valid_targetfile = os.path.join(self.basetestpath, "valid_export.xtf")
        invalid_targetfile = os.path.join(self.basetestpath, "valid_export.xtf")

        # let's export without specific parameters
        export_parameters = {"XTFFILEPATH": valid_targetfile}
        export_parameters.update(conn_parameters)
        alg = ExportingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # let's export again only the dataset 'validdata'
        export_parameters = {
            "XTFFILEPATH": valid_targetfile,
            "FILTER": "Dataset",
            "FILTERS": "validdata",
        }
        export_parameters.update(conn_parameters)
        alg = ExportingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # let's export the invalid dataset 'invaliddata'
        export_parameters = {
            "XTFFILEPATH": invalid_targetfile,
            "FILTER": "Dataset",
            "FILTERS": "invaliddata",
        }
        export_parameters.update(conn_parameters)
        alg = ExportingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # let's export the invalid dataset 'invaliddata' and disable validation
        export_parameters = {
            "XTFFILEPATH": invalid_targetfile,
            "FILTER": "Dataset",
            "FILTERS": "invaliddata",
            "DISABLEVALIDATION": True,
        }
        export_parameters.update(conn_parameters)
        alg = ExportingGPKGAlgorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        assert output["ISVALID"]

        assert os.path.isfile(valid_targetfile)
        assert os.path.isfile(invalid_targetfile)

    def test_validating_alg_pg(self):
        parameters = self.iliimporter_pg_config_params()
        parameters["SCHEMA"] = self.pg_schema(False)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)
