# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    22/06/2022
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

import os

from qgis.testing import start_app, unittest

from modelbaker.iliwrapper.ili2dbconfig import Ili2DbCommandConfiguration
from modelbaker.utils.globals import DbActionType
from tests.utils import get_pg_connection_string, iliimporter_config, testdata_path

start_app()


class TestPgservice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.pgservicefile = os.environ.get("PGSERVICEFILE", None)
        os.environ["PGSERVICEFILE"] = testdata_path("pgservice/pg_service.conf")

    def test_pure_service(self):
        """
        Set up connection with service configuration without authentification.
        In the uri the connection parameters are taken from the service conf and the username password from the seperate parameters.
        """
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_pure{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.dbservice = "freddys_service"
        # needs superuser since credentials from service are not valid
        importer.configuration.db_use_super_login = True

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
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

        # check layer uri if dbname/user/password are not in the manual params but from service conf: user and password are freddy

    def test_manual_service(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_pure{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.dbservice = "onlydb_service"
        # needs superuser since credentials from service are not valid
        importer.configuration.db_use_super_login = True

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
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

        # check layer uri if dbname are not in the manual but user password are (docker)

    def test_authconf_service(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_pure{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.dbservice = "freddys_service"
        # needs superuser since credentials from service are not valid
        importer.configuration.db_use_super_login = True

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
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

        # check layer uri if dbname are not in the manual and neither password and user but authdb instead

    def test_pgservice_pg_config_panel(self):

        pg_config_panel = PgConfigPanel(None, DbActionType.EXPORT)
        pg_config_panel.show()

        index_postgis_test = pg_config_panel.pg_service_combo_box.findData(
            "postgis_test", PgConfigPanel._SERVICE_COMBOBOX_ROLE.DBSERVICE
        )
        self.assertIsNot(index_postgis_test, -1)

        configuration = Ili2DbCommandConfiguration()
        configuration.dbservice = "postgis_test"
        pg_config_panel.set_fields(configuration)
        pg_config_panel.get_fields(configuration)

        self.assertEqual(configuration.dbhost, "db.test.com")
        self.assertEqual(configuration.dbport, "5433")
        self.assertEqual(configuration.dbusr, "postgres")
        self.assertEqual(configuration.dbpwd, "secret")
        self.assertEqual(configuration.sslmode, "verify-ca")

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        if cls.pgservicefile:
            os.environ["PGSERVICEFILE"] = cls.pgservicefile
