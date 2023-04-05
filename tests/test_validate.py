"""
/***************************************************************************
    begin                :    08.12.2021
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

from modelbaker.iliwrapper import iliimporter, ilivalidator
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import (
    ilidataimporter_config,
    iliimporter_config,
    ilivalidator_config,
    testdata_path,
)

start_app()


class TestExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_validate_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_roads_simple_validation_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)

        # Import valid data to ValidSet
        dataImporter.configuration.dataset = "ValidSet"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Invalid data to InvalidSet
        dataImporter.configuration.dataset = "InvalidSet"
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_roads_simple_invalid.xtf"
        )
        assert dataImporter.run() == iliimporter.Importer.ERROR
        dataImporter.configuration.disable_validation = True
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Validate data
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2gpkg
        validator.configuration = ilivalidator_config(validator.tool)
        validator.configuration.dbfile = importer.configuration.dbfile
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_validation_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)

        # Valid dataset
        validator.configuration.dataset = "ValidSet"
        assert validator.run() == ilivalidator.Validator.SUCCESS

        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 0

        # Invalid dataset
        validator.configuration.dataset = "InvalidSet"
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 1
        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )[0:36]
            == "Intersection coord1 (81.785, 99.314)"
        )

    def test_validate_postgis(self):
        # Schema Import
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
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2pg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)

        # Import valid data to ValidSet
        dataImporter.configuration.dataset = "ValidSet"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Invalid data to InvalidSet
        dataImporter.configuration.dataset = "InvalidSet"
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_roads_simple_invalid.xtf"
        )
        assert dataImporter.run() == iliimporter.Importer.ERROR
        dataImporter.configuration.disable_validation = True
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Validate data
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2pg
        validator.configuration = ilivalidator_config(validator.tool)
        validator.configuration.dbschema = importer.configuration.dbschema
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_validation_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)

        # Valid dataset
        validator.configuration.dataset = "ValidSet"
        assert validator.run() == ilivalidator.Validator.SUCCESS
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 0

        # Invalid dataset
        validator.configuration.dataset = "InvalidSet"
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 1
        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )[0:36]
            == "Intersection coord1 (81.785, 99.314)"
        )

    def test_validate_mssql(self):
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

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2mssql
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "RoadsSimple"
        dataImporter.configuration.dbschema = importer.configuration.dbschema
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)

        # Import valid data to ValidSet
        dataImporter.configuration.dataset = "ValidSet"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_roads_simple.xtf")
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Invalid data to InvalidSet
        dataImporter.configuration.dataset = "InvalidSet"
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_roads_simple_invalid.xtf"
        )
        assert dataImporter.run() == iliimporter.Importer.ERROR
        dataImporter.configuration.disable_validation = True
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Validate data
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2mssql
        validator.configuration = ilivalidator_config(validator.tool)
        validator.configuration.dbschema = importer.configuration.dbschema
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_validation_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)

        # Valid dataset
        validator.configuration.dataset = "ValidSet"
        assert validator.run() == ilivalidator.Validator.SUCCESS
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 0

        # Invalid dataset
        validator.configuration.dataset = "InvalidSet"
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 1
        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )[0:36]
            == "Intersection coord1 (81.785, 99.314)"
        )

    def test_validate_skips(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration.ilifile = testdata_path("ilimodels/brutalism_const.ili")
        importer.configuration.ilimodels = "Brutalism"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_skip_validation_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        importer.configuration.disable_validation = True
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(dataImporter.tool)
        dataImporter.configuration.ilimodels = "Brutalism"
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)

        # Import data to Baseset
        dataImporter.configuration.dataset = "Baseset"
        dataImporter.configuration.xtffile = testdata_path("xtf/test_validate_skip.xtf")
        assert dataImporter.run() == iliimporter.Importer.ERROR
        dataImporter.configuration.disable_validation = True
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Validate data
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2gpkg
        validator.configuration = ilivalidator_config(validator.tool)
        validator.configuration.dbfile = dataImporter.configuration.dbfile
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_validation_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)

        # Baseset dataset
        validator.configuration.dataset = "Baseset"

        # No skip
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 4

        expected_error_geometry = (
            "value 1314393.469 is out of range in attribute Geometry"
        )
        expected_error_multiplicity_1 = "Attribute Name requires a value"
        expected_error_multiplicity_2 = (
            "Object should associate 1 to 1 target objects (instead of 0)"
        )
        expected_error_constraint = (
            "Set Constraint Brutalism.Buildings.Resident.Constraint1 is not true."
        )
        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_geometry
        )
        assert (
            result_model.index(1, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_multiplicity_1
        )
        assert (
            result_model.index(2, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_multiplicity_2
        )
        assert (
            result_model.index(3, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_constraint
        )

        # Skip geometry errors
        validator.configuration.skip_geometry_errors = True
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 3
        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_multiplicity_1
        )
        assert (
            result_model.index(1, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_multiplicity_2
        )
        assert (
            result_model.index(2, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_constraint
        )

        # Multiplicity off
        validator.configuration.skip_geometry_errors = False
        validator.configuration.valid_config = testdata_path(
            "validate/multiplicityOff.ini"
        )
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 2
        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_geometry
        )
        assert (
            result_model.index(1, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_constraint
        )

        # Constraint off
        validator.configuration.valid_config = testdata_path(
            "validate/constraintValidationOff.ini"
        )
        assert validator.run() == ilivalidator.Validator.ERROR
        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 3
        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_geometry
        )
        assert (
            result_model.index(1, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_multiplicity_1
        )
        assert (
            result_model.index(2, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_error_multiplicity_2
        )

    def test_validate_exportmodels_gpkg(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "Staedtische_Ortsplanung_V1_1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "staedtische_ortsplanung_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # Import data
        # we disable the validation, since we have some mistakes (on purpose) in the xtf concerning Staedtische_Orstplanung_V1_1
        dataImporter = iliimporter.Importer(dataImport=True)
        dataImporter.tool = DbIliMode.ili2gpkg
        dataImporter.configuration = ilidataimporter_config(
            dataImporter.tool, "ilimodels"
        )
        dataImporter.configuration.dbfile = importer.configuration.dbfile
        dataImporter.configuration.disable_validation = True
        dataImporter.configuration.with_importtid = True
        dataImporter.configuration.xtffile = testdata_path(
            "xtf/test_staedtische_ortsplanung_v1_1.xtf"
        )
        dataImporter.stdout.connect(self.print_info)
        dataImporter.stderr.connect(self.print_error)
        assert dataImporter.run() == iliimporter.Importer.SUCCESS

        # Validate at city level (not setting --exportModels)
        # means validation will fail - we encouter the constraint failure from Staedtische_Ortsplanung_V1_1, Staedtisches_Gewerbe_V1 and Kantonale_Ortsplanung_V1_1
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2gpkg
        validator.configuration = ilivalidator_config(validator.tool, "ilimodels")
        validator.configuration.ilimodels = (
            "Staedtische_Ortsplanung_V1_1;Staedtisches_Gewerbe_V1;Infrastruktur_V1"
        )
        validator.configuration.dbfile = dataImporter.configuration.dbfile
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_test_staedtische_ortsplanung_v1_1_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)
        # No skip
        assert validator.run() == ilivalidator.Validator.ERROR

        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 3

        expected_staedtische_gewerbe_error = (
            "Needs an ethical evaluation (EthischeBeurteilung)"
        )
        expected_kantonale_ortsplanung_error = (
            "Beschreibung and/or Referenzcode must be defined."
        )
        expected_staedtische_ortsplanung_error = "Beschreibung needed when top secret."

        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_staedtische_gewerbe_error
        )
        assert (
            result_model.index(1, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_kantonale_ortsplanung_error
        )
        assert (
            result_model.index(2, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_staedtische_ortsplanung_error
        )

        # Validate at cantonal level (setting --exportModels KantonaleOrtsplanung_V1_1)
        # means validation will fail - we encouter the constraint failure from Kantonale_Ortsplanung_V1_1
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2gpkg
        validator.configuration = ilivalidator_config(validator.tool, "ilimodels")
        validator.configuration.ilimodels = (
            "Staedtische_Ortsplanung_V1_1;Infrastruktur_V1"
        )
        validator.configuration.iliexportmodels = "Kantonale_Ortsplanung_V1_1"
        validator.configuration.dbfile = dataImporter.configuration.dbfile
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_test_kantonale_ortsplanung_v1_1_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)
        # No skip
        assert validator.run() == ilivalidator.Validator.ERROR

        # check validation result
        result_model = ilivalidator.ValidationResultModel()
        result_model.configuration = validator.configuration
        result_model.reload()
        assert result_model.rowCount() == 1

        expected_kantonale_ortsplanung_error = (
            "Beschreibung and/or Referenzcode must be defined."
        )

        assert (
            result_model.index(0, 0).data(
                int(ilivalidator.ValidationResultModel.Roles.MESSAGE)
            )
            == expected_kantonale_ortsplanung_error
        )

        # Validate at national level (setting --exportModels Ortsplanung_V1_1;Gewerbe_V1)
        # means validation will succeed.
        validator = ilivalidator.Validator()
        validator.tool = DbIliMode.ili2gpkg
        validator.configuration = ilivalidator_config(validator.tool, "ilimodels")
        validator.configuration.ilimodels = (
            "Staedtische_Ortsplanung_V1_1;Staedtisches_Gewerbe_V1;Infrastruktur_V1"
        )
        validator.configuration.iliexportmodels = "Ortsplanung_V1_1;Gewerbe_V1"
        validator.configuration.dbfile = dataImporter.configuration.dbfile
        validator.configuration.xtflog = os.path.join(
            self.basetestpath,
            "tmp_test_kantonale_ortsplanung_v1_1_result_{:%Y%m%d%H%M%S%f}.xtf".format(
                datetime.datetime.now()
            ),
        )
        validator.stdout.connect(self.print_info)
        validator.stderr.connect(self.print_error)
        # No skip
        assert validator.run() == ilivalidator.Validator.SUCCESS

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
