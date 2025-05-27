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

from qgis.core import QgsExpressionContextUtils, QgsLayerTreeLayer, QgsProject
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


class TestProjectExtOptimizationSmart1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    """
    Those tests check if:
    - possible t_types are detected
    # to do in next step: - irrelevant basetables are detected (according to the assumptions below)
    # to do in next step: - t_types of irrelevant basetables will not be provided on hide-strategy but they are on none-strategy (there is no group strategy on smart1)

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
        self._set_pg_naming()

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
        importer.configuration.inheritance = "smart1"
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

        self._extopt_staedtische(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._extopt_staedtische(generator, strategy)

    def test_extopt_staedtische_geopackage(self):
        self._set_pg_naming(False)

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
        importer.configuration.inheritance = "smart1"
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

        self._extopt_staedtische(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
            consider_basket_handling=True,
        )

        self._extopt_staedtische(generator, strategy)

    def test_extopt_staedtische_mssql(self):
        self._set_pg_naming(False)

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
        importer.configuration.inheritance = "smart1"
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

        self._extopt_staedtische(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._extopt_staedtische(generator, strategy)

    def _extopt_staedtische(self, generator, strategy):

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers if l.alias is not None]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]
        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0

        # check the layers - strategy should not have influence here
        expected_aliases = [
            "Strasse",
            "Gebaeude",
            "Gebaeude_StadtFirma",
            "BesitzerIn",
            "Firma",
        ]
        assert set(aliases) == set(expected_aliases)

        # check relevant topics
        count = 0
        for layer in available_layers:
            # Strasse from Infrastruktur_V1
            if layer.alias == "Strasse":
                count += 1
                assert layer.all_topics == ["Infrastruktur_V1.Strassen"]
                assert layer.relevant_topics == ["Infrastruktur_V1.Strassen"]
            # BesitzerIn from Ortsplanung_V1_1
            if layer.alias == "BesitzerIn":
                count += 1
                assert set(layer.all_topics) == {
                    "Kantonale_Ortsplanung_V1_1.Konstruktionen",
                    "Staedtische_Ortsplanung_V1_1.Freizeit",
                    "Staedtische_Ortsplanung_V1_1.Gewerbe",
                    "Ortsplanung_V1_1.Konstruktionen",
                }
                assert set(layer.relevant_topics) == {
                    "Staedtische_Ortsplanung_V1_1.Freizeit",
                    "Staedtische_Ortsplanung_V1_1.Gewerbe",
                }
            # Firma from Staedtisches_Gewerbe_V1 and Gewerbe_V1
            if layer.alias == "Firma":
                count += 1
                assert set(layer.all_topics) == {
                    "Staedtisches_Gewerbe_V1.Firmen",
                    "Gewerbe_V1.Firmen",
                }
                assert set(layer.relevant_topics) == {"Staedtisches_Gewerbe_V1.Firmen"}
        assert count == 3

        project = Project(
            optimize_strategy=strategy,
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
        )
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
        assert len(all_layers) == 7

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {"Strasse", "Gebaeude"}

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Firma",
            "Gebaeude_StadtFirma",
            "BesitzerIn",
        }

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 10

        # strasse should have relation editors to only one layer (that sums up all the possibilities)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 2
                for tab in efc.tabs():
                    if tab.name() == "Gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
        # should find 1
        assert count == 1

        # strasse can only be in it's dedicated basket (only instance of topic Infrastruktur_V1.Strassen)
        # besitzerin can be in multiple baskets (instances of topics Ortsplanung_V1_1.Konstruktionen, Kantonale_Ortsplanung_V1_1.Konstruktionen, Staedtische_Ortsplanung_V1_1.Freizeit, Staedtische_Ortsplanung_V1_1.Gewerbe)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                count += 1

                # check layer variable
                layer_model_topic_names = (
                    QgsExpressionContextUtils.layerScope(layer.layer).variable(
                        "interlis_topic"
                    )
                    or ""
                )

                assert layer_model_topic_names == "Infrastruktur_V1.Strassen"

                # have look at the basket field
                fields = layer.layer.fields()
                field_idx = fields.lookupField(self.basket_fieldname)
                t_basket_field = fields.field(field_idx)

                # check filter in widget
                ews = t_basket_field.editorWidgetSetup()
                map = ews.config()

                assert (
                    map["FilterExpression"]
                    == f"\"topic\" IN ('Infrastruktur_V1.Strassen') and attribute(get_feature('{self.dataset_tablename}', '{self.tid_fieldname}', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                )

                # check default value expression
                default_value_definition = t_basket_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "@default_basket_infrastruktur_v1_strassen"
                )

            if layer.layer.name() == "BesitzerIn":
                count += 1

                # check layer variable
                expected_layer_model_topic_names = (
                    "Staedtische_Ortsplanung_V1_1.Freizeit,Staedtische_Ortsplanung_V1_1.Gewerbe"
                    if strategy == OptimizeStrategy.HIDE
                    else "Kantonale_Ortsplanung_V1_1.Konstruktionen,Ortsplanung_V1_1.Konstruktionen,Staedtische_Ortsplanung_V1_1.Freizeit,Staedtische_Ortsplanung_V1_1.Gewerbe"
                )

                layer_model_topic_names = (
                    QgsExpressionContextUtils.layerScope(layer.layer).variable(
                        "interlis_topic"
                    )
                    or ""
                )

                assert layer_model_topic_names == expected_layer_model_topic_names

                # have look at the basket field
                fields = layer.layer.fields()
                field_idx = fields.lookupField(self.basket_fieldname)
                t_basket_field = fields.field(field_idx)

                # check filter in widget
                ews = t_basket_field.editorWidgetSetup()
                map = ews.config()

                expected_filter_expression = (
                    f"\"topic\" IN ('Staedtische_Ortsplanung_V1_1.Freizeit','Staedtische_Ortsplanung_V1_1.Gewerbe') and attribute(get_feature('{self.dataset_tablename}', '{self.tid_fieldname}', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                    if strategy == OptimizeStrategy.HIDE
                    else f"\"topic\" IN ('Kantonale_Ortsplanung_V1_1.Konstruktionen','Ortsplanung_V1_1.Konstruktionen','Staedtische_Ortsplanung_V1_1.Freizeit','Staedtische_Ortsplanung_V1_1.Gewerbe') and attribute(get_feature('{self.dataset_tablename}', '{self.tid_fieldname}', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                )
                assert map["FilterExpression"] == expected_filter_expression

                # check default value expression
                default_value_definition = t_basket_field.defaultValueDefinition()
                assert default_value_definition is not None
                expected_default_value_expression = (
                    "@default_basket_staedtische_ortsplanung_v1_1_freizeit_staedtische_ortsplanung_v1_1_gewerbe"
                    if strategy == OptimizeStrategy.HIDE
                    else "@default_basket_kantonale_ortsplanung_v1_1_konstruktionen_ortsplanung_v1_1_konstruktionen_staedtische_ortsplanung_v1_1_freizeit_staedtische_ortsplanung_v1_1_gewerbe"
                )
                assert (
                    default_value_definition.expression()
                    == expected_default_value_expression
                )

        # should find 2
        assert count == 2

        # Strasse should not have a t_type column
        # Gebaeude should have a t_type with all possible entries
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                count += 1
                value_map = layer.layer.editFormConfig().widgetConfig(
                    self.type_fieldname
                )

                assert not value_map

            if layer.layer.name() == "Gebaeude":
                count += 1
                value_map = layer.layer.editFormConfig().widgetConfig(
                    self.type_fieldname
                )
                assert value_map

                expected_values = (
                    {
                        "stadtscng_v1_1freizeit_gebaeude",
                        "stadtscng_v1_1gewerbe_gebaeude",
                    }
                    if strategy == OptimizeStrategy.HIDE
                    else {
                        "gebaeude",
                        "stadtscng_v1_1freizeit_gebaeude",
                        "kantnl_ng_v1_1konstruktionen_gebaeude",
                        "stadtscng_v1_1gewerbe_gebaeude",
                    }
                )

                values = {next(iter(entry.values())) for entry in value_map["map"]}
                assert values == expected_values

                expected_keys = (
                    {
                        "Staedtische_Ortsplanung_V1_1.Freizeit.Gebaeude",
                        "Staedtische_Ortsplanung_V1_1.Gewerbe.Gebaeude",
                    }
                    if strategy == OptimizeStrategy.HIDE
                    else {
                        "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
                        "Staedtische_Ortsplanung_V1_1.Freizeit.Gebaeude",
                        "Kantonale_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
                        "Staedtische_Ortsplanung_V1_1.Gewerbe.Gebaeude",
                    }
                )
                keys = {next(iter(entry)) for entry in value_map["map"]}
                assert keys == expected_keys

        # should find 2
        assert count == 2

        QgsProject.instance().clear()

    def test_extopt_polymorphic_postgis(self):
        self._set_pg_naming()

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
        importer.configuration.inheritance = "smart1"
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
            consider_basket_handling=True,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic(generator, strategy)

    def test_extopt_polymorphic_geopackage(self):
        self._set_pg_naming(False)

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
        importer.configuration.inheritance = "smart1"
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

        self._extopt_polymorphic(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
            consider_basket_handling=True,
        )

        self._extopt_polymorphic(generator, strategy)

    def test_extopt_polymorphic_mssql(self):
        self._set_pg_naming(False)

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
        importer.configuration.inheritance = "smart1"
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

        self._extopt_polymorphic(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._extopt_polymorphic(generator, strategy)

    def _extopt_polymorphic(self, generator, strategy):
        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers if l.alias is not None]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]
        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0

        expected_aliases = [
            "BesitzerIn",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "Strasse",
            "TurnhalleTyp1",
            "TurnhalleTyp2",
        ]
        assert set(aliases) == set(expected_aliases)

        # check relevant topics
        count = 0
        for layer in available_layers:
            # Strasse from Infrastruktur_V1
            if layer.alias == "Strasse":
                count += 1
                assert layer.all_topics == ["Infrastruktur_V1.Strassen"]
                assert layer.relevant_topics == ["Infrastruktur_V1.Strassen"]
            # BesitzerIn from Ortsplanung_V1_1
            if layer.alias == "BesitzerIn":
                count += 1
                assert set(layer.all_topics) == {
                    "Polymorphic_Ortsplanung_V1_1.Gewerbe",
                    "Polymorphic_Ortsplanung_V1_1.Freizeit",
                    "Polymorphic_Ortsplanung_V1_1.Hallen",
                    "Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe",
                    "Ortsplanung_V1_1.Konstruktionen",
                }
                assert set(layer.relevant_topics) == {
                    "Polymorphic_Ortsplanung_V1_1.Gewerbe",
                    "Polymorphic_Ortsplanung_V1_1.Freizeit",
                    "Polymorphic_Ortsplanung_V1_1.Hallen",
                    "Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe",
                }
            # Gebaeude from Ortsplanung_V1_1
            if layer.alias == "Ortsplanung_V1_1.Konstruktionen.Gebaeude":
                count += 1
                assert set(layer.all_topics) == {
                    "Polymorphic_Ortsplanung_V1_1.Gewerbe",
                    "Polymorphic_Ortsplanung_V1_1.Freizeit",
                    "Polymorphic_Ortsplanung_V1_1.Hallen",
                    "Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe",
                    "Ortsplanung_V1_1.Konstruktionen",
                }
                assert set(layer.relevant_topics) == {
                    "Polymorphic_Ortsplanung_V1_1.Gewerbe",
                    "Polymorphic_Ortsplanung_V1_1.Freizeit",
                    "Polymorphic_Ortsplanung_V1_1.Hallen",
                    "Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe",
                }

        assert count == 3

        project = Project(
            optimize_strategy=strategy,
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
        )
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
        assert len(all_layers) == 8

        geometry_layers = {
            l.name() for l in root.children() if isinstance(l, QgsLayerTreeLayer)
        }
        assert geometry_layers == {
            "Strasse",
            "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Polymorphic_Ortsplanung_V1_1.Konstruktionen.Gebaeude",
            "BesitzerIn",
            "TurnhalleTyp1",
            "TurnhalleTyp2",
        }

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 11

        # strasse should have relation editors only to gebaeude (1)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 2
                for tab in efc.tabs():
                    if tab.name() == "Ortsplanung_V1_1.Konstruktionen.Gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
        # should find 1
        assert count == 1

        # strasse can only be in it's dedicated basket (only instance of topic Infrastruktur_V1.Strassen)
        # besitzerin can be in multiple baskets (instances of topics 'Polymorphic_Ortsplanung_V1_1.Gewerbe','Polymorphic_Ortsplanung_V1_1.Freizeit','Polymorphic_Ortsplanung_V1_1.Hallen','Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe','Ortsplanung_V1_1.Konstruktionen')
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                count += 1

                # check layer variable
                layer_model_topic_names = (
                    QgsExpressionContextUtils.layerScope(layer.layer).variable(
                        "interlis_topic"
                    )
                    or ""
                )

                assert layer_model_topic_names == "Infrastruktur_V1.Strassen"

                # have look at the basket field
                fields = layer.layer.fields()
                field_idx = fields.lookupField(self.basket_fieldname)
                t_basket_field = fields.field(field_idx)

                # check filter in widget
                ews = t_basket_field.editorWidgetSetup()
                map = ews.config()

                assert (
                    map["FilterExpression"]
                    == f"\"topic\" IN ('Infrastruktur_V1.Strassen') and attribute(get_feature('{self.dataset_tablename}', '{self.tid_fieldname}', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                )

                # check default value expression
                default_value_definition = t_basket_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "@default_basket_infrastruktur_v1_strassen"
                )

            if layer.layer.name() == "BesitzerIn":
                count += 1

                # check layer variable
                expected_layer_model_topic_names = (
                    "Polymorphic_Ortsplanung_V1_1.Freizeit,Polymorphic_Ortsplanung_V1_1.Gewerbe,Polymorphic_Ortsplanung_V1_1.Hallen,Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe"
                    if strategy == OptimizeStrategy.HIDE
                    else "Ortsplanung_V1_1.Konstruktionen,Polymorphic_Ortsplanung_V1_1.Freizeit,Polymorphic_Ortsplanung_V1_1.Gewerbe,Polymorphic_Ortsplanung_V1_1.Hallen,Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe"
                )
                layer_model_topic_names = (
                    QgsExpressionContextUtils.layerScope(layer.layer).variable(
                        "interlis_topic"
                    )
                    or ""
                )

                assert layer_model_topic_names == expected_layer_model_topic_names

                # have look at the basket field
                fields = layer.layer.fields()
                field_idx = fields.lookupField(self.basket_fieldname)
                t_basket_field = fields.field(field_idx)

                # check filter in widget
                ews = t_basket_field.editorWidgetSetup()
                map = ews.config()

                expected_filter_expression = (
                    f"\"topic\" IN ('Polymorphic_Ortsplanung_V1_1.Freizeit','Polymorphic_Ortsplanung_V1_1.Gewerbe','Polymorphic_Ortsplanung_V1_1.Hallen','Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe') and attribute(get_feature('{self.dataset_tablename}', '{self.tid_fieldname}', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                    if strategy == OptimizeStrategy.HIDE
                    else f"\"topic\" IN ('Ortsplanung_V1_1.Konstruktionen','Polymorphic_Ortsplanung_V1_1.Freizeit','Polymorphic_Ortsplanung_V1_1.Gewerbe','Polymorphic_Ortsplanung_V1_1.Hallen','Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe') and attribute(get_feature('{self.dataset_tablename}', '{self.tid_fieldname}', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                )
                assert map["FilterExpression"] == expected_filter_expression

                # check default value expression
                default_value_definition = t_basket_field.defaultValueDefinition()
                assert default_value_definition is not None
                expected_default_expression = (
                    "@default_basket_polymorphic_ortsplanung_v1_1_freizeit_polymorphic_ortsplanung_v1_1_gewerbe_polymorphic_ortsplanung_v1_1_hallen_polymorphic_ortsplanung_v1_1_industriegewerbe"
                    if strategy == OptimizeStrategy.HIDE
                    else "@default_basket_ortsplanung_v1_1_konstruktionen_polymorphic_ortsplanung_v1_1_freizeit_polymorphic_ortsplanung_v1_1_gewerbe_polymorphic_ortsplanung_v1_1_hallen_polymorphic_ortsplanung_v1_1_industriegewerbe"
                )
                assert (
                    default_value_definition.expression() == expected_default_expression
                )

        # should find 2
        assert count == 2

        # Strasse should not have a t_type column
        # Ortsplanung_V1_1.Konstruktionen.Gebaeude should have a t_type with all possible entries
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                count += 1
                value_map = layer.layer.editFormConfig().widgetConfig(
                    self.type_fieldname
                )

                assert not value_map

            if layer.layer.name() == "Ortsplanung_V1_1.Konstruktionen.Gebaeude":
                count += 1
                value_map = layer.layer.editFormConfig().widgetConfig(
                    self.type_fieldname
                )
                assert value_map

                expected_values = (
                    {
                        "polymrpng_v1_1hallen_gebaeude",
                        "turnhalletyp2",
                        "polymrpng_v1_1gewerbe_gebaeude",
                        "polymrpng_v1_1industriegewerbe_gebaeude",
                        "turnhalletyp1",
                        "markthalle",
                        "polymrpng_v1_1freizeit_gebaeude",
                    }
                    if strategy == OptimizeStrategy.HIDE
                    else {
                        "polymrpng_v1_1hallen_gebaeude",
                        "turnhalletyp2",
                        "polymrpng_v1_1gewerbe_gebaeude",
                        "polymrpng_v1_1industriegewerbe_gebaeude",
                        "turnhalletyp1",
                        "gebaeude",
                        "markthalle",
                        "polymrpng_v1_1freizeit_gebaeude",
                    }
                )
                values = {next(iter(entry.values())) for entry in value_map["map"]}
                assert values == expected_values

                expected_keys = (
                    {
                        "Polymorphic_Ortsplanung_V1_1.Hallen.Gebaeude",
                        "Polymorphic_Ortsplanung_V1_1.Hallen.TurnhalleTyp2",
                        "Polymorphic_Ortsplanung_V1_1.Gewerbe.Gebaeude",
                        "Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe.Gebaeude",
                        "Polymorphic_Ortsplanung_V1_1.Hallen.TurnhalleTyp1",
                        "Polymorphic_Ortsplanung_V1_1.Hallen.Markthalle",
                        "Polymorphic_Ortsplanung_V1_1.Freizeit.Gebaeude",
                    }
                    if strategy == OptimizeStrategy.HIDE
                    else {
                        "Polymorphic_Ortsplanung_V1_1.Hallen.Gebaeude",
                        "Polymorphic_Ortsplanung_V1_1.Hallen.TurnhalleTyp2",
                        "Polymorphic_Ortsplanung_V1_1.Gewerbe.Gebaeude",
                        "Polymorphic_Ortsplanung_V1_1.IndustrieGewerbe.Gebaeude",
                        "Polymorphic_Ortsplanung_V1_1.Hallen.TurnhalleTyp1",
                        "Ortsplanung_V1_1.Konstruktionen.Gebaeude",
                        "Polymorphic_Ortsplanung_V1_1.Hallen.Markthalle",
                        "Polymorphic_Ortsplanung_V1_1.Freizeit.Gebaeude",
                    }
                )
                keys = {next(iter(entry)) for entry in value_map["map"]}
                assert keys == expected_keys

        # should find 2
        assert count == 2

        QgsProject.instance().clear()

    def test_extopt_baustruct_postgis(self):
        self._set_pg_naming()

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
        importer.configuration.inheritance = "smart1"
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

        self._extopt_baustruct(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2pg,
            uri=get_pg_connection_string(),
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct(generator, strategy)

    def test_extopt_baustruct_geopackage(self):
        self._set_pg_naming(False)

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
        importer.configuration.inheritance = "smart1"
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

        self._extopt_baustruct(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2gpkg,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            optimize_strategy=strategy,
            consider_basket_handling=True,
        )

        self._extopt_baustruct(generator, strategy)

    def test_extopt_baustruct_mssql(self):
        self._set_pg_naming(False)

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
        importer.configuration.inheritance = "smart1"
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

        self._extopt_baustruct(generator, strategy)

        ### 2. OptimizeStrategy.HIDE ###
        strategy = OptimizeStrategy.HIDE

        generator = Generator(
            tool=DbIliMode.ili2mssql,
            uri=uri,
            inheritance=importer.configuration.inheritance,
            schema=importer.configuration.dbschema,
            consider_basket_handling=True,
            optimize_strategy=strategy,
        )

        self._extopt_baustruct(generator, strategy)

    def _extopt_baustruct(self, generator, strategy):
        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        aliases = [l.alias for l in available_layers if l.alias is not None]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]
        # check no ambiguous layers exists
        assert len(ambiguous_aliases) == 0

        expected_aliases = [
            "Strasse",
            "Feld",
            "Buntbrache",
            "Park",
            "Gebaeude",
            "Buntbrache",
            "Brutstelle",
            "Tierart",
            "Strassen_Gebaeude",
            "Material",
            "Bauart",
        ]
        assert set(aliases) == set(expected_aliases)

        # check relevant topics
        count = 0
        for layer in available_layers:
            # Strasse from Infrastruktur_V1
            if layer.alias == "Strasse":
                count += 1
                assert layer.all_topics == ["Infrastruktur_V1.Strassen"]
                assert layer.relevant_topics == ["Infrastruktur_V1.Strassen"]
            # Park from Bauplanung_V1_1 and Kantonale_Bauplanung_V1_1
            if layer.alias == "Park":
                count += 1
                assert set(layer.all_topics) == {
                    "Bauplanung_V1_1.Natur",
                    "Kantonale_Bauplanung_V1_1.Natur",
                }
                assert set(layer.relevant_topics) == {"Kantonale_Bauplanung_V1_1.Natur"}
            # Feld from Bauplanung_V1_1
            if layer.alias == "Feld":
                count += 1
                assert set(layer.all_topics) == {
                    "Bauplanung_V1_1.Natur",
                    "Kantonale_Bauplanung_V1_1.Natur",
                }
                assert set(layer.relevant_topics) == {"Kantonale_Bauplanung_V1_1.Natur"}
        assert count == 3

        project = Project(
            optimize_strategy=strategy,
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
        )
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
            "Strasse",
            "Feld",
            "Buntbrache",
            "Brutstelle",
            "Park",
            "Gebaeude",
        }

        tables_layers = {l.name() for l in root.findGroup("tables").children()}
        assert tables_layers == {
            "Bauart",
            "Strassen_Gebaeude",
            "Tierart",
            "Material",
        }

        # check relations - all are there
        relations = list(qgis_project.relationManager().relations().values())
        assert len(relations) == 18

        # strasse should have relation editors to one layer (gebaeude) (1)
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                efc = layer.layer.editFormConfig()
                # one general and four relation editors
                assert len(efc.tabs()) == 2
                for tab in efc.tabs():
                    if tab.name() == "Strassen_Gebaeude":
                        count += 1
                        assert len(tab.children()) == 1
        # should find 1 (one times gebaeude)
        assert count == 1

        # strasse can only be in it's dedicated basket (only instance of topic Infrastruktur_V1.Strassen)
        # no special cases with multi basket layers...
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                count += 1

                # check layer variable
                layer_model_topic_names = (
                    QgsExpressionContextUtils.layerScope(layer.layer).variable(
                        "interlis_topic"
                    )
                    or ""
                )

                assert layer_model_topic_names == "Infrastruktur_V1.Strassen"

                # have look at the basket field
                fields = layer.layer.fields()
                field_idx = fields.lookupField(self.basket_fieldname)
                t_basket_field = fields.field(field_idx)

                # check filter in widget
                ews = t_basket_field.editorWidgetSetup()
                map = ews.config()

                assert (
                    map["FilterExpression"]
                    == f"\"topic\" IN ('Infrastruktur_V1.Strassen') and attribute(get_feature('{self.dataset_tablename}', '{self.tid_fieldname}', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                )

                # check default value expression
                default_value_definition = t_basket_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "@default_basket_infrastruktur_v1_strassen"
                )

        # should find 1
        assert count == 1

        # Strasse should not have a t_type column
        # Gebaeude should have a t_type with all possible entries
        # Buntbrache should have a t_type with all possible entries
        # Feld should have a t_type with all possible entries
        count = 0
        for layer in project.layers:
            if layer.layer.name() == "Strasse":
                count += 1
                value_map = layer.layer.editFormConfig().widgetConfig(
                    self.type_fieldname
                )

                assert not value_map

            if layer.layer.name() == "Gebaeude":
                count += 1
                value_map = layer.layer.editFormConfig().widgetConfig(
                    self.type_fieldname
                )
                assert value_map

                expected_values = (
                    {"kantnl_ng_v1_1konstruktionen_gebaeude"}
                    if strategy == OptimizeStrategy.HIDE
                    else {"gebaeude", "kantnl_ng_v1_1konstruktionen_gebaeude"}
                )

                values = {next(iter(entry.values())) for entry in value_map["map"]}
                assert values == expected_values

                expected_keys = (
                    {"Kantonale_Bauplanung_V1_1.Konstruktionen.Gebaeude"}
                    if strategy == OptimizeStrategy.HIDE
                    else {
                        "Bauplanung_V1_1.Konstruktionen.Gebaeude",
                        "Kantonale_Bauplanung_V1_1.Konstruktionen.Gebaeude",
                    }
                )
                keys = {next(iter(entry)) for entry in value_map["map"]}
                assert keys == expected_keys

            if layer.layer.name() == "Buntbrache":
                count += 1
                value_map = layer.layer.editFormConfig().widgetConfig(
                    self.type_fieldname
                )
                assert value_map

                expected_values = (
                    {"buntbrache", "kantonalebuntbrache"}
                    if strategy == OptimizeStrategy.HIDE
                    else {"buntbrache", "kantonalebuntbrache"}
                )
                values = {next(iter(entry.values())) for entry in value_map["map"]}
                assert values == expected_values

                expected_keys = (
                    {
                        "Bauplanung_V1_1.Natur.Buntbrache",
                        "Kantonale_Bauplanung_V1_1.Natur.KantonaleBuntbrache",
                    }
                    if strategy == OptimizeStrategy.HIDE
                    else {
                        "Bauplanung_V1_1.Natur.Buntbrache",
                        "Kantonale_Bauplanung_V1_1.Natur.KantonaleBuntbrache",
                    }
                )
                keys = {next(iter(entry)) for entry in value_map["map"]}
                assert keys == expected_keys

            if layer.layer.name() == "Feld":
                count += 1
                value_map = layer.layer.editFormConfig().widgetConfig(
                    self.type_fieldname
                )
                assert value_map

                expected_values = (
                    {"sonnenblumenfeld", "kartoffelfeld"}
                    if strategy == OptimizeStrategy.HIDE
                    else {"feld", "sonnenblumenfeld", "kartoffelfeld"}
                )
                values = {next(iter(entry.values())) for entry in value_map["map"]}
                assert values == expected_values

                expected_keys = (
                    {
                        "Kantonale_Bauplanung_V1_1.Natur.Kartoffelfeld",
                        "Kantonale_Bauplanung_V1_1.Natur.Sonnenblumenfeld",
                    }
                    if strategy == OptimizeStrategy.HIDE
                    else {
                        "Bauplanung_V1_1.Natur.Feld",
                        "Kantonale_Bauplanung_V1_1.Natur.Kartoffelfeld",
                        "Kantonale_Bauplanung_V1_1.Natur.Sonnenblumenfeld",
                    }
                )
                keys = {next(iter(entry)) for entry in value_map["map"]}
                assert keys == expected_keys

        # should find 4
        assert count == 4

        QgsProject.instance().clear()

    def _set_pg_naming(self, is_pg=True):
        if is_pg:
            self.dataset_tablename = "t_ili2db_dataset"
            self.basket_fieldname = "t_basket"
            self.type_fieldname = "t_type"
            self.tid_fieldname = "t_id"
        else:
            self.dataset_tablename = "T_ILI2DB_DATASET"
            self.basket_fieldname = "T_basket"
            self.type_fieldname = "T_Type"
            self.tid_fieldname = "T_Id"

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()
