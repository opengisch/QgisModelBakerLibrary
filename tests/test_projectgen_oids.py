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
 *   the Free Software Foundation either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import datetime
import logging
import os
import pathlib
import tempfile

from qgis.core import QgsExpressionContextUtils, QgsProject
from qgis.testing import start_app, unittest

from modelbaker.dataobjects.project import Project
from modelbaker.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.utils.globals import OptimizeStrategy
from modelbaker.utils.qgis_utils import QgisProjectUtils
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
        importer.configuration.ilifile = testdata_path("ilimodels/OIDMadness_V1.ili")
        importer.configuration.ilimodels = "OIDMadness_V1"
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

        project = Project(
            optimize_strategy=strategy,
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # values
        t_id_name = "T_Id" if not_pg else "t_id"
        t_ili_tid_name = "T_Ili_Tid" if not_pg else "t_ili_tid"
        expected_uuid_expression = "uuid('WithoutBraces')"
        expected_i32_expression = t_id_name
        expected_standard_expression = f"'ch100000' || lpad( {t_id_name}, 8, 0 )"
        expected_other_expression = "'_' || uuid('WithoutBraces')"

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        tree_layers = root.findLayers()
        assert len(tree_layers) == 17

        count = 0
        for tree_layer in tree_layers:
            # with none
            if tree_layer.layer().name() in [
                "Parzellenidentifikation",
                "Gartenhaus",
                "Park",
            ]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == ""

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1
            # ANYOID
            if tree_layer.layer().name() in ["BesitzerIn"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.ANYOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1
            # UUIDOID
            if tree_layer.layer().name() in [
                "Wohnraum.Gebaeude",
                "Quartier.Gebaeude",
                "Wald",
            ]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.UUIDOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == expected_uuid_expression
                count += 1
            # STANARDOID
            if tree_layer.layer().name() in [
                "Brache",
                "Business.Gebaeude",
                "Parkplatz",
                "Spielplatz",
            ]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.STANDARDOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == expected_standard_expression
                )
                count += 1
            # I32OID
            if tree_layer.layer().name() in ["Wiese", "Spass.Gebaeude"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.I32OID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == expected_i32_expression
                count += 1
            # OIDMadness_V1.TypeID or OIDMadness_V1.TypeIDShort
            if tree_layer.layer().name() in ["See", "Fluss"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain in [
                    "OIDMadness_V1.TypeID",
                    "OIDMadness_V1.TypeIDShort",
                ]

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1

        # should find 15
        assert count == 15

        # check oid settings getter
        oid_settings = QgisProjectUtils(qgis_project).get_oid_settings()

        # change expression of Parkplatz
        oid_settings["Parkplatz"][
            "default_value_expression"
        ] = f"'chMBaker' || lpad( {t_id_name}, 8, 0 )"
        # change expression of See
        oid_settings["See"][
            "default_value_expression"
        ] = "'MB' || uuid('WithoutBraces')"
        # exponate t_ili_tid to form of BesitzerIn
        oid_settings["BesitzerIn"]["in_form"] = True

        QgisProjectUtils(QgsProject.instance()).set_oid_settings(oid_settings)

        # check layertree again
        qgis_project = QgsProject.instance()
        root = qgis_project.layerTreeRoot()
        assert root is not None

        tree_layers = root.findLayers()
        assert len(tree_layers) == 17

        count = 0
        for tree_layer in tree_layers:
            if tree_layer.layer().name() == "Parkplatz":
                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == f"'chMBaker' || lpad( {t_id_name}, 8, 0 )"
                )
                count += 1
            if tree_layer.layer().name() == "See":
                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "'MB' || uuid('WithoutBraces')"
                )
                count += 1
            if tree_layer.layer().name() == "BesitzerIn":
                # have look at the widgets in first tab "General"
                # t_ili_tid should be here now
                expected_widgets_in_general_tab = {
                    "t_basket",
                    "vorname",
                    "nachname",
                    "t_ili_tid",
                }

                efc = tree_layer.layer().editFormConfig()
                root_container = efc.invisibleRootContainer()
                assert root_container.children()

                assert expected_widgets_in_general_tab == {
                    child.name().lower()
                    for child in root_container.children()[0].children()
                }
                count += 1
        assert count == 3

        QgsProject.instance().clear()

    def _oids_tids_group(self, generator, strategy, not_pg=False):

        project = Project(
            optimize_strategy=strategy,
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        tree_layers = root.findLayers()
        assert len(tree_layers) == 17

        t_id_name = "T_Id" if not_pg else "t_id"
        t_ili_tid_name = "T_Ili_Tid" if not_pg else "t_ili_tid"
        expected_uuid_expression = "uuid('WithoutBraces')"
        expected_i32_expression = t_id_name
        expected_standard_expression = f"'ch100000' || lpad( {t_id_name}, 8, 0 )"
        expected_other_expression = "'_' || uuid('WithoutBraces')"

        count = 0
        for tree_layer in tree_layers:
            # with none
            if tree_layer.layer().name() in [
                "Parzellenidentifikation",
                "Gartenhaus",
                "Park",
            ]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == ""

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1
            # ANYOID
            if tree_layer.layer().name() in ["BesitzerIn"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.ANYOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1
            # UUIDOID
            if tree_layer.layer().name() in [
                "Wohnraum.Gebaeude",
                "Quartier.Gebaeude",
                "Wald",
            ]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.UUIDOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == expected_uuid_expression
                count += 1
            # STANARDOID
            if tree_layer.layer().name() in [
                "Brache",
                "Business.Gebaeude",
                "Parkplatz",
                "Spielplatz",
            ]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.STANDARDOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == expected_standard_expression
                )
                count += 1
            # I32OID
            if tree_layer.layer().name() in ["Wiese", "Spass.Gebaeude"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.I32OID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == expected_i32_expression
                count += 1
            # OIDMadness_V1.TypeID or OIDMadness_V1.TypeIDShort
            if tree_layer.layer().name() in ["See", "Fluss"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain in [
                    "OIDMadness_V1.TypeID",
                    "OIDMadness_V1.TypeIDShort",
                ]

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1

        # should find 15
        assert count == 15

        # check oid settings getter
        oid_settings = QgisProjectUtils(qgis_project).get_oid_settings()

        # change expression of Parkplatz
        oid_settings["Parkplatz"][
            "default_value_expression"
        ] = f"'chMBaker' || lpad( {t_id_name}, 8, 0 )"
        # change expression of See
        oid_settings["See"][
            "default_value_expression"
        ] = "'MB' || uuid('WithoutBraces')"
        # exponate t_ili_tid to form of BesitzerIn
        oid_settings["BesitzerIn"]["in_form"] = True

        QgisProjectUtils(QgsProject.instance()).set_oid_settings(oid_settings)

        # check layertree again
        qgis_project = QgsProject.instance()
        root = qgis_project.layerTreeRoot()
        assert root is not None

        tree_layers = root.findLayers()
        assert len(tree_layers) == 17

        count = 0
        for tree_layer in tree_layers:
            if tree_layer.layer().name() == "Parkplatz":
                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == f"'chMBaker' || lpad( {t_id_name}, 8, 0 )"
                )
                count += 1
            if tree_layer.layer().name() == "See":
                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "'MB' || uuid('WithoutBraces')"
                )
                count += 1
            if tree_layer.layer().name() == "BesitzerIn":
                # have look at the widgets in first tab "General"
                # t_ili_tid should be here now
                expected_widgets_in_general_tab = {
                    "t_basket",
                    "vorname",
                    "nachname",
                    "t_ili_tid",
                }

                efc = tree_layer.layer().editFormConfig()
                root_container = efc.invisibleRootContainer()
                assert root_container.children()

                assert expected_widgets_in_general_tab == {
                    child.name().lower()
                    for child in root_container.children()[0].children()
                }

                count += 1
        assert count == 3
        QgsProject.instance().clear()

    def _oids_tids_hide(self, generator, strategy, not_pg=False):

        project = Project(
            optimize_strategy=strategy,
            context={"catalogue_datasetname": CATALOGUE_DATASETNAME},
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check layertree
        root = qgis_project.layerTreeRoot()
        assert root is not None

        tree_layers = root.findLayers()
        assert len(tree_layers) == 16

        t_id_name = "T_Id" if not_pg else "t_id"
        t_ili_tid_name = "T_Ili_Tid" if not_pg else "t_ili_tid"
        expected_uuid_expression = "uuid('WithoutBraces')"
        expected_i32_expression = t_id_name
        expected_standard_expression = f"'ch100000' || lpad( {t_id_name}, 8, 0 )"
        expected_other_expression = "'_' || uuid('WithoutBraces')"

        # "Wohnraum.Gebaeude" is hidden because of the strategy
        count = 0
        for tree_layer in tree_layers:
            # with none
            if tree_layer.layer().name() in [
                "Parzellenidentifikation",
                "Gartenhaus",
                "Park",
            ]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == ""

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1
            # ANYOID
            if tree_layer.layer().name() in ["BesitzerIn"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.ANYOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1
            # UUIDOID
            if tree_layer.layer().name() in ["Quartier.Gebaeude", "Wald"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.UUIDOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == expected_uuid_expression
                count += 1
            # STANARDOID
            if tree_layer.layer().name() in [
                "Brache",
                "Business.Gebaeude",
                "Parkplatz",
                "Spielplatz",
            ]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.STANDARDOID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == expected_standard_expression
                )
                count += 1
            # I32OID
            if tree_layer.layer().name() in ["Wiese", "Spass.Gebaeude"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain == "INTERLIS.I32OID"

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == expected_i32_expression
                count += 1
            # OIDMadness_V1.TypeID or OIDMadness_V1.TypeIDShort
            if tree_layer.layer().name() in ["See", "Fluss"]:
                # check layer variable
                oid_domain = (
                    QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                        "oid_domain"
                    )
                    or ""
                )
                assert oid_domain in [
                    "OIDMadness_V1.TypeID",
                    "OIDMadness_V1.TypeIDShort",
                ]

                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression() == expected_other_expression
                )
                count += 1

        # should find 14
        assert count == 14

        # check oid settings getter
        oid_settings = QgisProjectUtils(qgis_project).get_oid_settings()

        # change expression of Parkplatz
        oid_settings["Parkplatz"][
            "default_value_expression"
        ] = f"'chMBaker' || lpad( {t_id_name}, 8, 0 )"
        # change expression of See
        oid_settings["See"][
            "default_value_expression"
        ] = "'MB' || uuid('WithoutBraces')"
        # exponate t_ili_tid to form of BesitzerIn
        oid_settings["BesitzerIn"]["in_form"] = True

        QgisProjectUtils(QgsProject.instance()).set_oid_settings(oid_settings)

        # check layertree again
        qgis_project = QgsProject.instance()
        root = qgis_project.layerTreeRoot()
        assert root is not None

        tree_layers = root.findLayers()
        assert len(tree_layers) == 16

        count = 0
        for tree_layer in tree_layers:
            if tree_layer.layer().name() == "Parkplatz":
                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == f"'chMBaker' || lpad( {t_id_name}, 8, 0 )"
                )
                count += 1
            if tree_layer.layer().name() == "See":
                # have look at the t_ili_tid field
                fields = tree_layer.layer().fields()
                field_idx = fields.lookupField(t_ili_tid_name)
                t_ili_tid_field = fields.field(field_idx)
                # check default value expression
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "'MB' || uuid('WithoutBraces')"
                )
                count += 1
            if tree_layer.layer().name() == "BesitzerIn":
                # have look at the widgets in first tab "General"
                # t_ili_tid should be here now
                expected_widgets_in_general_tab = {
                    "t_basket",
                    "vorname",
                    "nachname",
                    "t_ili_tid",
                }

                efc = tree_layer.layer().editFormConfig()
                root_container = efc.invisibleRootContainer()
                assert root_container.children()

                assert expected_widgets_in_general_tab == {
                    child.name().lower()
                    for child in root_container.children()[0].children()
                }
                count += 1
        assert count == 3

        QgsProject.instance().clear()

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()
