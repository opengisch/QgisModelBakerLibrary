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

import datetime
import logging
import os
import pathlib
import tempfile

from qgis.core import QgsLayerTreeLayer, QgsProject
from qgis.testing import start_app, unittest

from modelbaker.dataobjects.project import Project
from modelbaker.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.utils.globals import OptimizeStrategy
from tests.utils import get_pg_connection_string, iliimporter_config, testdata_path

CATALOGUE_DATASETNAME = "Catset"

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestProjectExtOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    """
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
    """

    def test_extopt_staedtische_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Staedtische_Ortsplanung_V1_1.ili"
        )
        importer.configuration.ilimodels = "Staedtische_Ortsplanung_V1_1"
        importer.configuration.dbschema = (
            "optimal_staedtische_{:%Y%m%d%H%M%S%f}".format(datetime.datetime.now())
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
            optimize_strategy=strategy,
        )

        self._extopt_staedtische_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_staedtische_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_staedtische_hide(generator, strategy)

    def test_extopt_staedtische_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Staedtische_Ortsplanung_V1_1.ili"
        )
        importer.configuration.ilimodels = "Staedtische_Ortsplanung_V1_1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_optimal_staedtische_{:%Y%m%d%H%M%S%f}.gpkg".format(
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
        )

        self._extopt_staedtische_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_staedtische_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_staedtische_hide(generator, strategy)

    def test_extopt_staedtische_mssql(self):
        return  # to do
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Staedtische_Ortsplanung_V1_1.ili"
        )
        importer.configuration.ilimodels = "Staedtische_Ortsplanung_V1_1"
        importer.configuration.dbschema = (
            "optimal_staedtische_{:%Y%m%d%H%M%S%f}".format(datetime.datetime.now())
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
            optimize_strategy=strategy,
        )

        self._extopt_staedtische_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_staedtische_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_staedtische_hide(generator, strategy)

    def _extopt_staedtische_none(self, generator, strategy):

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        [alias for alias in aliases if aliases.count(alias) > 1]

        # check no ambiguous layers exists
        expected_aliases = [
            "BesitzerIn",
            "Freizeit.Gebaeude",
            "Gebaeude_StadtFirma",
            "Gewerbe.Gebaeude",
            "Gewerbe_V1.Firmen.Firma",
            "Kantonale_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Staedtisches_Gewerbe_V1.Firmen.Firma",
            "Strasse",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Kantonale_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Gewerbe_V1.Firmen.Firma",
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 9

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {
            "Strasse",
            "Freizeit.Gebaeude",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Kantonale_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Gewerbe.Gebaeude",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Staedtisches_Gewerbe_V1.Firmen.Firma",
            "Gewerbe_V1.Firmen.Firma",
            "Gebaeude_StadtFirma",
            "BesitzerIn",
        }

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 10

        # strasse should have relation editors to all layers (4/4)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 5
                for tab in efc.tabs():
                    if tab.name() == "stadtscng_v1_1freizeit_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "stadtscng_v1_1gewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "kantnl_ng_v1_1konstruktionen_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
        # should find 4
        assert count == 4

        QgsProject.instance().clear()

    def _extopt_staedtische_group(self, generator, strategy):
        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases = [
            "BesitzerIn",
            "Freizeit.Gebaeude",
            "Gebaeude_StadtFirma",
            "Gewerbe.Gebaeude",
            "Gewerbe_V1.Firmen.Firma",
            "Kantonale_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Staedtisches_Gewerbe_V1.Firmen.Firma",
            "Strasse",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Kantonale_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Gewerbe_V1.Firmen.Firma",
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 9

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {"Strasse", "Freizeit.Gebaeude", "Gewerbe.Gebaeude"}

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Staedtisches_Gewerbe_V1.Firmen.Firma",
            "Gebaeude_StadtFirma",
            "BesitzerIn",
        }

        base_group = root.findGroup("base layers")
        assert base_group

        grouped_base_layers = {
            l.name() for l in base_group.children() if isinstance(l, QgsLayerTreeLayer)
        }

        assert grouped_base_layers == {
            "Kantonale_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
        }

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 10

        # strasse should only have relation editors to relevant layers (2/4)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and two relation editors
                assert len(efc.tabs()) == 3
                for tab in efc.tabs():
                    if tab.name() == "stadtscng_v1_1freizeit_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "stadtscng_v1_1gewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if (
                        tab.name() == "kantnl_ng_v1_1konstruktionen_gebaeude"
                    ):  # should not happen
                        count += 1
                    if tab.name() == "gebaeude":  # should not happen
                        count += 1
        # should find only 2
        assert count == 2

        QgsProject.instance().clear()

    def _extopt_staedtische_hide(self, generator, strategy):

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]

        # ambiguous aliases exist, since we don't rename them when they are hidden anyway
        assert len(ambiguous_aliases) == 4
        expected_aliases = [
            "BesitzerIn",
            "Freizeit.Gebaeude",
            "Gebaeude_StadtFirma",
            "Gewerbe.Gebaeude",
            "Konstruktionen.Gebaeude",
            "Firma",
            "Strasse",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Kantonale_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Gewerbe_V1.Firmen.Firma",
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 6

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {"Strasse", "Freizeit.Gebaeude", "Gewerbe.Gebaeude"}

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {"Firma", "Gebaeude_StadtFirma", "BesitzerIn"}

        # check relations - only 13 are here
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 6

        # strasse should only have relation editors to relevant layers (2/4)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and two relation editors
                assert len(efc.tabs()) == 3
                for tab in efc.tabs():
                    if tab.name() == "stadtscng_v1_1freizeit_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "stadtscng_v1_1gewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if (
                        tab.name() == "kantnl_ng_v1_1konstruktionen_gebaeude"
                    ):  # should not happen
                        count += 1
                    if tab.name() == "gebaeude":  # should not happen
                        count += 1
        # should find only 2
        assert count == 2

    def test_extopt_polymorphic_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Polymorphic_Ortsplanung_V1_1.ili"
        )
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

        ### 1. OptimizeStrategy.NONE ###
        strategy = OptimizeStrategy.NONE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            schema=importer.configuration.dbschema,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            schema=importer.configuration.dbschema,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            schema=importer.configuration.dbschema,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic_hide(generator, strategy)

    def test_extopt_polymorphic_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Polymorphic_Ortsplanung_V1_1.ili"
        )
        importer.configuration.ilimodels = "Polymorphic_Ortsplanung_V1_1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_optimal_polymorph_{:%Y%m%d%H%M%S%f}.gpkg".format(
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
        )

        self._extopt_polymorphic_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic_hide(generator, strategy)

    def test_extopt_polymorphic_mssql(self):
        return  # to do
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Polymorphic_Ortsplanung_V1_1.ili"
        )
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

        ### 1. OptimizeStrategy.NONE ###
        strategy = OptimizeStrategy.NONE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic_hide(generator, strategy)

    def _extopt_polymorphic_none(self, generator, strategy):
        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases = [
            "BesitzerIn",
            "Freizeit.Gebaeude",
            "Gewerbe.Gebaeude",
            "Hallen.Gebaeude",
            "IndustrieGewerbe.Gebaeude",
            "Markthalle",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Strasse",
            "TurnhalleTyp1",
            "TurnhalleTyp2",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude"
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 11

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {
            "IndustrieGewerbe.Gebaeude",
            "Strasse",
            "Freizeit.Gebaeude",
            "Markthalle",
            "TurnhalleTyp2",
            "Hallen.Gebaeude",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "TurnhalleTyp1",
            "Gewerbe.Gebaeude",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "BesitzerIn",
        }

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 16

        # strasse should have relation editors to all layers (8/8)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 9
                for tab in efc.tabs():
                    if tab.name() == "gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1gewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1freizeit_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1industriegewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1hallen_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "markthalle":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "turnhalletyp1":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "turnhalletyp2":
                        count += 1
                        assert len(tab.children()) == 1
        # should find 8
        assert count == 8

        QgsProject.instance().clear()

    def _extopt_polymorphic_group(self, generator, strategy):

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases = [
            "BesitzerIn",
            "Freizeit.Gebaeude",
            "Gewerbe.Gebaeude",
            "Hallen.Gebaeude",
            "IndustrieGewerbe.Gebaeude",
            "Markthalle",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Strasse",
            "TurnhalleTyp1",
            "TurnhalleTyp2",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude"
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 11

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {
            "IndustrieGewerbe.Gebaeude",
            "Strasse",
            "Freizeit.Gebaeude",
            "Markthalle",
            "TurnhalleTyp2",
            "Hallen.Gebaeude",
            "TurnhalleTyp1",
            "Gewerbe.Gebaeude",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "BesitzerIn",
        }

        base_group = root.findGroup("base layers")
        assert base_group

        grouped_base_layers = {
            l.name() for l in base_group.children() if isinstance(l, QgsLayerTreeLayer)
        }

        assert grouped_base_layers == {"Ortsplanung_V1_1.Konstruktionen.Gebaeude"}

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 16

        # strasse should have relation editors to all layers (8/8)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 8
                for tab in efc.tabs():
                    if tab.name() == "gebaeude":  # this should not happen
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1gewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1freizeit_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1industriegewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1hallen_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "markthalle":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "turnhalletyp1":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "turnhalletyp2":
                        count += 1
                        assert len(tab.children()) == 1
        # should find 7
        assert count == 7

        QgsProject.instance().clear()

    def _extopt_polymorphic_hide(self, generator, strategy):

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]

        # ambiguous aliases exist, since we don't rename them when they are hidden anyway
        assert len(ambiguous_aliases) == 2
        expected_aliases = [
            "BesitzerIn",
            "Freizeit.Gebaeude",
            "Gewerbe.Gebaeude",
            "Hallen.Gebaeude",
            "IndustrieGewerbe.Gebaeude",
            "Markthalle",
            "Konstruktionen.Gebaeude",
            "Strasse",
            "TurnhalleTyp1",
            "TurnhalleTyp2",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude"
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 10

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {
            "IndustrieGewerbe.Gebaeude",
            "Strasse",
            "Freizeit.Gebaeude",
            "Markthalle",
            "TurnhalleTyp2",
            "Hallen.Gebaeude",
            "TurnhalleTyp1",
            "Gewerbe.Gebaeude",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {"Konstruktionen.Gebaeude", "BesitzerIn"}

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 14

        # strasse should have relation editors to all layers (8/8)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 8
                for tab in efc.tabs():
                    if tab.name() == "gebaeude":  # this should not happen
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1gewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1freizeit_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1industriegewerbe_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "polymrpng_v1_1hallen_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "markthalle":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "turnhalletyp1":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "turnhalletyp2":
                        count += 1
                        assert len(tab.children()) == 1
        # should find 7
        assert count == 7

        QgsProject.instance().clear()

    def test_extopt_baustruct_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Kantonale_Bauplanung_V1_1.ili"
        )
        importer.configuration.ilimodels = "Kantonale_Bauplanung_V1_1"
        importer.configuration.dbschema = "optimal_baustruct_{:%Y%m%d%H%M%S%f}".format(
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
            optimize_strategy=strategy,
        )

        self._extopt_baustruct_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct_hide(generator, strategy)

    def test_extopt_baustruct_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Kantonale_Bauplanung_V1_1.ili"
        )
        importer.configuration.ilimodels = "Kantonale_Bauplanung_V1_1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_optimal_baustruct_{:%Y%m%d%H%M%S%f}.gpkg".format(
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
        )

        self._extopt_baustruct_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct_hide(generator, strategy)

    def test_extopt_baustruct_mssql(self):
        return  # to do
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/Kantonale_Bauplanung_V1_1.ili"
        )
        importer.configuration.ilimodels = "Kantonale_Bauplanung_V1_1"
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

        ### 1. OptimizeStrategy.NONE ###
        strategy = OptimizeStrategy.NONE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct_none(generator, strategy)

        ### 2. OptimizeStrategy.GROUP ###
        strategy = OptimizeStrategy.GROUP

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct_group(generator, strategy)

        ### 3. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct_hide(generator, strategy)

    def _extopt_baustruct_none(self, generator, strategy):
        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)
        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases = [
            "Strasse",
            "Sonnenblumenfeld",
            "Kartoffelfeld",
            "KantonaleBuntbrache",
            "Kantonale_Bauplanung_V1_1.Natur.Park",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Feld",
            "Buntbrache",
            "Brutstelle",
            "Kantonale_Bauplanung_V1_1.Natur.Tierart",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Park",
            "Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Tierart",
            "Bauart",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Bauplanung_V1_1.Natur.Park",
            "Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Tierart",
            "Bauplanung_V1_1.Natur.Feld",  # because extended multiple times
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 18

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Kantonale_Bauplanung_V1_1.Natur.Park",
            "Strasse",
            "Bauplanung_V1_1.Natur.Park",
            "Sonnenblumenfeld",
            "Buntbrache",
            "Brutstelle",
            "KantonaleBuntbrache",
            "Feld",
            "Kartoffelfeld",
            "Bauplanung_V1_1.Konstruktionen.Gebaeude",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Bauart",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Kantonale_Bauplanung_V1_1.Natur.Tierart",
            "Bauplanung_V1_1.Konstruktionen.Material",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Tierart",
        }

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 18

        # strasse should have relation editors to all layers (2/2)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 4
                for tab in efc.tabs():
                    if tab.name() == "kantnl_ng_v1_1konstruktionen_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
        # should find 3 (one times gebaeude and two times kantnl_ng_v1_1konstruktionen_gebaeude because it's extended)
        assert count == 3

        QgsProject.instance().clear()

    def _extopt_baustruct_group(self, generator, strategy):

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]

        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0
        expected_aliases = [
            "Strasse",
            "Sonnenblumenfeld",
            "Kartoffelfeld",
            "KantonaleBuntbrache",
            "Kantonale_Bauplanung_V1_1.Natur.Park",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Feld",
            "Buntbrache",
            "Brutstelle",
            "Kantonale_Bauplanung_V1_1.Natur.Tierart",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Park",
            "Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Tierart",
            "Bauart",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Bauplanung_V1_1.Natur.Park",
            "Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Tierart",
            "Bauplanung_V1_1.Natur.Feld",  # because extended multiple times
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 18

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Kantonale_Bauplanung_V1_1.Natur.Park",
            "Strasse",
            "Sonnenblumenfeld",
            "Buntbrache",
            "Brutstelle",
            "KantonaleBuntbrache",
            "Kartoffelfeld",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Bauart",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Kantonale_Bauplanung_V1_1.Natur.Tierart",
            "Kantonale_Bauplanung_V1_1.Konstruktionen.Material",
        }

        base_group = root.findGroup("base layers")
        assert base_group

        grouped_base_layers = {
            l.name() for l in base_group.children() if isinstance(l, QgsLayerTreeLayer)
        }

        assert grouped_base_layers == {
            "Bauplanung_V1_1.Natur.Park",
            "Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Feld",
        }

        base_table_group = base_group.findGroup("base tables")
        assert base_table_group

        grouped_base_tables = {
            l.name()
            for l in base_table_group.children()
            if isinstance(l, QgsLayerTreeLayer)
        }

        assert grouped_base_tables == {
            "Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Tierart",
        }

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 18

        # strasse should have relation editors to all layers (3/2) - since extended relation it's two times
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 2
                for tab in efc.tabs():
                    if tab.name() == "kantnl_ng_v1_1konstruktionen_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "gebaeude":  # this should not happen
                        count += 1
                        assert len(tab.children()) == 1
        # should find 1 (one times kantnl_ng_v1_1konstruktionen_gebaeude)
        assert count == 1

        QgsProject.instance().clear()

    def _extopt_baustruct_hide(self, generator, strategy):

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers]
        irrelevant_layer_ilinames = [
            l.ili_name for l in available_layers if not l.is_relevant
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]

        # ambiguous aliases exist, since we don't rename them when they are hidden anyway
        assert len(ambiguous_aliases) == 10
        expected_aliases = [
            "Strasse",
            "Sonnenblumenfeld",
            "Kartoffelfeld",
            "KantonaleBuntbrache",
            "Park",
            "Gebaeude",
            "Buntbrache",
            "Brutstelle",
            "Tierart",
            "Strassen_Gebaeude",
            "Material",
            "Bauart",
            "Feld",
        ]
        assert set(aliases) == set(expected_aliases)

        # irrelevant layers are detected
        assert len(irrelevant_layer_ilinames) > 0
        expected_irrelevant_layer_ilinames = [
            "Bauplanung_V1_1.Natur.Park",
            "Bauplanung_V1_1.Konstruktionen.Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Strassen_Gebaeude",
            "Bauplanung_V1_1.Konstruktionen.Material",
            "Bauplanung_V1_1.Natur.Tierart",
            "Bauplanung_V1_1.Natur.Feld",  # because extended multiple times
        ]
        assert set(irrelevant_layer_ilinames) == set(expected_irrelevant_layer_ilinames)

        project = Project(optimize_strategy=strategy)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        all_layers = root.findLayers()
        assert len(all_layers) == 12

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {
            "Gebaeude",
            "Park",
            "Strasse",
            "Park",
            "Sonnenblumenfeld",
            "Buntbrache",
            "Brutstelle",
            "KantonaleBuntbrache",
            "Kartoffelfeld",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {"Bauart", "Strassen_Gebaeude", "Tierart", "Material"}

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 7

        # strasse should have relation editors to only relevant layers
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 2
                for tab in efc.tabs():
                    if tab.name() == "kantnl_ng_v1_1konstruktionen_gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
                    if tab.name() == "gebaeude":  # this should not happen
                        count += 1
                        assert len(tab.children()) == 1
        # should find 1 (one times kantnl_ng_v1_1konstruktionen_gebaeude)
        assert count == 1

        QgsProject.instance().clear()

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()
