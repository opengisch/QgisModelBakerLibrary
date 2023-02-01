"""
/***************************************************************************
                              -------------------
        begin                : 09/08/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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

import configparser
import datetime
import logging
import os
import pathlib
import shutil
import tempfile

from qgis.core import QgsProject
from qgis.testing import start_app, unittest

import modelbaker.utils.db_utils as db_utils
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import iliimporter_config

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestMetaConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.toppings_test_path = os.path.join(
            test_path, "testdata", "ilirepo", "usabilityhub"
        )

    """
    General info:
    When passing a --metaConfig (local file path or "ilidata:"-id), parameters from the metaconfig-file are used by ili2db, but when those parameters are set manually as well on the command, they override the parameters from the metaconfig-file.
    """

    def test_metaconfig_kbs_postgis_modelbaker_sets(self):
        """
        Case: Passing a metaconfig file without parameters, modelbaker would set.
        Means: No coalesceCatalogueRef in the metaconfig file.
        Result: These parameters are in the ili2db command (command check), and considered by ili2db (db check).
        """
        metaconfig_file = os.path.join(
            self.toppings_test_path,
            "metaconfig/opengisch_KbS_LV95_V1_4.ini",
        )

        # parse and check metaconfig
        metaconfig = configparser.ConfigParser()
        metaconfig.read_file(open(metaconfig_file))
        assert "ch.ehi.ili2db" in metaconfig.sections()

        # coalesceCatalogueRef must NOT be in the metaconfig
        assert "coalesceCatalogueRef" not in metaconfig["ch.ehi.ili2db"]

        # create importer
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.metaconfig = metaconfig
        importer.configuration.metaconfig_id = metaconfig_file

        # --metaConfig must be in the command
        assert "--metaConfig" in importer.command(False)
        # --coalesceCatalogueRef must be in the command
        assert "--coalesceCatalogueRef" in importer.command(False)

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # coalesceCatalogueRef must be considered in the db
        db_connector = db_utils.get_db_connector(importer.configuration)
        setting_records = db_connector.get_ili2db_settings()

        found_settings = 0
        for setting_record in setting_records:
            if setting_record["tag"] == "ch.ehi.ili2db.catalogueRefTrafo":
                found_settings += 1
                assert setting_record["setting"] == "coalesce"
        assert found_settings == 1

    def test_metaconfig_kbs_postgis_modelbaker_avoids(self):
        """
        Case: Passing a metaconfig file with parameters, modelbaker would set as well.
        Means: coalesceCatalogueRef in the metaconfig file.
        Result: These parameters are NOT in the ili2db command (command check), but considered by ili2db (db check).
        """
        metaconfig_file = os.path.join(
            self.toppings_test_path,
            "metaconfig/opengisch_KbS_LV95_V1_4_with_params.ini",
        )

        # parse and check metaconfig
        metaconfig = configparser.ConfigParser()
        metaconfig.read_file(open(metaconfig_file))
        assert "ch.ehi.ili2db" in metaconfig.sections()

        # coalesceCatalogueRef must be in the metaconfig
        assert "coalesceCatalogueRef" in metaconfig["ch.ehi.ili2db"]

        # create importer
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.metaconfig = metaconfig
        importer.configuration.metaconfig_id = metaconfig_file

        # --metaConfig must be in the command
        assert "--metaConfig" in importer.command(False)
        # --coalesceCatalogueRef must NOT be in the command
        assert "--coalesceCatalogueRef" not in importer.command(False)

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # coalesceCatalogueRef must be considered in the db
        db_connector = db_utils.get_db_connector(importer.configuration)
        setting_records = db_connector.get_ili2db_settings()

        found_settings = 0
        for setting_record in setting_records:
            if setting_record["tag"] == "ch.ehi.ili2db.catalogueRefTrafo":
                found_settings += 1
                assert setting_record["setting"] == "coalesce"
        assert found_settings == 1

    def test_metaconfig_kbs_postgis_additional_parameters(self):
        """
        Means: nameByTopic in the metaconfig file.
        Case: Passing a metaconfig file with parameters, modelbaker does not set.
        Result: These parameters are NOT in the ili2db command (command check), but considered by ili2db (db check).
        """
        metaconfig_file = os.path.join(
            self.toppings_test_path,
            "metaconfig/opengisch_KbS_LV95_V1_4_with_params.ini",
        )

        # parse and check metaconfig
        metaconfig = configparser.ConfigParser()
        metaconfig.read_file(open(metaconfig_file))
        assert "ch.ehi.ili2db" in metaconfig.sections()

        # nameByTopic must be in the metaconfig
        assert "nameByTopic" in metaconfig["ch.ehi.ili2db"]

        # create importer
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.metaconfig = metaconfig
        importer.configuration.metaconfig_id = metaconfig_file

        # --metaConfig must be in the command
        assert "--metaConfig" in importer.command(False)
        # --nameByTopic must NOT be in the command
        assert "--nameByTopic" not in importer.command(False)

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # nameByTopic must be considered in the db
        db_connector = db_utils.get_db_connector(importer.configuration)
        setting_records = db_connector.get_ili2db_settings()

        found_settings = 0
        for setting_record in setting_records:
            if setting_record["tag"] == "ch.ehi.ili2db.nameOptimization":
                found_settings += 1
                assert setting_record["setting"] == "topic"
        assert found_settings == 1

    def test_metaconfig_kbs_postgis_modelbaker_overrides(self):
        """
        Means: smart1inheritance in the metaconfig file but --smart2inheritance in the modelbaker setting.
        Case: Passing a metaconfig file with parameters, modelbaker overrides differently by advanced settings (like smart-inharitance.)
        Result: These parameters overrides are in the ili2db command (command check), and considered by ili2db (db check).
        """
        metaconfig_file = os.path.join(
            self.toppings_test_path,
            "metaconfig/opengisch_KbS_LV95_V1_4_with_params.ini",
        )

        # parse and check metaconfig
        metaconfig = configparser.ConfigParser()
        metaconfig.read_file(open(metaconfig_file))
        assert "ch.ehi.ili2db" in metaconfig.sections()

        # smart1Inheritance must be in the metaconfig
        assert "smart1Inheritance" in metaconfig["ch.ehi.ili2db"]

        # create importer
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.metaconfig = metaconfig
        importer.configuration.metaconfig_id = metaconfig_file
        importer.configuration.inheritance = "smart2"

        # --metaConfig must be in the command
        assert "--metaConfig" in importer.command(False)
        # --smart2Inheritance must be in the command
        assert "--smart2Inheritance" in importer.command(False)

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # --smart2Inheritance must be considered in the db
        db_connector = db_utils.get_db_connector(importer.configuration)
        setting_records = db_connector.get_ili2db_settings()

        found_settings = 0
        for setting_record in setting_records:
            if setting_record["tag"] == "ch.ehi.ili2db.inheritanceTrafo":
                found_settings += 1
                assert setting_record["setting"] == "smart2"
        assert found_settings == 1

    def test_metaconfig_kbs_postgis_params_only(self):
        """
        Means: coalesceCatalogueRef in the metaconfig file and createEnumTabsWithId is NOT in the metaconfig but metaconfig_params_only in the modelbaker setting.
        Case: Passing a metaconfig file with parameters and the setting qgis.modelbaker.metaConfigParamsOnly.
        Result: NO parameters (except exceptions like --metaConfig and models etc) are in the ili2db command (command check), and metaconfig params are considered (coalesceCatalogueRef) by ili2db (db check) but the ones not set are not (createEnumTabsWithId)
        """
        metaconfig_file = os.path.join(
            self.toppings_test_path,
            "metaconfig/opengisch_KbS_LV95_V1_4_metaconfig_params_only.ini",
        )

        # parse and check metaconfig
        metaconfig = configparser.ConfigParser()
        metaconfig.read_file(open(metaconfig_file))
        assert "ch.ehi.ili2db" in metaconfig.sections()

        # coalesceCatalogueRef must be in the metaconfig and createEnumTabsWithId must NOT be in the metaconfig
        assert "coalesceCatalogueRef" in metaconfig["ch.ehi.ili2db"]
        assert "createEnumTabsWithId" not in metaconfig["ch.ehi.ili2db"]

        # check if qgis.modelbaker.metaConfigParamsOnly is there
        assert "CONFIGURATION" in metaconfig.sections()
        assert "qgis.modelbaker.metaConfigParamsOnly" in metaconfig["CONFIGURATION"]

        # create importer
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.metaconfig = metaconfig
        importer.configuration.metaconfig_id = metaconfig_file
        importer.configuration.metaconfig_params_only = True

        # --metaConfig must be in the command
        assert "--metaConfig" in importer.command(False)
        # --coalesceCatalogueRef must NOT be in the command and --createEnumTabsWithId must NOT be in the command
        assert "--coalesceCatalogueRef" not in importer.command(False)
        assert "--createEnumTabsWithId" not in importer.command(False)

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # --coalesceCatalogueRef must be considered in the db
        # --createEnumTabsWithId must NOT be considered in the db
        db_connector = db_utils.get_db_connector(importer.configuration)
        setting_records = db_connector.get_ili2db_settings()

        found_settings = 0
        for setting_record in setting_records:
            if setting_record["tag"] == "ch.ehi.ili2db.catalogueRefTrafo":
                found_settings += 1
                assert setting_record["setting"] == "coalesce"
            if setting_record["tag"] == "ch.ehi.ili2db.createEnumDefs":
                # this should not be found
                found_settings += 1
        assert found_settings == 1

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().clear()

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
