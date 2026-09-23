"""
Metadata:
    Creation Date: 2025-10-10
    Copyright: (C) 2025 by Dave Signer
    Contact: david@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""

import datetime
import logging
import os
import tempfile

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProviderRegistry,
)
from qgis.testing import start_app, unittest

from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.processing.ili2db_exporting import (
    ExportingGPKGAlgorithm,
    ExportingPGAlgorithm,
)
from modelbaker.processing.ili2db_importing import (
    ImportingGPKGAlgorithm,
    ImportingPGAlgorithm,
)
from modelbaker.processing.ili2db_schema_importing import (
    SchemaImportingGPKGAlgorithm,
    SchemaImportingPGAlgorithm,
)
from modelbaker.processing.ili2db_validating import (
    ValidatingGPKGAlgorithm,
    ValidatingPGAlgorithm,
)
from modelbaker.processing.util_dataconnectionparsing import (
    DataConnectionParsingGPKGAlgorithm,
    DataConnectionParsingPGAlgorithm,
)
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
            "USER": configuration.dbusr,
            "PASSWORD": configuration.dbpwd,
        }
        return params

    def schema_import_alg_test(
        self, tool: DbIliMode, parameters: dict, expected_result: bool
    ):
        alg = (
            SchemaImportingGPKGAlgorithm()
            if tool == DbIliMode.ili2gpkg
            else SchemaImportingPGAlgorithm()
        )
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(parameters, context, feedback)
        assert output["ISVALID"] == expected_result

    def gpkg_file(self, basket_col):
        dbfile = os.path.join(
            self.basetestpath,
            "tmp_roads_simple_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        schema_import_parameters = {  # smart2 by default
            "CRS": QgsCoordinateReferenceSystem("EPSG:2056"),
            "BASKETCOL": basket_col,
            "MODELS": "RoadsSimple",
            "ILIFILE": testdata_path("ilimodels/RoadsSimple.ili"),
            "DBPATH": dbfile,
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, schema_import_parameters, True)
        return dbfile

    def pg_schema(self, basket_col):
        dbschema = "roads_simple_{:%Y%m%d%H%M%S%f}".format(datetime.datetime.now())
        schema_import_parameters = {  # smart2 by default
            "CRS": QgsCoordinateReferenceSystem("EPSG:2056"),
            "BASKETCOL": basket_col,
            "MODELS": "RoadsSimple",
            "ILIFILE": testdata_path("ilimodels/RoadsSimple.ili"),
            "SCHEMA": dbschema,
        }
        schema_import_parameters.update(self.iliimporter_pg_config_params())
        self.schema_import_alg_test(DbIliMode.ili2pg, schema_import_parameters, True)
        return dbschema

    def test_schema_import(self):
        def params_gpkg(base):
            params = base.copy()
            params["DBPATH"] = os.path.join(
                self.basetestpath,
                "tmp_roads_simple_{:%Y%m%d%H%M%S%f}.gpkg".format(
                    datetime.datetime.now()
                ),
            )
            return params

        def params_pg(base):
            params = base.copy()
            params["SCHEMA"] = dbschema = "roads_simple_{:%Y%m%d%H%M%S%f}".format(
                datetime.datetime.now()
            )
            params.update(self.iliimporter_pg_config_params())
            return params

        base_params = {  # Only mandatory params, should succeed
            "MODELS": "RoadsSimple",
            "ILIFILE": testdata_path("ilimodels/RoadsSimple.ili"),
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), True)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), True)

        base_params = {  # smart1
            "INHERITANCE": "smart1",
            "MODELS": "RoadsSimple",
            "ILIFILE": testdata_path("ilimodels/RoadsSimple.ili"),
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), True)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), True)

        base_params = {  # nosmart
            "INHERITANCE": "nosmart",
            "MODELS": "RoadsSimple",
            "ILIFILE": testdata_path("ilimodels/RoadsSimple.ili"),
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), True)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), True)

        base_params = {  # No models, ilifile's implicit model
            "ILIFILE": testdata_path("ilimodels/RoadsSimple.ili"),
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), True)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), True)

        base_params = {  # Models with no ilifile
            "MODELS": "RoadsSimple",
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), False)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), False)

        base_params = {}  # Missing both models and ilifile
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), False)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), False)

        base_params = {  # Model requires basket column
            "BASKETCOL": False,
            "ILIFILE": testdata_path("ilimodels/PlansDAffectation_V1_2.ili"),
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), False)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), False)

        base_params = {  # Model translation, with basket column
            "BASKETCOL": True,
            "ILIFILE": testdata_path("ilimodels/PlansDAffectation_V1_2.ili"),
            "LANGUAGE": "fr",
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), True)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), True)

        base_params = {  # Import several models
            "MODELS": "CIAF_LADM;another",
            "ILIFILE": testdata_path("ilimodels/CIAF_LADM/CIAF_LADM.ili"),
        }
        self.schema_import_alg_test(DbIliMode.ili2gpkg, params_gpkg(base_params), True)
        self.schema_import_alg_test(DbIliMode.ili2pg, params_pg(base_params), True)

    def test_algs_gpkg(self):
        conn_parameters_baskets = {}
        conn_parameters_baskets["DBPATH"] = self.gpkg_file(True)
        self._algs_with_baskets(
            conn_parameters_baskets,
            ImportingGPKGAlgorithm,
            ValidatingGPKGAlgorithm,
            ExportingGPKGAlgorithm,
        )
        conn_parameters = {}
        conn_parameters["DBPATH"] = self.gpkg_file(False)
        self._algs_without_baskets(
            conn_parameters,
            ImportingGPKGAlgorithm,
            ValidatingGPKGAlgorithm,
            ExportingGPKGAlgorithm,
        )

    def test_algs_pg(self):
        conn_parameters_baskets = self.iliimporter_pg_config_params()
        conn_parameters_baskets["SCHEMA"] = self.pg_schema(True)
        self._algs_with_baskets(
            conn_parameters_baskets,
            ImportingPGAlgorithm,
            ValidatingPGAlgorithm,
            ExportingPGAlgorithm,
        )
        conn_parameters = self.iliimporter_pg_config_params()
        conn_parameters["SCHEMA"] = self.pg_schema(False)
        self._algs_without_baskets(
            conn_parameters,
            ImportingPGAlgorithm,
            ValidatingPGAlgorithm,
            ExportingPGAlgorithm,
        )

    def _algs_with_baskets(
        self,
        conn_parameters,
        importing_algorithm,
        validating_algorithm,
        exporting_algorithm,
    ):
        # import valid data now to a dataset called 'validdata'
        import_parameters = {
            "XTFFILEPATH": testdata_path("xtf/test_roads_simple.xtf"),
            "DATASET": "validdata",
        }
        import_parameters.update(conn_parameters)
        alg = importing_algorithm()
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
        alg = importing_algorithm()
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
        alg = importing_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(import_parameters, context, feedback)
        assert output["ISVALID"]

        # validate without specific parameters
        validation_parameters = {}
        validation_parameters.update(conn_parameters)
        alg = validating_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(validation_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # validate again only the dataset 'validdata'
        validation_parameters = {"FILTERMODE": "Datasets", "FILTER": "validdata"}
        validation_parameters.update(conn_parameters)
        alg = validating_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(validation_parameters, context, feedback)
        assert output["ISVALID"]

        valid_targetfile = os.path.join(self.basetestpath, "valid_export.xtf")
        invalid_targetfile = os.path.join(self.basetestpath, "invalid_export.xtf")

        # let's export without specific parameters
        export_parameters = {"XTFFILEPATH": valid_targetfile}
        export_parameters.update(conn_parameters)
        alg = exporting_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # let's export again only the dataset 'validdata'
        export_parameters = {
            "XTFFILEPATH": valid_targetfile,
            "FILTERMODE": "Datasets",
            "FILTER": "validdata",
        }
        export_parameters.update(conn_parameters)
        alg = exporting_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        assert output["ISVALID"]

        # let's export the invalid dataset 'invaliddata'
        export_parameters = {
            "XTFFILEPATH": invalid_targetfile,
            "FILTERMODE": "Datasets",
            "FILTER": "invaliddata",
        }
        export_parameters.update(conn_parameters)
        alg = exporting_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # let's export the invalid dataset 'invaliddata' and disable validation
        export_parameters = {
            "XTFFILEPATH": invalid_targetfile,
            "FILTERMODE": "Datasets",
            "FILTER": "invaliddata",
            "DISABLEVALIDATION": True,
        }
        export_parameters.update(conn_parameters)
        alg = exporting_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        assert output["ISVALID"]

        assert os.path.isfile(valid_targetfile)
        assert os.path.isfile(invalid_targetfile)

    def _algs_without_baskets(
        self,
        conn_parameters,
        importing_algorithm,
        validating_algorithm,
        exporting_algorithm,
    ):
        # import valid data now
        import_parameters = {"XTFFILEPATH": testdata_path("xtf/test_roads_simple.xtf")}
        import_parameters.update(conn_parameters)
        alg = importing_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(import_parameters, context, feedback)
        assert output["ISVALID"]

        # validate without specific parameters
        validation_parameters = {}
        validation_parameters.update(conn_parameters)
        alg = validating_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(validation_parameters, context, feedback)
        assert output["ISVALID"]

        # import invalid data now
        import_parameters = {
            "XTFFILEPATH": testdata_path("xtf/test_roads_simple_invalid.xtf")
        }
        import_parameters.update(conn_parameters)
        alg = importing_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(import_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # import invalid data again
        # this time we disable the validation
        import_parameters = {
            "XTFFILEPATH": testdata_path("xtf/test_roads_simple_invalid.xtf"),
            "DISABLEVALIDATION": True,
        }
        import_parameters.update(conn_parameters)
        alg = importing_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(import_parameters, context, feedback)
        assert output["ISVALID"]

        # validate without specific parameters
        validation_parameters = {}
        validation_parameters.update(conn_parameters)
        alg = validating_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(validation_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        invalid_targetfile = os.path.join(self.basetestpath, "invalid_export.xtf")

        # let's export without specific parameters
        export_parameters = {"XTFFILEPATH": invalid_targetfile}
        export_parameters.update(conn_parameters)
        alg = exporting_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        # fails
        assert not output["ISVALID"]

        # let's export and disable validation
        export_parameters = {
            "XTFFILEPATH": invalid_targetfile,
            "DISABLEVALIDATION": True,
        }
        export_parameters.update(conn_parameters)
        alg = exporting_algorithm()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(export_parameters, context, feedback)
        assert output["ISVALID"]

        assert os.path.isfile(invalid_targetfile)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)


class TestProcessingUtilAlgorithms(unittest.TestCase):

    PG_CONNECTIONS = {
        "pg-one": {
            "uri": "host=localhost1 port=54321 dbname=db1 user=flintheart password=glomgold sslmode=prefer",
            "config": {"savePassword": "true", "saveUsername": "true"},
        },
        "pg-two": {
            "uri": "host=localhost2 port=54322 dbname=db2 authcfg=xyz sslmode=require",
            "config": {"savePassword": "false", "saveUsername": "false"},
        },
        "pg-three-invalid": {
            "uri": "port=54323 dbname=db3 user=john password=rockerduck sslmode=disable",
            "config": {"savePassword": "false", "saveUsername": "true"},
        },
    }

    GPKG_CONNECTIONS = {
        "data1.gpkg": "C:\\Users\\flintheart\\glomgold\\data1.gpkg",
        "data2.gpkg": "/home/john/rockerduck/data2.gpkg",
    }

    @classmethod
    def setUp(self):
        for name, settings in self.PG_CONNECTIONS.items():

            md = QgsProviderRegistry.instance().providerMetadata("postgres")

            # Create connection instance & save to QGIS settings
            conn = md.createConnection(settings["uri"], settings["config"])
            QgsProviderRegistry.instance().providerMetadata("postgres").saveConnection(
                conn, name
            )

        for name, path in self.GPKG_CONNECTIONS.items():
            md = QgsProviderRegistry.instance().providerMetadata("ogr")
            config = {"database": path}
            conn = md.createConnection(path, {})
            QgsProviderRegistry.instance().providerMetadata("ogr").saveConnection(
                conn, name
            )

    @classmethod
    def tearDown(self):
        for name in self.PG_CONNECTIONS.keys():
            QgsProviderRegistry.instance().providerMetadata(
                "postgres"
            ).deleteConnection(name)
        for name in self.GPKG_CONNECTIONS.keys():
            QgsProviderRegistry.instance().providerMetadata("ogr").deleteConnection(
                name
            )

    def connection_parsing_alg_test(
        self, tool: DbIliMode, parameters: dict, expected_output: dict
    ):
        alg = (
            DataConnectionParsingGPKGAlgorithm()
            if tool == DbIliMode.ili2gpkg
            else DataConnectionParsingPGAlgorithm()
        )
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        output = alg.processAlgorithm(parameters, context, feedback)
        assert output == expected_output

    def test_pg_data_connection_parsing(self):

        connection_parameters = {
            "DATABASE": "pg-one",
            "NEWSCHEMA": "pg-one-schema",
        }
        expected_output = {
            "SERVICE": "",
            "HOST": "localhost1",
            "PORT": "54321",
            "DBNAME": "db1",
            "USER": "flintheart",
            "PASSWORD": "glomgold",
            "SCHEMA": "pg-one-schema",
            "SSLMODE": "prefer",
            "AUTHCFG": "",
            "ISVALID": True,
        }
        self.connection_parsing_alg_test(
            DbIliMode.ili2pg, connection_parameters, expected_output
        )

        connection_parameters = {
            "DATABASE": "pg-two",
        }
        expected_output = {
            "SERVICE": "",
            "HOST": "localhost2",
            "PORT": "54322",
            "DBNAME": "db2",
            # on an authcfg connection, it takes the user and pw from there, but because the authcfg does not exist it's null here
            "USER": None,
            "PASSWORD": None,
            "SCHEMA": "public",  # taking the default schema
            "SSLMODE": "require",
            "AUTHCFG": "xyz",
            "ISVALID": True,
        }
        self.connection_parsing_alg_test(
            DbIliMode.ili2pg, connection_parameters, expected_output
        )

        connection_parameters = {
            "DATABASE": "pg-three-invalid",
            "SCHEMA": "pg-three-schema",
        }
        expected_output = {
            "SERVICE": "",
            "HOST": "",
            "PORT": "54323",
            "DBNAME": "db3",
            "USER": "John",
            "PASSWORD": "",
            "SCHEMA": "pg-three-schema",
            "SSLMODE": "disable",
            "AUTHCFG": "",
            "ISVALID": False,  # the connection is invalid because the host is missing
        }

    def test_gpkg_data_connection_parsing(self):
        connection_parameters = {"DATABASE": "data1.gpkg"}
        expected_output = {
            "DBPATH": "C:\\Users\\flintheart\\glomgold\\data1.gpkg",
            "ISVALID": True,
        }
        self.connection_parsing_alg_test(
            DbIliMode.ili2gpkg, connection_parameters, expected_output
        )

        connection_parameters = {"DATABASE": "data2.gpkg"}
        expected_output = {
            "DBPATH": "/home/john/rockerduck/data2.gpkg",
            "ISVALID": True,
        }
        self.connection_parsing_alg_test(
            DbIliMode.ili2gpkg, connection_parameters, expected_output
        )

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)
