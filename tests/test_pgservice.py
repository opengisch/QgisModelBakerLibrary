# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    24/06/2022
    git sha              :    :%H$
    copyright            :    (C) 2022 by Dave Signer (took base from) Damiano Lombardi
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
from subprocess import call

from qgis.core import QgsDataSourceUri, QgsProject
from qgis.testing import start_app, unittest

import modelbaker.utils.db_utils as db_utils
from modelbaker.dataobjects.project import Project
from modelbaker.db_factory.db_simple_factory import DbSimpleFactory
from modelbaker.db_factory.pg_command_config_manager import PgCommandConfigManager
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.iliwrapper.ili2dbconfig import ValidateConfiguration
from tests.utils import iliimporter_config, testdata_path

start_app()


class TestPgservice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.pgservicefile = os.environ.get("PGSERVICEFILE", None)
        os.environ["PGSERVICEFILE"] = testdata_path("pgservice/pg_service.conf")
        os.environ["PGPASSWORD"] = "docker"
        call(
            [
                "psql",
                "-h" + os.environ["PGHOST"],
                "-Udocker",
                "-c \"CREATE USER sevy WITH LOGIN SUPERUSER PASSWORD 'sevys_password';\"",
            ],
            env=os.environ,
        )
        call(
            [
                "psql",
                "-h" + os.environ["PGHOST"],
                "-Udocker",
                "-c \"CREATE USER mani WITH LOGIN SUPERUSER PASSWORD 'manis_password';\"",
            ],
            env=os.environ,
        )

    def test_pure_service(self):
        """
        Set up connection with service configuration with authentification.
        [sevys_service]
        dbname=gis
        user=sevy
        password=sevys_password

        Import is done with superuser docker / docker.

        In the uri the dbname, username and password are taken from the service conf and the host from the manual parameter.
        """
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_pure{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        # override default values
        importer.configuration.base_configuration.super_pg_user = "docker"
        importer.configuration.base_configuration.super_pg_password = "docker"
        importer.configuration.dbusr = ""
        importer.configuration.dbpwd = ""
        # assuming user chooses service
        importer.configuration.dbservice = "sevys_service"
        # params would be set over the gui when loading the service conf
        importer.configuration.database = "gis"
        importer.configuration.dbusr = "sevy"
        importer.configuration.dbpwd = "sevys_password"
        # needs superuser
        importer.configuration.db_use_super_login = True

        # create schema with superuser
        db_simple_factory = DbSimpleFactory()
        db_factory = db_simple_factory.create_factory(importer.configuration.tool)
        res, message = db_factory.pre_generate_project(importer.configuration)
        assert res

        # import model
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = PgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        mgmt_uri = config_manager.get_uri(importer.configuration.db_use_super_login)

        generator = Generator(
            DbIliMode.ili2pg,
            uri,
            "smart2",
            importer.configuration.dbschema,
            mgmt_uri=mgmt_uri,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # dbname/user/password should not be in the layer source
        # for validation they should be available from the service conf
        count = 0
        for layer in available_layers:
            if layer.name == "landcover":
                source_provider = layer.layer.dataProvider()
                source = QgsDataSourceUri(layer.layer.dataProvider().dataSourceUri())
                assert source.service() == "sevys_service"
                assert source.host() == os.environ["PGHOST"]
                assert source.database() is None
                assert source.username() is None
                assert source.password() is None

                validate_configuration = ValidateConfiguration()
                valid, mode = db_utils.get_configuration_from_layersource(
                    source_provider, source, validate_configuration
                )
                assert valid

                assert validate_configuration.database == "gis"
                assert validate_configuration.dbusr == "sevy"
                assert validate_configuration.dbpwd == "sevys_password"

                count += 1

                break

        assert count == 1

    def test_manual_service(self):
        """
        Set up connection with service configuration with authentification.
        [manis_service]
        dbname=gis

        Import is done with superuser docker / docker.

        In the uri the dbname is taken from the service conf and the host, username and password from the manual parameter.
        """
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_pure{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        # override default values
        importer.configuration.base_configuration.super_pg_user = "docker"
        importer.configuration.base_configuration.super_pg_password = "docker"
        importer.configuration.dbusr = ""
        importer.configuration.dbpwd = ""
        # assuming user chooses service
        importer.configuration.dbservice = "manis_service"
        # params would be set over the gui when loading the service conf
        importer.configuration.database = "gis"
        importer.configuration.dbusr = ""
        importer.configuration.dbpwd = ""
        # assuming user types in additional params
        importer.configuration.dbusr = "mani"
        importer.configuration.dbpwd = "manis_password"
        # needs superuser
        importer.configuration.db_use_super_login = True

        # create schema with superuser
        db_simple_factory = DbSimpleFactory()
        db_factory = db_simple_factory.create_factory(importer.configuration.tool)
        res, message = db_factory.pre_generate_project(importer.configuration)
        assert res

        # import model
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = PgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        mgmt_uri = config_manager.get_uri(importer.configuration.db_use_super_login)

        # create schema with superuser
        db_simple_factory = DbSimpleFactory()
        db_factory = db_simple_factory.create_factory(importer.configuration.tool)
        res, message = db_factory.pre_generate_project(importer.configuration)
        assert res

        generator = Generator(
            DbIliMode.ili2pg,
            uri,
            "smart2",
            importer.configuration.dbschema,
            mgmt_uri=mgmt_uri,
        )
        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # dbname should not be in the layer source but user/password are (mani/manis_password)
        # for validation dbname should be available from the service conf
        count = 0
        for layer in available_layers:
            if layer.name == "landcover":
                source_provider = layer.layer.dataProvider()
                source = QgsDataSourceUri(layer.layer.dataProvider().dataSourceUri())
                assert source.service() == "manis_service"
                assert source.host() == os.environ["PGHOST"]
                assert source.database() is None
                assert source.username() is "mani"
                assert source.password() is "manis_password"

                validate_configuration = ValidateConfiguration()
                valid, mode = db_utils.get_configuration_from_layersource(
                    source_provider, source, validate_configuration
                )
                assert valid

                assert validate_configuration.database == "gis"
                assert validate_configuration.dbusr == "mani"
                assert validate_configuration.dbpwd == "manis_password"

                count += 1

                break

        assert count == 1

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        if cls.pgservicefile:
            os.environ["PGSERVICEFILE"] = cls.pgservicefile
