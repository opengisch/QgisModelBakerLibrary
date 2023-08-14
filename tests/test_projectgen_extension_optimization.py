"""
/***************************************************************************
                              -------------------
        begin                : 14.08.2023
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

import configparser
import datetime
import logging
import os
import pathlib
import shutil
import tempfile
from decimal import Decimal

import yaml
from qgis.core import Qgis, QgsEditFormConfig, QgsProject, QgsRelation
from qgis.PyQt.QtCore import QEventLoop, Qt, QTimer
from qgis.testing import start_app, unittest

from modelbaker.dataobjects.project import Project
from modelbaker.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.iliwrapper.ilicache import (
    IliDataCache,
    IliDataItemModel,
    IliToppingFileCache,
    IliToppingFileItemModel,
)
from tests.utils import get_pg_connection_string, iliimporter_config, testdata_path

CATALOGUE_DATASETNAME = "Catset"

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestProjectExtOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    '''
    Those tests check if:
    - no ambiguous layers exists - they are all named properly and unique
    - irrelevant layers are detected (according to the assumptions below)
    - irrelevant layers are handled according the the chosen strategy: hidden or grouped
    - relations (and their widgets) are handled according to the stategy (not created when hidden, not in the forms used when grouped)
    
    Assumption:
    Since it appears almost impossible to care for all the cases, I need to make some assumptions what mostly would be the case.
    - When you extend a base class with the same name, you intend to "replace" it, otherwise you would rename it.
    - When you extend a base class multiple times (what you do with different names) then you intend to "replace" it.
    - Exception for the two cases above: When you extended the class it in the same model but another topic (because if you intent to "replace" it, you would have made it ABSTRACT)

    This is tested with three use cases:
    - Polymorphic_Ortsplanung_V1_1 containing several topics extending the same class
    - Staedtische_Ortsplanung_V1_1 containing several extention levels on the same class
    - Bauplanung_V1_1 containing structures and extending assocciations
    '''


    def test_staedtische_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Staedtische_Ortsplanung_V1_1.ili")
        importer.configuration.ilimodels = "Staedtische_Ortsplanung_V1_1"
        importer.configuration.dbschema = "optimal_staedtische_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            importer.configuration.inheritance,
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['dsaf.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        
    def test_staedtische_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Staedtische_Ortsplanung_V1_1.ili")
        importer.configuration.ilimodels = "Staedtische_Ortsplanung_V1_1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_optimal_staedtische_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['asdf.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

    def test_staedtische_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Staedtische_Ortsplanung_V1_1.ili")
        importer.configuration.ilimodels = "Staedtische_Ortsplanung_V1_1"
        importer.configuration.dbschema = "optimal_staedtische_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
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

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['asdffasd.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

    def test_polymorphic_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Polymorphic_Ortsplanung_V1_1.ili")
        importer.configuration.ilimodels = "Polymorphic_Ortsplanung_V1_1"
        importer.configuration.dbschema = "optimal_polymorph_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            importer.configuration.inheritance,
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['Ortsplanung_V1_1.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

    def test_polymorphic_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Polymorphic_Ortsplanung_V1_1.ili")
        importer.configuration.ilimodels = "Polymorphic_Ortsplanung_V1_1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_optimal_polymorph_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['Ortsplanung_V1_1.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

    def test_polymorphic_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Polymorphic_Ortsplanung_V1_1.ili")
        importer.configuration.ilimodels = "Polymorphic_Ortsplanung_V1_1"
        importer.configuration.dbschema = "optimal_polymorph_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
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

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['Ortsplanung_V1_1.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

    def test_baustruct_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Bauplanung_V1_1.ili")
        importer.configuration.ilimodels = "Bauplanung_V1_1"
        importer.configuration.dbschema = "optimal_baustruct_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            importer.configuration.inheritance,
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['asf.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        
    def test_baustruct_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Bauplanung_V1_1.ili")
        importer.configuration.ilimodels = "Bauplanung_V1_1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_optimal_baustruct_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['sdaf.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

    def test_baustruct_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Bauplanung_V1_1.ili")
        importer.configuration.ilimodels = "Bauplanung_V1_1"
        importer.configuration.dbschema = "optimal_baustruct_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
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

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [l.ili_name for l in available_layers if not l.is_relevant ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias)>1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases =  ['BesitzerIn', 'Freizeit.Gebaeude', 'Gewerbe.Gebaeude', 'Hallen.Gebaeude', 'IndustrieGewerbe.Gebaeude', 'Markthalle', 'Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude', 'Strasse', 'TurnhalleTyp1', 'TurnhalleTyp2']
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames =  ['asdfafs.Konstruktionen.Gebaeude']
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()