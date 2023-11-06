"""
/***************************************************************************
                              -------------------
        begin                : 03.11.2023
        git sha              : :%H$
        copyright            : (C) 2023 by Dave Signer
        email                : david@opengis.ch
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
import pathlib
import tempfile

from qgis.core import QgsProject
from qgis.testing import start_app, unittest

from modelbaker.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.utils.globals import OptimizeStrategy
from tests.utils import get_pg_connection_string, iliimporter_config, testdata_path

CATALOGUE_DATASETNAME = "Catset"

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestProjectOIDs(unittest.TestCase):

    BASKET_TABLES = [
        "t_ili2db_basket",
        "T_ILI2DB_BASKET",
        "t_ili2db_dataset",
        "T_ILI2DB_DATASET",
    ]

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    """
    Those tests check:
        the oids...
    """

    def test_oids_tids_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/OIDMadness.ili")
        importer.configuration.ilimodels = "OIDMadness"
        importer.configuration.dbschema = "oid_madness{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        ### 1. OptimizeStrategy.NONE ###
        strategy = OptimizeStrategy.NONE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._oids_tids_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._oids_tids_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._oids_tids_hide(generator, strategy)

    def test_oids_tids_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/OIDMadness_V1.ili")
        importer.configuration.ilimodels = "OIDMadness_V1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_optimal_oid_madness_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        ### 1. OptimizeStrategy.NONE ###
        strategy = OptimizeStrategy.NONE

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
            consider_basket_handling=True,
        )

        self._oids_tids_none(generator, strategy, True)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
            consider_basket_handling=True,
        )

        self._oids_tids_group(generator, strategy, True)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
            consider_basket_handling=True,
        )

        self._oids_tids_hide(generator, strategy, True)

    def test_oids_tids_mssql(self):

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/OIDMadness_V1.ili")
        importer.configuration.ilimodels = "OIDMadness_V1"
        importer.configuration.dbschema = (
            "optimal_oid_madness_{:%Y%m%d%H%M%S%f}".format(datetime.datetime.now())
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        assert importer.run() == iliimporter.Importer.SUCCESS

        ### 1. OptimizeStrategy.NONE ###
        strategy = OptimizeStrategy.NONE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._oids_tids_none(generator, strategy, True)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._oids_tids_group(generator, strategy, True)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._oids_tids_hide(generator, strategy, True)

    def _oids_tids_none(self, generator, strategy, not_pg=False):

        # all layers are visible
        available_layers = generator.layers()
        layers_of_interest = [
            l for l in available_layers if l.name not in self.BASKET_TABLES
        ]

        oid_map = dict()

        for layer in layers_of_interest:
            oid_entry = dict()
            oid_entry["alias"] = layer.alias
            oid_entry["iliname"] = layer.ili_name
            oid_entry["oid_domain"] = layer.oid_domain
            oid_map[layer.name] = oid_entry

        assert oid_map == {
            "parzellenidentifikation": {
                "alias": "Parzellenidentifikation",
                "iliname": "OIDBaseMadness_V1.Parzellenidentifikation",
                "oid_domain": None,
            },
            "besitzerin": {
                "alias": "BesitzerIn",
                "iliname": "OIDBaseMadness_V1.Konstruktionen.BesitzerIn",
                "oid_domain": "INTERLIS.ANYOID",
            },
            "oidbasmdnss_v1wohnraum_gebaeude": {
                "alias": "Wohnraum.Gebaeude",
                "iliname": "OIDBaseMadness_V1.Wohnraum.Gebaeude",
                "oid_domain": "INTERLIS.UUIDOID",
            },
            "gartenhaus": {
                "alias": "Gartenhaus",
                "iliname": "OIDBaseMadness_V1.Wohnraum.Gartenhaus",
                "oid_domain": None,
            },
            "park": {
                "alias": "Park",
                "iliname": "OIDMadness_V1.Natur.Park",
                "oid_domain": None,
            },
            "brache": {
                "alias": "Brache",
                "iliname": "OIDMadness_V1.Natur.Brache",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "wiese": {
                "alias": "Wiese",
                "iliname": "OIDMadness_V1.Natur.Wiese",
                "oid_domain": "INTERLIS.I32OID",
            },
            "wald": {
                "alias": "Wald",
                "iliname": "OIDMadness_V1.Natur.Wald",
                "oid_domain": "INTERLIS.UUIDOID",
            },
            "see": {
                "alias": "See",
                "iliname": "OIDMadness_V1.Natur.See",
                "oid_domain": "OIDMadness_V1.TypeID",
            },
            "fluss": {
                "alias": "Fluss",
                "iliname": "OIDMadness_V1.Natur.Fluss",
                "oid_domain": "OIDMadness_V1.TypeIDShort",
            },
            "oidmadness_v1quartier_gebaeude": {
                "alias": "Quartier.Gebaeude",
                "iliname": "OIDMadness_V1.Quartier.Gebaeude",
                "oid_domain": "INTERLIS.UUIDOID",
            },
            "oidmadness_v1business_gebaeude": {
                "alias": "Business.Gebaeude",
                "iliname": "OIDMadness_V1.Business.Gebaeude",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "parkplatz": {
                "alias": "Parkplatz",
                "iliname": "OIDMadness_V1.Business.Parkplatz",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "oidmadness_v1spass_gebaeude": {
                "alias": "Spass.Gebaeude",
                "iliname": "OIDMadness_V1.Spass.Gebaeude",
                "oid_domain": "INTERLIS.I32OID",
            },
            "spielplatz": {
                "alias": "Spielplatz",
                "iliname": "OIDMadness_V1.Spass.Spielplatz",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
        }

        # set two layers default expression
        for layer in layers_of_interest:
            if layer.name == "brache":
                layer.t_ili_tid_field.default_value_expression = (
                    "'ch_baker'||ilicounter(000000000,999999999)"
                )
            if layer.name == "wiese":
                layer.t_ili_tid_field.default_value_expression = (
                    "ilicounter(0,999999999)"
                )

        # check if it's properly set
        count = 0
        for layer in available_layers:
            if layer.name == "brache":
                count += 1
                assert (
                    layer.t_ili_tid_field.default_value_expression
                    == "'ch_baker'||ilicounter(000000000,999999999)"
                )
            if layer.name == "wiese":
                count += 1
                assert (
                    layer.t_ili_tid_field.default_value_expression
                    == "ilicounter(0,999999999)"
                )
        assert count == 2

    def _oids_tids_group(self, generator, strategy, not_pg=False):

        # all layers are visible
        available_layers = generator.layers()
        layers_of_interest = [
            l for l in available_layers if l.name not in self.BASKET_TABLES
        ]

        oid_map = dict()

        for layer in layers_of_interest:
            oid_entry = dict()
            oid_entry["alias"] = layer.alias
            oid_entry["iliname"] = layer.ili_name
            oid_entry["oid_domain"] = layer.oid_domain
            oid_map[layer.name] = oid_entry

        assert oid_map == {
            "parzellenidentifikation": {
                "alias": "Parzellenidentifikation",
                "iliname": "OIDBaseMadness_V1.Parzellenidentifikation",
                "oid_domain": None,
            },
            "besitzerin": {
                "alias": "BesitzerIn",
                "iliname": "OIDBaseMadness_V1.Konstruktionen.BesitzerIn",
                "oid_domain": "INTERLIS.ANYOID",
            },
            "oidbasmdnss_v1wohnraum_gebaeude": {
                "alias": "Wohnraum.Gebaeude",
                "iliname": "OIDBaseMadness_V1.Wohnraum.Gebaeude",
                "oid_domain": "INTERLIS.UUIDOID",
            },
            "gartenhaus": {
                "alias": "Gartenhaus",
                "iliname": "OIDBaseMadness_V1.Wohnraum.Gartenhaus",
                "oid_domain": None,
            },
            "park": {
                "alias": "Park",
                "iliname": "OIDMadness_V1.Natur.Park",
                "oid_domain": None,
            },
            "brache": {
                "alias": "Brache",
                "iliname": "OIDMadness_V1.Natur.Brache",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "wiese": {
                "alias": "Wiese",
                "iliname": "OIDMadness_V1.Natur.Wiese",
                "oid_domain": "INTERLIS.I32OID",
            },
            "wald": {
                "alias": "Wald",
                "iliname": "OIDMadness_V1.Natur.Wald",
                "oid_domain": "INTERLIS.UUIDOID",
            },
            "see": {
                "alias": "See",
                "iliname": "OIDMadness_V1.Natur.See",
                "oid_domain": "OIDMadness_V1.TypeID",
            },
            "fluss": {
                "alias": "Fluss",
                "iliname": "OIDMadness_V1.Natur.Fluss",
                "oid_domain": "OIDMadness_V1.TypeIDShort",
            },
            "oidmadness_v1quartier_gebaeude": {
                "alias": "Quartier.Gebaeude",
                "iliname": "OIDMadness_V1.Quartier.Gebaeude",
                "oid_domain": "INTERLIS.UUIDOID",
            },
            "oidmadness_v1business_gebaeude": {
                "alias": "Business.Gebaeude",
                "iliname": "OIDMadness_V1.Business.Gebaeude",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "parkplatz": {
                "alias": "Parkplatz",
                "iliname": "OIDMadness_V1.Business.Parkplatz",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "oidmadness_v1spass_gebaeude": {
                "alias": "Spass.Gebaeude",
                "iliname": "OIDMadness_V1.Spass.Gebaeude",
                "oid_domain": "INTERLIS.I32OID",
            },
            "spielplatz": {
                "alias": "Spielplatz",
                "iliname": "OIDMadness_V1.Spass.Spielplatz",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
        }

        # set two layers default expression
        for layer in layers_of_interest:
            if layer.name == "brache":
                layer.t_ili_tid_field.default_value_expression = (
                    "'ch_baker'||ilicounter(000000000,999999999)"
                )
            if layer.name == "wiese":
                layer.t_ili_tid_field.default_value_expression = (
                    "ilicounter(0,999999999)"
                )

        # check if it's properly set
        count = 0
        for layer in available_layers:
            if layer.name == "brache":
                count += 1
                assert (
                    layer.t_ili_tid_field.default_value_expression
                    == "'ch_baker'||ilicounter(000000000,999999999)"
                )
            if layer.name == "wiese":
                count += 1
                assert (
                    layer.t_ili_tid_field.default_value_expression
                    == "ilicounter(0,999999999)"
                )
        assert count == 2

    def _oids_tids_hide(self, generator, strategy, not_pg=False):

        # only relevant layers are visible
        available_layers = generator.layers()
        layers_of_interest = [
            l
            for l in available_layers
            if l.is_relevant and l.name not in self.BASKET_TABLES
        ]

        oid_map = dict()

        for layer in layers_of_interest:
            oid_entry = dict()
            oid_entry["alias"] = layer.alias
            oid_entry["iliname"] = layer.ili_name
            oid_entry["oid_domain"] = layer.oid_domain
            oid_map[layer.name] = oid_entry

        # this one is hidden: 'oidbasmdnss_v1wohnraum_gebaeude': {'alias': 'Wohnraum.Gebaeude', 'iliname': 'OIDBaseMadness_V1.Wohnraum.Gebaeude', 'oid_domain': 'INTERLIS.UUIDOID'},
        assert oid_map == {
            "parzellenidentifikation": {
                "alias": "Parzellenidentifikation",
                "iliname": "OIDBaseMadness_V1.Parzellenidentifikation",
                "oid_domain": None,
            },
            "besitzerin": {
                "alias": "BesitzerIn",
                "iliname": "OIDBaseMadness_V1.Konstruktionen.BesitzerIn",
                "oid_domain": "INTERLIS.ANYOID",
            },
            "gartenhaus": {
                "alias": "Gartenhaus",
                "iliname": "OIDBaseMadness_V1.Wohnraum.Gartenhaus",
                "oid_domain": None,
            },
            "park": {
                "alias": "Park",
                "iliname": "OIDMadness_V1.Natur.Park",
                "oid_domain": None,
            },
            "brache": {
                "alias": "Brache",
                "iliname": "OIDMadness_V1.Natur.Brache",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "wiese": {
                "alias": "Wiese",
                "iliname": "OIDMadness_V1.Natur.Wiese",
                "oid_domain": "INTERLIS.I32OID",
            },
            "wald": {
                "alias": "Wald",
                "iliname": "OIDMadness_V1.Natur.Wald",
                "oid_domain": "INTERLIS.UUIDOID",
            },
            "see": {
                "alias": "See",
                "iliname": "OIDMadness_V1.Natur.See",
                "oid_domain": "OIDMadness_V1.TypeID",
            },
            "fluss": {
                "alias": "Fluss",
                "iliname": "OIDMadness_V1.Natur.Fluss",
                "oid_domain": "OIDMadness_V1.TypeIDShort",
            },
            "oidmadness_v1quartier_gebaeude": {
                "alias": "Quartier.Gebaeude",
                "iliname": "OIDMadness_V1.Quartier.Gebaeude",
                "oid_domain": "INTERLIS.UUIDOID",
            },
            "oidmadness_v1business_gebaeude": {
                "alias": "Business.Gebaeude",
                "iliname": "OIDMadness_V1.Business.Gebaeude",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "parkplatz": {
                "alias": "Parkplatz",
                "iliname": "OIDMadness_V1.Business.Parkplatz",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
            "oidmadness_v1spass_gebaeude": {
                "alias": "Spass.Gebaeude",
                "iliname": "OIDMadness_V1.Spass.Gebaeude",
                "oid_domain": "INTERLIS.I32OID",
            },
            "spielplatz": {
                "alias": "Spielplatz",
                "iliname": "OIDMadness_V1.Spass.Spielplatz",
                "oid_domain": "INTERLIS.STANDARDOID",
            },
        }

        # set two layers default expression
        for layer in layers_of_interest:
            if layer.name == "brache":
                layer.t_ili_tid_field.default_value_expression = (
                    "'ch_baker'||ilicounter(000000000,999999999)"
                )
            if layer.name == "wiese":
                layer.t_ili_tid_field.default_value_expression = (
                    "ilicounter(0,999999999)"
                )

        # check if it's properly set
        count = 0
        for layer in available_layers:
            if layer.name == "brache":
                count += 1
                assert (
                    layer.t_ili_tid_field.default_value_expression
                    == "'ch_baker'||ilicounter(000000000,999999999)"
                )
            if layer.name == "wiese":
                count += 1
                assert (
                    layer.t_ili_tid_field.default_value_expression
                    == "ilicounter(0,999999999)"
                )
        assert count == 2

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()
