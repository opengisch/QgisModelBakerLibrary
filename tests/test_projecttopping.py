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

import datetime
import logging
import os
import pathlib
import shutil
import tempfile

import yaml
from qgis.core import QgsEditFormConfig, QgsLayerTreeModel, QgsProject
from qgis.PyQt.QtCore import QEventLoop, Qt, QTimer
from qgis.testing import start_app, unittest

from modelbaker.dataobjects.project import Project
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.iliwrapper.ilicache import IliToppingFileCache
from tests.utils import get_pg_connection_string, iliimporter_config

start_app()

test_path = pathlib.Path(__file__).parent.absolute()

CATALOGUE_DATASETNAME = "Catset"


class TestProjectTopping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.toppings_test_path = os.path.join(
            test_path, "testdata", "ilirepo", "usabilityhub"
        )

    def test_kbs_postgis_qlr_layers(self):
        """
        Checks if layers can be added with a qlr defintion file by the layertree structure.
        Checks if groups can be added (containing layers itself) with a qlr definition file by the layertree structure.
        Checks if layers can be added with no source info as invalid layers.
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml"
        )
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

        assert len(available_layers) == 16

        # load the projecttopping file
        projecttopping_file_path = os.path.join(
            self.toppings_test_path,
            "projecttopping/opengis_projecttopping_qlr_KbS_LV95_V1_4.yaml",
        )

        with open(projecttopping_file_path) as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            legend = generator.legend(
                available_layers,
                layertree_structure=projecttopping_data["layertree"],
                path_resolver=lambda path: os.path.join(
                    os.path.dirname(projecttopping_file_path), path
                )
                if path
                else None,
            )

        # QLR defined layer ("Roads from QLR") is appended
        # layers from QLR defined group are not
        # invalid layers ("An invalid layer" and "Another invalid layer") are appended
        assert len(available_layers) == 19

        relations, _ = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check if the ili layers are properly loaded
        ili_layers_group = qgis_project.layerTreeRoot().findGroup(
            "KbS_LV95_V1_4 Layers"
        )
        assert ili_layers_group is not None
        ili_layers_group_layers = ili_layers_group.findLayers()
        assert [layer.name() for layer in ili_layers_group_layers] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort (Geo_Lage_Polygon)",
        ]

        qlr_layers_group = qgis_project.layerTreeRoot().findGroup("Other Layers")
        assert qlr_layers_group is not None

        # qlr layer ("Roads from QLR") is properly loaded
        qlr_layers_group_layers = qlr_layers_group.findLayers()
        assert "The Road Signs" in [layer.name() for layer in qlr_layers_group_layers]

        # qlr group ("QLR-Group") is properly loaded
        qlr_group = qlr_layers_group.findGroup("Simple Roads")
        assert qlr_group is not None

        qlr_group_layers = qlr_group.findLayers()
        expected_qlr_layers = {
            "StreetNamePosition",
            "StreetAxis",
            "LandCover",
            "Street",
            "LandCover_Type",
            "RoadSign_Type",
            "The Road Signs",
        }
        assert {layer.name() for layer in qlr_group_layers} == expected_qlr_layers

    def test_kbs_postgis_source_layers(self):
        """
        Checks if layers can be added with "ogr" provider and uri defined in the layertree structure.
        Checks if layers can be added with "postgres" provider and uri defined in the layertree structure.
        Checks if layers can be added with "wms" provider and uri defined in the layertree structure.
        Checks if layers can be added with no source info as invalid layers.
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml"
        )
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

        assert len(available_layers) == 16

        # load the projecttopping file
        projecttopping_file_path = os.path.join(
            self.toppings_test_path,
            "projecttopping/opengis_projecttopping_source_KbS_LV95_V1_4.yaml",
        )

        # write dynamic parameters in the new file
        test_projecttopping_file_path = os.path.join(
            test_path, "testtree_{:%Y%m%d%H%M%S%f}.yaml".format(datetime.datetime.now())
        )
        with open(projecttopping_file_path) as file:
            filedata = file.read()

            filedata = filedata.replace("{test_path}", os.path.join(test_path))
            filedata = filedata.replace("{PGHOST}", importer.configuration.dbhost)
            filedata = filedata.replace(
                "{test_schema}", importer.configuration.dbschema
            )

            with open(test_projecttopping_file_path, "w") as file:
                file.write(filedata)

        with open(test_projecttopping_file_path) as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            legend = generator.legend(
                available_layers,
                layertree_structure=projecttopping_data["layertree"],
                path_resolver=lambda path: os.path.join(
                    os.path.dirname(projecttopping_file_path), path
                )
                if path
                else None,
            )

        # ogr layer is added ("Local Landcover")
        # postgres layer is added ("Local Belasteter Standort")
        # wms layer is added ("Local WMS")
        # invalid layers ("An invalid layer" and "Another invalid layer") are appended
        assert len(available_layers) == 21

        relations, _ = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check if the ili layers are properly loaded
        ili_layers_group = qgis_project.layerTreeRoot().findGroup(
            "KbS_LV95_V1_4 Layers"
        )
        assert ili_layers_group is not None
        ili_layers_group_layers = ili_layers_group.findLayers()
        assert [layer.name() for layer in ili_layers_group_layers] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort (Geo_Lage_Polygon)",
        ]

        source_layers_group = qgis_project.layerTreeRoot().findGroup("Other Layers")
        assert source_layers_group is not None

        # ogr layer ("Local Landcover") is properly loaded
        source_layers_group_layers = source_layers_group.findLayers()
        expected_source_layers = {
            "Local Landcover",
            "Local Zuständigkeit Kataster",
            "Local WMS",
            "An invalid layer",
            "Another invalid layer",
        }
        assert {
            layer.name() for layer in source_layers_group_layers
        } == expected_source_layers

        for layer in source_layers_group_layers:
            qgis_layer = layer.layer()
            if layer.name() == "Local WMS":
                assert qgis_layer.dataProvider().name() == "wms"
                print(qgis_layer.dataProvider().dataSourceUri())
                assert (
                    qgis_layer.dataProvider().dataSourceUri()
                    == "contextualWMSLegend=0&crs=EPSG:2056&dpiMode=7&featureCount=10&format=image/jpeg&layers=ch.bav.kataster-belasteter-standorte-oev&styles=default&url=https://wms.geo.admin.ch/?%0ASERVICE%3DWMS%0A%26VERSION%3D1.3.0%0A%26REQUEST%3DGetCapabilities"
                )
                assert qgis_layer.isValid()
            if layer.name() == "Local Zuständigkeit Kataster":
                assert qgis_layer.dataProvider().name() == "postgres"
                print(qgis_layer.dataProvider().dataSourceUri())
                assert (
                    qgis_layer.dataProvider().dataSourceUri()
                    == f"dbname='gis' host={importer.configuration.dbhost} user='docker' password='docker' key='t_id' checkPrimaryKeyUnicity='1' table=\"{importer.configuration.dbschema}\".\"zustaendigkeitkataster\""
                )
                assert qgis_layer.isValid()
            if layer.name() == "Local Landcover":
                assert qgis_layer.dataProvider().name() == "ogr"

        os.remove(test_projecttopping_file_path)

    def test_kbs_postgis_qml_styles(self):
        """
        Checks if qml style files can be applied by the layer tree.
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml"
        )
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

        assert len(available_layers) == 16

        # load the projecttopping file
        projecttopping_file_path = os.path.join(
            self.toppings_test_path,
            "projecttopping/opengis_projecttopping_qml_KbS_LV95_V1_4.yaml",
        )

        with open(projecttopping_file_path) as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            legend = generator.legend(
                available_layers,
                layertree_structure=projecttopping_data["layertree"],
                path_resolver=lambda path: os.path.join(
                    os.path.dirname(projecttopping_file_path), path
                )
                if path
                else None,
            )

        # No layers added now - stays 16
        assert len(available_layers) == 16

        relations, _ = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)
        count = 0

        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert tabs[0].name() == "Allgemein"
                for field in layer.layer.fields():
                    if field.name() == "bemerkung_rm":
                        assert field.alias() == "Bemerkung Romanisch"
                    if field.name() == "bemerkung_it":
                        assert field.alias() == "Bemerkung Italienisch"
            if layer.name == "parzellenidentifikation":
                count += 1
                assert (
                    layer.layer.displayExpression()
                    == "nbident || ' - '  || \"parzellennummer\" "
                )

        # check if the layers have been considered
        assert count == 2

    def test_kbs_postgis_qml_multistyles(self):
        """
        Checks if "styles" and their qml style files can be applied by the layer tree
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml"
        )
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

        assert len(available_layers) == 16

        # load the projecttopping file
        projecttopping_file_path = os.path.join(
            self.toppings_test_path,
            "projecttopping/opengis_projecttopping_multistyles_KbS_LV95_V1_4.yaml",
        )

        with open(projecttopping_file_path) as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            legend = generator.legend(
                available_layers,
                layertree_structure=projecttopping_data["layertree"],
                path_resolver=lambda path: os.path.join(
                    os.path.dirname(projecttopping_file_path), path
                )
                if path
                else None,
            )

        # No layers added now - stays 16
        assert len(available_layers) == 16

        relations, _ = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)
        count = 0

        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count += 1
                style_manager = layer.layer.styleManager()

                # default style
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert tabs[0].name() == "Allgemein"
                for field in layer.layer.fields():
                    if field.name() == "bemerkung_rm":
                        assert field.alias() == "Bemerkung Romanisch"
                    if field.name() == "bemerkung_it":
                        assert field.alias() == "Bemerkung Italienisch"
                assert (
                    layer.layer.displayExpression()
                    == "'Default: '||standorttyp ||' - '||katasternummer"
                )

                # robot style (in binary)
                style_manager.setCurrentStyle("robot")
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert (
                    tabs[0].name()
                    == "01000111 01100101 01101110 01100101 01110010 01100001 01101100"
                )
                for field in layer.layer.fields():
                    if field.name() == "bemerkung_rm":
                        assert (
                            field.alias()
                            == "01100010 01100101 01101101 01100101 01110010 01101011 01110101 01101110 01100111 01011111 01110010 01101101"
                        )
                    if field.name() == "bemerkung_it":
                        assert (
                            field.alias()
                            == "01100010 01100101 01101101 01100101 01110010 01101011 01110101 01101110 01100111 01011111 01101001 01110100"
                        )
                assert (
                    layer.layer.displayExpression()
                    == "'Robot: '||standorttyp ||' - '||katasternummer"
                )

                # french style (in french)
                style_manager.setCurrentStyle("french")
                edit_form_config = layer.layer.editFormConfig()
                assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert tabs[0].name() == "Général"
                for field in layer.layer.fields():
                    if field.name() == "bemerkung_rm":
                        assert field.alias() == "Remarque en Romane"
                    if field.name() == "bemerkung_it":
                        assert field.alias() == "Remarque en Italien"
                assert (
                    layer.layer.displayExpression()
                    == "'French: '||standorttyp ||' - '||katasternummer"
                )

        # check if the layers have been considered
        assert count == 1

    def test_kbs_postgis_qml_mapthemes(self):
        """
        Checks if mapthemes can be applied to the project
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml"
        )
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

        assert len(available_layers) == 16

        # load the projecttopping file
        projecttopping_file_path = os.path.join(
            self.toppings_test_path,
            "projecttopping/opengis_projecttopping_multistyles_KbS_LV95_V1_4.yaml",
        )

        with open(projecttopping_file_path) as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            legend = generator.legend(
                available_layers,
                layertree_structure=projecttopping_data["layertree"],
                path_resolver=lambda path: os.path.join(
                    os.path.dirname(projecttopping_file_path), path
                )
                if path
                else None,
            )
            assert "mapthemes" in projecttopping_data
            mapthemes = projecttopping_data["mapthemes"]

        # No layers added now - stays 16
        assert len(available_layers) == 16

        relations, _ = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.mapthemes = mapthemes
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # 1. NO THEME:
        # no map theme should be applied yet. The layer tree should be like it is defined in the YAML
        layertree_root = qgis_project.layerTreeRoot()
        layertree_model = QgsLayerTreeModel(layertree_root)

        # group "KbS_LV95_V1_4 Layers" should be expanded and checked
        main_group = layertree_root.findGroup("KbS_LV95_V1_4 Layers")
        assert main_group is not None
        assert main_group.isExpanded()
        assert main_group.itemVisibilityChecked()

        # group "Informationen" should be expanded and checked
        information_group = main_group.findGroup("Informationen")
        assert information_group is not None
        assert main_group.isExpanded()
        assert main_group.itemVisibilityChecked()

        # Belasteter_Standort (Geo_Lage_Polygon) is expanded (default) and checked (default)
        # Belasteter_Standord (Geo_Lage_Punkt) has the default style
        count_default_state = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count_default_state += 1

                layer_node = main_group.findLayer(layer.layer)
                assert layer_node.isExpanded()
                assert layer_node.itemVisibilityChecked()
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count_default_state += 1

                # default style display expression
                assert (
                    layer.layer.displayExpression()
                    == "'Default: '||standorttyp ||' - '||katasternummer"
                )
        assert count_default_state == 2

        # 2. "Group Checker Theme" THEME:
        # let's apply the "Group Checker Theme"
        qgis_project.mapThemeCollection().applyTheme(
            "Group Checker Theme", layertree_root, layertree_model
        )
        layertree_root = qgis_project.layerTreeRoot()
        layertree_model = QgsLayerTreeModel(layertree_root)

        # group "KbS_LV95_V1_4 Layers" should NOT be expanded and NOT checked
        main_group = layertree_root.findGroup("KbS_LV95_V1_4 Layers")
        assert main_group is not None
        assert not main_group.isExpanded()
        # not yet possible to control group checked state: assert not main_group.itemVisibilityChecked()

        # group "Informationen" should be expanded and checked
        information_group = main_group.findGroup("Informationen")
        assert information_group is not None
        assert information_group.isExpanded()
        # not yet possible to control group checked state: assert information_group.itemVisibilityChecked()

        # Belasteter_Standort (Geo_Lage_Polygon) is NOT expanded and NOT checked
        # Belasteter_Standord (Geo_Lage_Punkt) has the default style still
        count_group_checker_state = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count_group_checker_state += 1

                layer_node = main_group.findLayer(layer.layer)
                # not in theme, so not enabled
                assert not layer_node.itemVisibilityChecked()
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count_group_checker_state += 1

                # default style display expression
                assert (
                    layer.layer.displayExpression()
                    == "'Default: '||standorttyp ||' - '||katasternummer"
                )
        assert count_group_checker_state == 2

        # 3. "French Theme" THEME:
        # let's apply the "French Theme"
        qgis_project.mapThemeCollection().applyTheme(
            "French Theme", layertree_root, layertree_model
        )
        layertree_root = qgis_project.layerTreeRoot()
        layertree_model = QgsLayerTreeModel(layertree_root)

        # group "KbS_LV95_V1_4 Layers" should be expanded and checked
        main_group = layertree_root.findGroup("KbS_LV95_V1_4 Layers")
        assert main_group is not None
        assert main_group.isExpanded()
        # not yet possible to control group checked state: assert main_group.itemVisibilityChecked()

        # group "Informationen" should be NOT expanded and checked
        information_group = main_group.findGroup("Informationen")
        assert information_group is not None
        assert not information_group.isExpanded()
        # not yet possible to control group checked state: assert information_group.itemVisibilityChecked()

        # Belasteter_Standort (Geo_Lage_Polygon) is expanded and checked...
        # ... but some symbology items of it are unchecked
        # Belasteter_Standord (Geo_Lage_Punkt) has the french style
        count_french_state = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count_french_state += 1

                layer_node = main_group.findLayer(layer.layer)
                assert layer_node.isExpanded()
                assert layer_node.itemVisibilityChecked()

                # check if the symbology items are checked/unchecked right
                expected_checked_items = [
                    "{71f4f768-f5a0-4556-a526-e003f02430e8}",
                    "{fc472bf1-4694-4033-8a69-0ba5db267e92}",
                    "{fa7fd14d-afac-4d49-8ae6-054d6ef3ed4c}",
                    "{175249d7-9889-445f-b233-1acf85fefe30}",
                    "{88de6f70-cd62-4a3f-9cb0-5635c1d2cfeb}",
                    "{3f377bb8-7110-41e0-9fe5-32a4e802aa28}",
                ]

                symbolitem_keys = [
                    item.ruleKey()
                    for item in layer.layer.renderer().legendSymbolItems()
                ]
                assert symbolitem_keys and len(symbolitem_keys) == 9

                for symbolitem_key in symbolitem_keys:
                    if symbolitem_key in expected_checked_items:
                        assert layer.layer.renderer().legendSymbolItemChecked(
                            symbolitem_key
                        )
                    else:
                        assert not layer.layer.renderer().legendSymbolItemChecked(
                            symbolitem_key
                        )

                # check if the symbology items are expanded/collapsed right
                expected_expanded_items = [
                    "{fa7fd14d-afac-4d49-8ae6-054d6ef3ed4c}",
                    "{88de6f70-cd62-4a3f-9cb0-5635c1d2cfeb}",
                ]

                expanded_items = layer_node.customProperty("expandedLegendNodes")
                assert expanded_items and len(expanded_items)
                assert set(expanded_items) == set(expected_expanded_items)

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count_french_state += 1

                # french style display expression
                assert (
                    layer.layer.displayExpression()
                    == "'French: '||standorttyp ||' - '||katasternummer"
                )
        assert count_french_state == 2

        # 4. "Robot Theme" THEME:
        # let's apply the "Robot Theme"
        qgis_project.mapThemeCollection().applyTheme(
            "Robot Theme", layertree_root, layertree_model
        )
        layertree_root = qgis_project.layerTreeRoot()
        layertree_model = QgsLayerTreeModel(layertree_root)

        # group "KbS_LV95_V1_4 Layers" should be expanded and checked
        main_group = layertree_root.findGroup("KbS_LV95_V1_4 Layers")
        assert main_group is not None
        assert main_group.isExpanded()
        # not yet possible to control group checked state: assert main_group.itemVisibilityChecked()

        # group "Informationen" should be NOT expanded but checked
        information_group = main_group.findGroup("Informationen")
        assert information_group is not None
        assert not information_group.isExpanded()
        # not yet possible to control group checked state: assert information_group.itemVisibilityChecked()

        # Belasteter_Standort (Geo_Lage_Polygon) is NOT expanded but checked...
        # ... and some symbology items of it are unchecked
        # Belasteter_Standord (Geo_Lage_Punkt) has the robot style
        count_robot_state = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count_robot_state += 1

                layer_node = main_group.findLayer(layer.layer)
                assert not layer_node.isExpanded()
                assert layer_node.itemVisibilityChecked()

                # check if the symbology items are checked/unchecked right
                expected_checked_items = [
                    "{cd999ccf-a63e-4a1a-81fc-7b31473da49e}",
                    "{71f4f768-f5a0-4556-a526-e003f02430e8}",
                    "{fc472bf1-4694-4033-8a69-0ba5db267e92}",
                    "{175249d7-9889-445f-b233-1acf85fefe30}",
                    "{88de6f70-cd62-4a3f-9cb0-5635c1d2cfeb}",
                ]

                symbolitem_keys = [
                    item.ruleKey()
                    for item in layer.layer.renderer().legendSymbolItems()
                ]
                assert symbolitem_keys and len(symbolitem_keys) == 9

                for symbolitem_key in symbolitem_keys:
                    if symbolitem_key in expected_checked_items:
                        assert layer.layer.renderer().legendSymbolItemChecked(
                            symbolitem_key
                        )
                    else:
                        assert not layer.layer.renderer().legendSymbolItemChecked(
                            symbolitem_key
                        )

                # check if the symbology items are expanded/collapsed right
                expected_expanded_items = ["{fa7fd14d-afac-4d49-8ae6-054d6ef3ed4c}"]

                expanded_items = layer_node.customProperty("expandedLegendNodes")
                assert expanded_items and len(expanded_items) == 1
                assert set(expanded_items) == set(expected_expanded_items)

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count_robot_state += 1

                # robot style display expression
                assert (
                    layer.layer.displayExpression()
                    == "'Robot: '||standorttyp ||' - '||katasternummer"
                )
        assert count_robot_state == 2

    def test_kbs_postgis_iliname(self):
        """
        Checks if layers can be loaded by it's iliname and geometry column.
        Checks if layers can be loaded by it's layername (what is basicly the table name) for layers without alias.
        Checks if qml style files can be applied by to some layers and some not (with the same name).
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml"
        )
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart2",
            importer.configuration.dbschema,
            consider_basket_handling=True,
        )
        available_layers = generator.layers()

        assert len(available_layers) == 18

        # load the projecttopping file
        projecttopping_file_path = os.path.join(
            self.toppings_test_path,
            "projecttopping/opengis_projecttopping_iliname_KbS_LV95_V1_4.yaml",
        )

        with open(projecttopping_file_path) as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            legend = generator.legend(
                available_layers,
                layertree_structure=projecttopping_data["layertree"],
                path_resolver=lambda path: self.ilidata_path_resolver(
                    importer.configuration.base_configuration,
                    os.path.dirname(projecttopping_file_path),
                    path,
                )
                if path
                else None,
            )

        # additional basket layers
        assert len(available_layers) == 18

        relations, _ = generator.relations(available_layers)

        project = Project(context={"catalogue_datasetname": CATALOGUE_DATASETNAME})
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # punkt layer with applied qml
        punkt_standort = None
        # polygon layer with applied qml
        polygon_standort = None
        # parzellen layer with applied qml
        parzellen = None
        # system layer found by it's layername
        t_ili2db_basket = None
        t_ili2db_dataset = None

        main_group = qgis_project.layerTreeRoot().findGroup("KbS_LV95_V1_4 Layers")
        assert main_group is not None
        layers = main_group.findLayers()

        for layer in layers:
            if layer.name() == "Punkt Standort":
                punkt_standort = layer
            if layer.name() == "Polygon Standort":
                polygon_standort = layer
            if layer.name() == "Parzellen":
                parzellen = layer

        assert punkt_standort.layer().isValid()
        assert polygon_standort.layer().isValid()
        assert parzellen.layer().isValid()

        system_group = qgis_project.layerTreeRoot().findGroup("System Layers")
        assert system_group is not None
        layers = system_group.findLayers()
        for layer in layers:
            if layer.name() == "t_ili2db_basket":
                t_ili2db_basket = layer
            if layer.name() == "t_ili2db_dataset":
                t_ili2db_dataset = layer

        assert t_ili2db_basket.layer().isValid()
        assert t_ili2db_dataset.layer().isValid()

        # check qml from file at punkt_standort
        edit_form_config = punkt_standort.layer().editFormConfig()
        assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
        tabs = edit_form_config.tabs()
        assert len(tabs) == 5
        assert tabs[0].name() == "Allgemein"
        for field in punkt_standort.layer().fields():
            if field.name() == "bemerkung_rm":
                assert field.alias() == "Bemerkung Romanisch"
            if field.name() == "bemerkung_it":
                assert field.alias() == "Bemerkung Italienisch"

        # check qml from file at polygon_standort
        edit_form_config = polygon_standort.layer().editFormConfig()
        assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
        tabs = edit_form_config.tabs()
        assert len(tabs) == 5
        assert tabs[0].name() == "Allgemein"
        for field in polygon_standort.layer().fields():
            if field.name() == "bemerkung_rm":
                assert field.alias() == "Bemerkung Romanisch"
            if field.name() == "bemerkung_it":
                assert field.alias() == "Bemerkung Italienisch"

        # check qml from file at parzellen
        assert (
            parzellen.layer().displayExpression()
            == "nbident || ' - '  || \"parzellennummer\" "
        )

    def test_kbs_postgis_ilidata(self):
        """
        Checks if qml style files can be got over ilidata.xml and applied by the layer tree.
        Checks if qlr style files can be got over ilidata.xml and applied by the layer tree.
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml"
        )
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

        assert len(available_layers) == 16

        # load the projecttopping file
        projecttopping_file_path = os.path.join(
            self.toppings_test_path,
            "projecttopping/opengis_projecttopping_ilidata_KbS_LV95_V1_4.yaml",
        )

        with open(projecttopping_file_path) as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            legend = generator.legend(
                available_layers,
                layertree_structure=projecttopping_data["layertree"],
                path_resolver=lambda path: self.ilidata_path_resolver(
                    importer.configuration.base_configuration,
                    os.path.dirname(projecttopping_file_path),
                    path,
                )
                if path
                else None,
            )

        # QLR defined layer ("Roads from QLR") is appended
        # layers from QLR defined group are not
        # invalid layers ("An invalid layer" and "Another invalid layer") are appended
        assert len(available_layers) == 19

        relations, _ = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        belasteter_standort_geo_lage_punkt = None
        parzellenidentifikation = None
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                belasteter_standort_geo_lage_punkt = layer
            if layer.name == "parzellenidentifikation":
                parzellenidentifikation = layer

        # check qml from file
        assert belasteter_standort_geo_lage_punkt
        edit_form_config = belasteter_standort_geo_lage_punkt.layer.editFormConfig()
        assert edit_form_config.layout() == QgsEditFormConfig.TabLayout
        tabs = edit_form_config.tabs()
        assert len(tabs) == 5
        assert tabs[0].name() == "Allgemein"
        for field in belasteter_standort_geo_lage_punkt.layer.fields():
            if field.name() == "bemerkung_rm":
                assert field.alias() == "Bemerkung Romanisch"
            if field.name() == "bemerkung_it":
                assert field.alias() == "Bemerkung Italienisch"

        # check qml from ilidata
        assert parzellenidentifikation
        assert (
            parzellenidentifikation.layer.displayExpression()
            == "nbident || ' - '  || \"parzellennummer\" "
        )

        qlr_layers_group = qgis_project.layerTreeRoot().findGroup("Other Layers")
        assert qlr_layers_group is not None

        # check qlr from ilidata ("Roads from QLR") is properly loaded
        qlr_layers_group_layers = qlr_layers_group.findLayers()
        assert "The Road Signs" in [layer.name() for layer in qlr_layers_group_layers]

        # check qlr group from file ("QLR-Group") is properly loaded
        qlr_group = qlr_layers_group.findGroup("Simple Roads")
        assert qlr_group is not None

        qlr_group_layers = qlr_group.findLayers()
        expected_qlr_layers = {
            "StreetNamePosition",
            "StreetAxis",
            "LandCover",
            "Street",
            "LandCover_Type",
            "RoadSign_Type",
            "The Road Signs",
        }
        assert {layer.name() for layer in qlr_group_layers} == expected_qlr_layers

    def test_kbs_postgis_layouts_and_variables(self):
        """
        Checks if print layouts can be applied to the project
        """

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, self.toppings_test_path
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = "2056"
        importer.configuration.tomlfile = os.path.join(
            self.toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml"
        )
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

        assert len(available_layers) == 16

        # load the projecttopping file
        projecttopping_file_path = os.path.join(
            self.toppings_test_path,
            "projecttopping/opengis_projecttopping_layouts_and_variables_KbS_LV95_V1_4.yaml",
        )

        with open(projecttopping_file_path) as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            legend = generator.legend(
                available_layers,
                layertree_structure=projecttopping_data["layertree"],
                path_resolver=lambda path: os.path.join(
                    os.path.dirname(projecttopping_file_path), path
                )
                if path
                else None,
            )
            assert "variables" in projecttopping_data
            custom_variables = projecttopping_data["variables"]
            assert "layouts" in projecttopping_data
            resolved_layouts = generator.resolved_layouts(
                projecttopping_data["layouts"],
                path_resolver=lambda path: os.path.join(
                    os.path.dirname(projecttopping_file_path), path
                )
                if path
                else None,
            )

        # No layers added now - stays 16
        assert len(available_layers) == 16

        relations, _ = generator.relations(available_layers)

        project = Project()
        project.layers = available_layers
        project.legend = legend
        project.relations = relations
        project.custom_variables = custom_variables
        project.layouts = resolved_layouts
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # test variables
        custom_variables = qgis_project.customVariables()
        assert custom_variables.get("First Variable") == "This is a test value."
        assert custom_variables.get("Another Variable") == "2"
        assert custom_variables.get("Variable with Structure") == [
            "Not",
            "The",
            "Normal",
            815,
            "Case",
        ]

        # test print layout
        checked_layout_count = 0
        for layout in qgis_project.layoutManager().printLayouts():
            if layout.name() == "Layout One":
                assert layout.itemsModel()
                # there are two items on layout one and an atlas item (so there are 3 rows)
                assert layout.itemsModel().rowCount() == 3
                # and an atlas is activated
                assert layout.atlas()
                # but coverage layer is not properly attached by QGIS
                # assert layout.atlas().coverageLayer().name() == "Belasteter_Standort (Geo_Lage_Punkt)"
                checked_layout_count += 1
            if layout.name() == "Layout Two":
                assert layout.itemsModel()
                # there are three items on layout two and an atlas item (so there are 4 rows)
                assert layout.itemsModel().rowCount() == 4
                # and an atlas is activated
                assert layout.atlas()
                # but coverage layer is not properly attached by QGIS
                # assert layout.atlas().coverageLayer().name() == "Belasteter_Standort (Geo_Lage_Polygon)"
                checked_layout_count += 1
        assert checked_layout_count == 2

    # that's the same like in generate_project.py and workflow_wizard.py
    def get_topping_file_list(self, base_config, id_list):
        topping_file_model = self.get_topping_file_model(
            base_config, id_list, test_path
        )
        file_path_list = []

        for file_id in id_list:
            matches = topping_file_model.match(
                topping_file_model.index(0, 0), Qt.DisplayRole, file_id, 1
            )
            if matches:
                file_path = matches[0].data(int(topping_file_model.Roles.LOCALFILEPATH))
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, base_config, id_list, tool_dir=None):
        topping_file_cache = IliToppingFileCache(base_config, id_list, tool_dir)

        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        topping_file_cache.download_finished.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(30000)

        topping_file_cache.refresh()

        if len(topping_file_cache.downloaded_files) != len(id_list):
            loop.exec()

        return topping_file_cache.model

    # that's the same (more or less) like in project_creation_page.py

    def ilidata_path_resolver(self, base_config, base_path, path):
        if "ilidata:" in path or "file:" in path:
            data_file_path_list = self.get_topping_file_list(base_config, [path])
            return data_file_path_list[0] if data_file_path_list else None
        return os.path.join(base_path, path)

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
