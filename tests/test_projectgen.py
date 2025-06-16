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


class TestProjectGen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_ili2db3_kbs_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.db_ili_version = 3
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
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

        count = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                belasteter_standort_punkt_layer = layer
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert (
                    edit_form_config.layout()
                    == QgsEditFormConfig.EditorLayout.TabLayout
                )
                tabs = edit_form_config.tabs()
                fields = {field.name() for field in tabs[0].children()}
                assert fields == {
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "geo_lage_polygon",
                    "inbetrieb",
                    "ersteintrag",
                    "bemerkung_en",
                    "bemerkung_rm",
                    "katasternummer",
                    "bemerkung_it",
                    "nachsorge",
                    "url_kbs_auszug",
                    "url_standort",
                    "statusaltlv",
                    "bemerkung_fr",
                    "standorttyp",
                    "bemerkung",
                    "geo_lage_punkt",
                    "bemerkung_de",
                }

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "Parzellenidentifikation",
                        "EGRID_",
                        "Deponietyp",
                        "UntersMassn",
                    ]
                    assert set(tab_list) == set(expected_tab_list)
                    assert len(tab_list) == len(expected_tab_list)

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                belasteter_standort_polygon_layer = layer

        assert count == 1
        assert len(available_layers) == 16

        assert (
            len(
                qgis_project.relationManager().referencingRelations(
                    belasteter_standort_polygon_layer.layer
                )
            )
            == 1  # only zuständigkeit kataster - the others are enum value relation
        )
        assert (
            len(
                qgis_project.relationManager().referencedRelations(
                    belasteter_standort_polygon_layer.layer
                )
            )
            > 3
        )
        assert (
            len(
                qgis_project.relationManager().referencingRelations(
                    belasteter_standort_punkt_layer.layer
                )
            )
            == 1  # only zuständigkeit kataster - the others are enum value relation
        )
        assert (
            len(
                qgis_project.relationManager().referencedRelations(
                    belasteter_standort_punkt_layer.layer
                )
            )
            > 3
        )

    def test_kbs_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbschema = "kbs_lv95_v1_3_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
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

        count = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                belasteter_standort_punkt_layer = layer
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert (
                    edit_form_config.layout()
                    == QgsEditFormConfig.EditorLayout.TabLayout
                )
                tabs = edit_form_config.tabs()
                fields = {field.name() for field in tabs[0].children()}
                assert fields == {
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "geo_lage_polygon",
                    "inbetrieb",
                    "ersteintrag",
                    "katasternummer",
                    "nachsorge",
                    "url_kbs_auszug",
                    "url_standort",
                    "statusaltlv",
                    "standorttyp",
                    "bemerkung",
                    "bemerkung_de",
                    "bemerkung_fr",
                    "bemerkung_rm",
                    "bemerkung_it",
                    "bemerkung_en",
                    "geo_lage_punkt",
                }

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "Parzellenidentifikation",
                        "EGRID_",
                        "Deponietyp",
                        "UntersMassn",
                    ]
                    assert len(tab_list) == len(expected_tab_list)
                    assert set(tab_list) == set(expected_tab_list)

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                belasteter_standort_polygon_layer = layer

        assert count == 1
        assert len(available_layers) == 16

        assert (
            len(
                qgis_project.relationManager().referencingRelations(
                    belasteter_standort_polygon_layer.layer
                )
            )
            == 1  # only zuständigkeit kataster - the others are enum value relation
        )
        assert (
            len(
                qgis_project.relationManager().referencedRelations(
                    belasteter_standort_polygon_layer.layer
                )
            )
            > 3
        )
        assert (
            len(
                qgis_project.relationManager().referencingRelations(
                    belasteter_standort_punkt_layer.layer
                )
            )
            == 1  # only zuständigkeit kataster - the others are enum value relation
        )
        assert (
            len(
                qgis_project.relationManager().referencedRelations(
                    belasteter_standort_punkt_layer.layer
                )
            )
            > 3
        )

    def test_ili2db3_kbs_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_kbs_3_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        importer.configuration.db_ili_version = 3
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

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

        count = 0
        for layer in available_layers:
            if layer.name == "belasteter_standort":  # Polygon
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert (
                    edit_form_config.layout()
                    == QgsEditFormConfig.EditorLayout.TabLayout
                )
                tabs = edit_form_config.tabs()
                fields = {field.name() for field in tabs[0].children()}
                assert fields == {
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "geo_lage_polygon",
                    "inbetrieb",
                    "ersteintrag",
                    "bemerkung_en",
                    "bemerkung_rm",
                    "katasternummer",
                    "bemerkung_it",
                    "nachsorge",
                    "url_kbs_auszug",
                    "url_standort",
                    "statusaltlv",
                    "bemerkung_fr",
                    "standorttyp",
                    "bemerkung",
                    "bemerkung_de",
                }

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "Parzellenidentifikation",
                        "Geo_Lage_Punkt",
                        "EGRID_",
                        "Deponietyp",
                        "UntersMassn",
                    ]
                    assert len(tab_list) == len(expected_tab_list)
                    assert set(tab_list) == set(expected_tab_list)

                for tab in tabs:
                    if len(tab.findElements(tab.AeTypeRelation)) == 0:
                        assert tab.columnCount() == 2
                    else:
                        assert tab.columnCount() == 1

        assert count == 1
        assert {
            "statusaltlv",
            "multilingualtext",
            "untersmassn",
            "multilingualmtext",
            "languagecode_iso639_1",
            "deponietyp",
            "zustaendigkeitkataster",
            "standorttyp",
            "localisedtext",
            "localisedmtext",
            "belasteter_standort",
            "deponietyp_",
            "egrid_",
            "untersmassn_",
            "parzellenidentifikation",
            "belasteter_standort_geo_lage_punkt",
        } == {layer.name for layer in available_layers}

    def test_kbs_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

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

        count = 0
        for layer in available_layers:
            if layer.name == "belasteter_standort":  # Polygon
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert (
                    edit_form_config.layout()
                    == QgsEditFormConfig.EditorLayout.TabLayout
                )
                tabs = edit_form_config.tabs()
                fields = {field.name() for field in tabs[0].children()}
                assert fields == {
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "geo_lage_polygon",
                    "inbetrieb",
                    "ersteintrag",
                    "katasternummer",
                    "nachsorge",
                    "url_kbs_auszug",
                    "url_standort",
                    "statusaltlv",
                    "standorttyp",
                    "bemerkung",
                    "bemerkung_de",
                    "bemerkung_fr",
                    "bemerkung_rm",
                    "bemerkung_it",
                    "bemerkung_en",
                }

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "Parzellenidentifikation",
                        "Belasteter_Standort (Geo_Lage_Punkt)",
                        "EGRID_",
                        "Deponietyp",
                        "UntersMassn",
                    ]
                    assert len(tab_list) == len(expected_tab_list)
                    assert set(tab_list) == set(expected_tab_list)

                for tab in tabs:
                    if len(tab.findElements(tab.AeTypeRelation)) == 0:
                        assert tab.columnCount() == 2
                    else:
                        assert tab.columnCount() == 1

        assert count == 1
        assert {
            "statusaltlv",
            "multilingualtext",
            "untersmassn",
            "multilingualmtext",
            "languagecode_iso639_1",
            "deponietyp",
            "zustaendigkeitkataster",
            "standorttyp",
            "localisedtext",
            "localisedmtext",
            "belasteter_standort",
            "deponietyp_",
            "egrid_",
            "untersmassn_",
            "parzellenidentifikation",
            "belasteter_standort_geo_lage_punkt",
        } == {layer.name for layer in available_layers}

    def test_naturschutz_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbschema = "naturschutz_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 15
        assert len(available_layers) == 23
        assert len(relations) == 13

    def test_naturschutz_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_naturschutz_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 65
        assert len(available_layers) == 23
        assert len(relations) == 13

    def test_naturschutz_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbschema = "naturschutz_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
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
            DbIliMode.ili2mssql, uri, "smart1", importer.configuration.dbschema
        )

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 20
        assert len(available_layers) == 23
        assert len(relations) == 22

    def test_naturschutz_set_ignored_layers_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbschema = "naturschutz_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        generator.set_additional_ignored_layers(["einzelbaum", "datenbestand"])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 17
        assert len(available_layers) == 21
        assert len(relations) == 12

    def test_naturschutz_set_ignored_layers_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_naturschutz_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        generator.set_additional_ignored_layers(["einzelbaum", "datenbestand"])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        legend = generator.legend(available_layers)
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 67
        assert len(available_layers) == 21
        assert len(relations) == 12

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        layer_names = [l.name().lower() for l in qgis_project.mapLayers().values()]
        assert "einzelbaum" not in layer_names
        assert "datenbestand" not in layer_names
        assert "hochstamm_obstgarten" in layer_names

    def test_naturschutz_set_ignored_layers_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )
        importer.configuration.dbschema = "naturschutz_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
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
            DbIliMode.ili2mssql, uri, "smart1", importer.configuration.dbschema
        )

        generator.set_additional_ignored_layers(["einzelbaum", "datenbestand"])
        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 22
        assert len(available_layers) == 21
        assert len(relations) == 21

    def test_naturschutz_nometa_postgis(self):
        # model with missing meta attributes for multigeometry - no layers should be ignored
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1_noMeta"
        )
        importer.configuration.dbschema = "naturschutz_nometa_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 9
        assert len(available_layers) == 29
        assert len(relations) == 23

    def test_naturschutz_nometa_geopackage(self):
        # model with missing meta attributes for multigeometry - no layers should be ignored
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1_noMeta"
        )
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_naturschutz_nometa_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.create_basket_col = True
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        ignored_layers = generator.get_ignored_layers()
        available_layers = generator.layers([])
        relations, _ = generator.relations(available_layers)

        assert len(ignored_layers) == 31
        assert len(available_layers) == 29
        assert len(relations) == 23

    def test_ranges_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
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

        count = 0
        for layer in available_layers:
            if layer.name == "avaluo":
                config = (
                    layer.layer.fields()
                    .field("area_terreno2")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "-100.0"
                assert config["Max"] == "100000.0"

                config = (
                    layer.layer.fields()
                    .field("area_terreno3")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "0.0"
                assert (
                    int(Decimal(config["Max"])) == 99999999999999
                )  # '9.9999999999999906e+013'

                count += 1
                break

        assert count == 1

    def test_ranges_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_ranges_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

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

        count = 0
        for layer in available_layers:
            if layer.name == "avaluo":
                config = (
                    layer.layer.fields()
                    .field("area_terreno2")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "-100.0"
                assert config["Max"] == "100000.0"

                config = (
                    layer.layer.fields()
                    .field("area_terreno3")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "0.0"
                assert (
                    int(Decimal(config["Max"])) == 99999999999999
                )  # '9.99999999999999E13'

                count += 1
                break

        assert count == 1

    def test_ranges_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        count = 0
        for layer in available_layers:
            if layer.name == "avaluo":
                config = (
                    layer.layer.fields()
                    .field("area_terreno2")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "-100.0"
                assert config["Max"] == "100000.0"

                config = (
                    layer.layer.fields()
                    .field("area_terreno3")
                    .editorWidgetSetup()
                    .config()
                )
                assert config["Min"] == "0.0"
                assert (
                    int(Decimal(config["Max"])) == 99999999999999
                )  # '99999999999999.9'

                count += 1
                break

        assert count == 1

    def test_precision_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/RoadsSimpleIndividualExtents.ili"
        )
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_prec_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
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

        count = 0
        for layer in available_layers:
            if layer.layer.name().lower() == "streetnameposition":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "streetaxis":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.0
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is False
                )
            if layer.layer.name().lower() == "roadsign":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.1
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "landcover":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.000001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
        assert count == 4

    def test_precision_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/RoadsSimpleIndividualExtents.ili"
        )
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_precision_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

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

        count = 0
        for layer in available_layers:
            if layer.layer.name().lower() == "streetnameposition":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "streetaxis":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.0
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is False
                )
            if layer.layer.name().lower() == "roadsign":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.1
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "landcover":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.000001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
        assert count == 4

    def test_precision_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/RoadsSimpleIndividualExtents.ili"
        )
        importer.configuration.ilimodels = "RoadsSimple"
        importer.configuration.dbschema = "roads_simple_prec_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server="mssql",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        count = 0
        for layer in available_layers:
            if layer.layer.name().lower() == "streetnameposition":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "streetaxis":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.0
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is False
                )
            if layer.layer.name().lower() == "roadsign":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000000000000000,0.0000000000000000 : 200.0000000000000000,200.0000000000000000"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.1
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
            if layer.layer.name().lower() == "landcover":
                count += 1
                assert (
                    layer.extent.toString()
                    == "0.0000020000000000,0.0000040000000000 : 200.0000080000000082,200.0000060000000133"
                )
                assert layer.layer.geometryOptions().geometryPrecision() == 0.000001
                assert (
                    bool(layer.layer.geometryOptions().removeDuplicateNodes()) is True
                )
        assert count == 4

    def test_extent_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
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
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                assert (
                    layer.extent.toString(2)
                    == "165000.00,23000.00 : 1806900.00,1984900.00"
                )

        assert count == 1

    def test_extent_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_extent_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                assert (
                    layer.extent.toString(2)
                    == "165000.00,23000.00 : 1806900.00,1984900.00"
                )

        assert count == 1

    def test_extent_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server="mssql",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
        )

        available_layers = generator.layers()
        count = 0
        for layer in available_layers:
            if layer.extent is not None:
                count += 1
                assert (
                    layer.extent.toString(2)
                    == "165000.00,23000.00 : 1806900.00,1984900.00"
                )

        assert count == 1

    def test_nmrel_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "CoordSys"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "geoellipsoidal":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig("lambert_from5_fkey")
                assert map["nm-rel"] == "lambert_to5_fkey"
                map = edit_form_config.widgetConfig("axis_geoellipsoidal_axis_fkey")
                assert bool(map) is False
        assert count == 1

    def test_nmrel_geopackage(self):

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "CoordSys"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_nmrel_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

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

        count = 0
        for layer in available_layers:
            if layer.name == "geoellipsoidal":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig("lambert_from5_geoellipsoidal_T_Id")
                assert map["nm-rel"] == "lambert_to5_geocartesian2d_T_Id"
                map = edit_form_config.widgetConfig(
                    "axis_geoellipsoidal_axis_geoellipsoidal_T_Id"
                )
                assert bool(map) is False
        assert count == 1

    def test_meta_attr_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV03_V1"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"t_ili_tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"t_id"'
                )

        assert count == 2

    def test_meta_attr_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV03_V1"

        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_meta_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

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

        count = 0
        for layer in available_layers:
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"T_Ili_Tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"T_Id"'
                )

        assert count == 2

    def test_meta_attr_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV03_V1"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        count = 0
        for layer in available_layers:
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == (
                    '"T_Ili_Tid"' if Qgis.QGIS_VERSION_INT >= 31800 else '"T_Id"'
                )

        assert count == 2

    def test_meta_attr_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"
        importer.configuration.tomlfile = testdata_path(
            "toml/ExceptionalLoadsRoute_V1.toml"
        )
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "obstacle":
                count += 1
                assert layer.layer.displayExpression() == "type"

        assert count == 3

    def test_meta_attr_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"
        importer.configuration.tomlfile = testdata_path(
            "toml/ExceptionalLoadsRoute_V1.toml"
        )
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        count = 0
        for layer in available_layers:
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "obstacle":
                count += 1
                assert layer.layer.displayExpression() == "type"

        assert count == 3

    def test_meta_attr_hidden_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/hidden_fields.toml")
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in project.layers:
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count = 1
                        attribute_names = [child.name() for child in tab.children()]
                        assert len(attribute_names) == 18
                        assert "tipo" not in attribute_names
                        assert "avaluo" not in attribute_names

        assert count == 1

    def test_meta_attr_hidden_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/hidden_fields.toml")
        importer.configuration.inheritance = "smart2"
        importer.configuration.srs_code = 3116
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server="mssql",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        count = 0
        for layer in project.layers:
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count = 1
                        attribute_names = [child.name() for child in tab.children()]
                        assert len(attribute_names) == 18
                        assert "tipo" not in attribute_names
                        assert "avaluo" not in attribute_names

        assert count == 1

    def test_meta_attr_toml_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "ExceptionalLoadsRoute_LV95_V1"
        importer.configuration.tomlfile = testdata_path(
            "toml/ExceptionalLoadsRoute_V1.toml"
        )

        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_toml_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

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

        count = 0
        for layer in available_layers:
            if layer.name == "typeofroute":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "route":
                count += 1
                assert layer.layer.displayExpression() == "type"
            if layer.name == "obstacle":
                count += 1
                assert layer.layer.displayExpression() == "type"

        assert count == 3

    def test_meta_attr_order_toml_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool, "ilimodels/CIAF_LADM"
        )
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/attribute_order.toml")

        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_order_toml_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

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

        count = 0
        for layer in available_layers:
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = [
                            "attr1",
                            "attr2",
                            "attr3",
                            "attr5",
                            "attr4",
                            "attr6",
                            "attr8",
                            "attr9",
                            "avaluo",
                            "tipo",
                            "fmi",
                            "numero_predial",
                        ]

                        for i, val in enumerate(expected_order):
                            assert val == names[i]

        assert count == 1

    def test_meta_attr_order_toml_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/attribute_order.toml")
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = [
                            "attr1",
                            "attr2",
                            "attr3",
                            "attr5",
                            "attr4",
                            "attr6",
                            "attr8",
                            "attr9",
                            "avaluo",
                            "tipo",
                            "fmi",
                            "numero_predial",
                        ]

                        for i, val in enumerate(expected_order):
                            assert val == names[i]

        assert count == 1

    def test_meta_attr_order_toml_mssql(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = "CIAF_LADM"
        importer.configuration.tomlfile = testdata_path("toml/attribute_order.toml")
        importer.configuration.inheritance = "smart2"
        importer.configuration.srs_code = 3116
        importer.configuration.dbschema = "ciaf_ladm_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server="mssql",
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        count = 0
        for layer in available_layers:
            if layer.name == "predio":
                efc = layer.layer.editFormConfig()
                for tab in efc.tabs():
                    if tab.name() == "General":
                        count += 1
                        names = [child.name() for child in tab.children()]

                        # More than 10 to test numeric order instead of string order (1-10-11-2)
                        # 'tipo' is an inherited attribute pointing to a domain
                        expected_order = [
                            "attr1",
                            "attr2",
                            "attr3",
                            "attr5",
                            "attr4",
                            "attr6",
                            "attr8",
                            "attr9",
                            "avaluo",
                            "tipo",
                            "fmi",
                            "numero_predial",
                        ]

                        for i, val in enumerate(expected_order):
                            assert val == names[i]

        assert count == 1

    def test_bagof_cardinalities_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/CardinalityBag.ili")
        importer.configuration.ilimodels = "CardinalityBag"
        importer.configuration.dbschema = "any_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
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
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ["enumarrays_None", "enumbag_0", "0..*", "ei_typen", "t_id", "dispname"],
            ["enumarrays_None", "enumbag_1", "1..*", "ei_typen", "t_id", "dispname"],
            ["enumarrays_None", "enumlist_0", "0..*", "ei_typen", "t_id", "dispname"],
            ["enumarrays_None", "enumlist_1", "1..*", "ei_typen", "t_id", "dispname"],
            ["catarrays_None", "catbag_0", "0..*", "refitemitem", "t_id", "dispname"],
            ["catarrays_None", "catbag_1", "1..*", "refitemitem", "t_id", "dispname"],
            ["catarrays_None", "catlist_0", "0..*", "refitemitem", "t_id", "dispname"],
            ["catarrays_None", "catlist_1", "1..*", "refitemitem", "t_id", "dispname"],
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                assert [
                    layer_name,
                    attribute,
                    cardinality,
                    domain_table.name,
                    key_field,
                    value_field,
                ] in expected_bags_of_enum

        assert count == 8

        # Test widget type and constraints
        count = 0
        for layer in available_layers:
            if layer.name == "enumarrays":
                count += 1
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("enumbag_0")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("enumbag_1")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("enumlist_0")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("enumlist_1")
                    ).type()
                    == "ValueRelation"
                )

                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("enumbag_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("enumbag_1")
                    )
                    == 'array_length("enumbag_1")>0'
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("enumlist_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("enumlist_1")
                    )
                    == 'array_length("enumlist_1")>0'
                )

            if layer.name == "catarrays":
                count += 1
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("catbag_0")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("catbag_1")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("catlist_0")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("catlist_1")
                    ).type()
                    == "ValueRelation"
                )

                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("catbag_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("catbag_1")
                    )
                    == 'array_length("catbag_1")>0'
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("catlist_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("catlist_1")
                    )
                    == 'array_length("catlist_1")>0'
                )
        assert count == 2

    def test_bagof_cardinalities_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/CardinalityBag.ili")
        importer.configuration.ilimodels = "CardinalityBag"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_bags_of_enum_CardinalityBag_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            DbIliMode.ili2gpkg, uri, importer.configuration.inheritance
        )

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # Test BAGs OF ENUM
        expected_bags_of_enum = [
            ["enumarrays_None", "enumbag_0", "0..*", "ei_typen", "T_Id", "dispName"],
            ["enumarrays_None", "enumbag_1", "1..*", "ei_typen", "T_Id", "dispName"],
            ["enumarrays_None", "enumlist_0", "0..*", "ei_typen", "T_Id", "dispName"],
            ["enumarrays_None", "enumlist_1", "1..*", "ei_typen", "T_Id", "dispName"],
            ["catarrays_None", "catbag_0", "0..*", "refitemitem", "T_Id", "dispName"],
            ["catarrays_None", "catbag_1", "1..*", "refitemitem", "T_Id", "dispName"],
            ["catarrays_None", "catlist_0", "0..*", "refitemitem", "T_Id", "dispName"],
            ["catarrays_None", "catlist_1", "1..*", "refitemitem", "T_Id", "dispName"],
        ]

        count = 0
        for layer_name, bag_of_enum in bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                count += 1
                bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]
                assert [
                    layer_name,
                    attribute,
                    cardinality,
                    domain_table.name,
                    key_field,
                    value_field,
                ] in expected_bags_of_enum

        assert count == 8

        # Test widget type and constraints
        count = 0
        for layer in available_layers:
            if layer.name == "enumarrays":
                count += 1
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("enumbag_0")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("enumbag_1")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("enumlist_0")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("enumlist_1")
                    ).type()
                    == "ValueRelation"
                )

                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("enumbag_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("enumbag_1")
                    )
                    == 'array_length("enumbag_1")>0'
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("enumlist_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("enumlist_1")
                    )
                    == 'array_length("enumlist_1")>0'
                )

            if layer.name == "catarrays":
                count += 1
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("catbag_0")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("catbag_1")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("catlist_0")
                    ).type()
                    == "ValueRelation"
                )
                assert (
                    layer.layer.editorWidgetSetup(
                        layer.layer.fields().indexOf("catlist_1")
                    ).type()
                    == "ValueRelation"
                )

                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("catbag_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("catbag_1")
                    )
                    == 'array_length("catbag_1")>0'
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("catlist_0")
                    )
                    == ""
                )
                assert (
                    layer.layer.constraintExpression(
                        layer.layer.fields().indexOf("catlist_1")
                    )
                    == 'array_length("catlist_1")>0'
                )
        assert count == 2

    def test_relation_strength_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//Assoc23.ili")
        importer.configuration.ilimodels = "Assoc3"
        importer.configuration.dbschema = "assoc23_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        assert (
            qgis_project.relationManager().relation("agg3_agg3_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        assert (
            qgis_project.relationManager().relation("agg3_agg3_b_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager().relation("assoc3_assoc3_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager().relation("assoc3_assoc3_b_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        assert (
            qgis_project.relationManager().relation("classb1_agg1_a_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_agg2_a_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_assoc1_a_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_assoc2_a_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        # and that's the one with the strength 1 (composition)
        assert (
            qgis_project.relationManager().relation("classb1_comp1_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )

    def test_relation_strength_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//Assoc23.ili")
        importer.configuration.ilimodels = "Assoc3"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_assoc23_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            DbIliMode.ili2gpkg, uri, importer.configuration.inheritance
        )

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        assert (
            qgis_project.relationManager()
            .relation("agg3_agg3_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        assert (
            qgis_project.relationManager()
            .relation("agg3_agg3_b_classb1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager()
            .relation("assoc3_assoc3_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager()
            .relation("assoc3_assoc3_b_classb1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        assert (
            qgis_project.relationManager()
            .relation("classb1_agg1_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("classb1_agg2_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("classb1_assoc1_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager()
            .relation("classb1_assoc2_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Association
        )
        # and that's the one with the strength 1 (composition)
        assert (
            qgis_project.relationManager()
            .relation("classb1_comp1_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )

    def test_relation_strength_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//Assoc23.ili")
        importer.configuration.ilimodels = "Assoc3"
        importer.configuration.dbschema = "assoc23_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        assert (
            qgis_project.relationManager().relation("agg3_agg3_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        assert (
            qgis_project.relationManager().relation("agg3_agg3_b_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager().relation("assoc3_assoc3_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager().relation("assoc3_assoc3_b_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        assert (
            qgis_project.relationManager().relation("classb1_agg1_a_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_agg2_a_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_assoc1_a_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        assert (
            qgis_project.relationManager().relation("classb1_assoc2_a_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        # and that's the one with the strength 1 (composition)
        assert (
            qgis_project.relationManager().relation("classb1_comp1_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )

    def test_relation_strength_fakecomposition_postgis(self):
        # Test wheter associations with cardinality {1} or linking table relations become compositions in QGIS as they need a parent, even though they are not compositions in INTERLIS

        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//CompAssoc23.ili")
        importer.configuration.ilimodels = "CompAssoc"
        importer.configuration.dbschema = "compassoc_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # join table to parent table should be composition
        assert (
            qgis_project.relationManager().relation("assoc_assoc_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager().relation("assoc_assoc_b_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to basket table should be association
        assert (
            qgis_project.relationManager().relation("assoc_t_basket_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        # real composition -<#>{0..1} should be composition
        assert (
            qgis_project.relationManager().relation("classb1_comp_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # fake composition --{0..1} should be composition
        assert (
            qgis_project.relationManager()
            .relation("classb1_fakecomp_1a_fkey")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        # fake composition -<>{0..1} should be composition
        assert (
            qgis_project.relationManager()
            .relation("classb1_fakecomp_2a_fkey")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )

    def test_relation_strength_fakecomposition_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//CompAssoc23.ili")
        importer.configuration.ilimodels = "CompAssoc"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_compassoc_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            DbIliMode.ili2gpkg, uri, importer.configuration.inheritance
        )

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # join table to parent table should be composition
        assert (
            qgis_project.relationManager()
            .relation("assoc_assoc_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager()
            .relation("assoc_assoc_b_classb1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to basket table should be association
        assert (
            qgis_project.relationManager()
            .relation("assoc_T_basket_T_ILI2DB_BASKET_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Association
        )
        # real composition -<#>{0..1} should be composition
        assert (
            qgis_project.relationManager()
            .relation("classb1_comp_a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        # fake composition --{0..1} should be composition
        assert (
            qgis_project.relationManager()
            .relation("classb1_fakecomp_1a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        # fake composition -<>{0..1} should be composition
        assert (
            qgis_project.relationManager()
            .relation("classb1_fakecomp_2a_classa1_T_Id")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )

    def test_relation_strength_fakecomposition_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels//CompAssoc23.ili")
        importer.configuration.ilimodels = "CompAssoc"
        importer.configuration.dbschema = "compassoc{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        # join table to parent table should be composition
        assert (
            qgis_project.relationManager().relation("assoc_assoc_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to parent table should be composition
        assert (
            qgis_project.relationManager().relation("assoc_assoc_b_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # join table to basket table should be association
        assert (
            qgis_project.relationManager().relation("assoc_t_basket_fkey").strength()
            == QgsRelation.RelationStrength.Association
        )
        # real composition -<#>{0..1} should be composition
        assert (
            qgis_project.relationManager().relation("classb1_comp_a_fkey").strength()
            == QgsRelation.RelationStrength.Composition
        )
        # fake composition --{0..1} should be composition
        assert (
            qgis_project.relationManager()
            .relation("classb1_fakecomp_1a_fkey")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )
        # fake composition -<>{0..1} should be composition
        assert (
            qgis_project.relationManager()
            .relation("classb1_fakecomp_2a_fkey")
            .strength()
            == QgsRelation.RelationStrength.Composition
        )

    def test_relation_cardinality_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels//OneToOneRelations.ili"
        )
        importer.configuration.ilimodels = "GeolTest"
        importer.configuration.dbschema = "cardinality_max_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        contact_layer = None
        for layer in available_layers:
            if layer.name == "contact":
                contact_layer = layer
                break
        assert contact_layer

        tab_address = None
        tab_identificator = None
        tab_ahvnr = None
        tab_job = None
        efc = contact_layer.layer.editFormConfig()
        for tab in efc.tabs():
            if tab.name() == "Address":
                tab_address = tab
            elif tab.name() == "Identificator":
                tab_identificator = tab
            elif tab.name() == "AHVNr":
                tab_ahvnr = tab
            elif tab.name() == "Job":
                tab_job = tab
        assert tab_address
        assert tab_identificator
        assert tab_ahvnr
        assert tab_job

        if Qgis.QGIS_VERSION_INT < 31800:
            return

        # At the moment the cardinality_max can be determined exactly only for structures,
        # and the "one_to_one" mode will be set only to those. See also:
        # https://github.com/opengisch/QgisModelBakerLibrary/pull/30#issuecomment-1257912535
        for child in tab_address.children():
            self.assertIn("one_to_one", child.relationEditorConfiguration())
            self.assertTrue(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_identificator.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_ahvnr.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_job.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

    def test_relation_cardinality_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels//OneToOneRelations.ili"
        )
        importer.configuration.ilimodels = "GeolTest"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_cardinality_max_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            DbIliMode.ili2gpkg, uri, importer.configuration.inheritance
        )

        available_layers = generator.layers()
        relations, bags_of_enum = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        contact_layer = None
        for layer in available_layers:
            if layer.name == "contact":
                contact_layer = layer
                break
        assert contact_layer

        tab_address = None
        tab_identificator = None
        tab_ahvnr = None
        tab_job = None
        efc = contact_layer.layer.editFormConfig()
        for tab in efc.tabs():
            if tab.name() == "Address":
                tab_address = tab
            elif tab.name() == "Identificator":
                tab_identificator = tab
            elif tab.name() == "AHVNr":
                tab_ahvnr = tab
            elif tab.name() == "Job":
                tab_job = tab
        assert tab_address
        assert tab_identificator
        assert tab_ahvnr
        assert tab_job

        if Qgis.QGIS_VERSION_INT < 31800:
            return

        # At the moment the cardinality_max can be determined exactly only for structures,
        # and the "one_to_one" mode will be set only to those. See also:
        # https://github.com/opengisch/QgisModelBakerLibrary/pull/30#issuecomment-1257912535
        for child in tab_address.children():
            self.assertIn("one_to_one", child.relationEditorConfiguration())
            self.assertTrue(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_identificator.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_ahvnr.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_job.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

    def test_relation_cardinality_mssql(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels//OneToOneRelations.ili"
        )
        importer.configuration.ilimodels = "GeolTest"
        importer.configuration.dbschema = "cardinality_max_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql, uri, "smart2", importer.configuration.dbschema
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

        contact_layer = None
        for layer in available_layers:
            if layer.name == "contact":
                contact_layer = layer
                break
        assert contact_layer

        tab_address = None
        tab_identificator = None
        tab_ahvnr = None
        tab_job = None
        efc = contact_layer.layer.editFormConfig()
        for tab in efc.tabs():
            if tab.name() == "Address":
                tab_address = tab
            elif tab.name() == "Identificator":
                tab_identificator = tab
            elif tab.name() == "AHVNr":
                tab_ahvnr = tab
            elif tab.name() == "Job":
                tab_job = tab
        assert tab_address
        assert tab_identificator
        assert tab_ahvnr
        assert tab_job

        if Qgis.QGIS_VERSION_INT < 31800:
            return

        # At the moment the cardinality_max can be determined exactly only for structures,
        # and the "one_to_one" mode will be set only to those. See also:
        # https://github.com/opengisch/QgisModelBakerLibrary/pull/30#issuecomment-1257912535
        for child in tab_address.children():
            self.assertIn("one_to_one", child.relationEditorConfiguration())
            self.assertTrue(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_identificator.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_ahvnr.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

        for child in tab_job.children():
            if "one_to_one" in child.relationEditorConfiguration():
                self.assertFalse(child.relationEditorConfiguration()["one_to_one"])

    def test_tid_default_postgis(self):
        """
        When OID defined in INTERLIS - PostgreSQL creates uuid server side.
        When OID not defined in INTERLIS - QGIS should set it with default values.
        """
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbschema = "tid_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
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
            consider_basket_handling=True,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project(context={"catalogue_datasetname": CATALOGUE_DATASETNAME})
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "singleline":
                # default expression since it's not defined in model
                count += 1
                fields = layer.layer.fields()
                field_idx = fields.lookupField("t_ili_tid")
                t_ili_tid_field = fields.field(field_idx)
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "'_' || uuid('WithoutBraces')"
                )
            if layer.name == "station":
                # default expression according model definition (althoug there is a default value server side)
                count += 1
                fields = layer.layer.fields()
                field_idx = fields.lookupField("t_ili_tid")
                t_ili_tid_field = fields.field(field_idx)
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == "uuid('WithoutBraces')"

        # check if the layers have been considered
        assert count == 2

    def test_tid_import_geopackage(self):
        """
        When OID defined in INTERLIS - QGIS should set it with default values.
        When OID not defined in INTERLIS - QGIS should set it with default values.
        """
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, "tmp_tid_gpkg.gpkg"
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            DbIliMode.ili2gpkg,
            uri,
            importer.configuration.inheritance,
            consider_basket_handling=True,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project(context={"catalogue_datasetname": CATALOGUE_DATASETNAME})
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "singleline":
                # default expression since it's not defined in model
                count += 1
                fields = layer.layer.fields()
                field_idx = fields.lookupField("T_Ili_Tid")
                t_ili_tid_field = fields.field(field_idx)
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "'_' || uuid('WithoutBraces')"
                )
            if layer.name == "station":
                # default expression according model definition
                count += 1
                fields = layer.layer.fields()
                field_idx = fields.lookupField("T_Ili_Tid")
                t_ili_tid_field = fields.field(field_idx)
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == "uuid('WithoutBraces')"

        # check if the layers have been considered
        assert count == 2

    def test_tid_import_mssql(self):
        """
        When OID defined in INTERLIS - MSSQL creates uuid server side.
        When OID not defined in INTERLIS - QGIS should set it with default values.
        """
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbschema = "tid_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)

        assert importer.run() == iliimporter.Importer.SUCCESS

        uri = "DRIVER={drv};SERVER={server};DATABASE={db};UID={uid};PWD={pwd}".format(
            drv="{ODBC Driver 17 for SQL Server}",
            server=importer.configuration.dbhost,
            db=importer.configuration.database,
            uid=importer.configuration.dbusr,
            pwd=importer.configuration.dbpwd,
        )

        generator = Generator(
            DbIliMode.ili2mssql,
            uri,
            importer.configuration.inheritance,
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project(context={"catalogue_datasetname": CATALOGUE_DATASETNAME})
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "singleline":
                # default expression since it's not defined in model
                count += 1
                fields = layer.layer.fields()
                field_idx = fields.lookupField("t_ili_tid")
                t_ili_tid_field = fields.field(field_idx)
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert (
                    default_value_definition.expression()
                    == "'_' || uuid('WithoutBraces')"
                )
            if layer.name == "station":
                # default expression according model definition
                count += 1
                fields = layer.layer.fields()
                field_idx = fields.lookupField("t_ili_tid")
                t_ili_tid_field = fields.field(field_idx)
                default_value_definition = t_ili_tid_field.defaultValueDefinition()
                assert default_value_definition is not None
                assert default_value_definition.expression() == "uuid('WithoutBraces')"

        # check if the layers have been considered
        assert count == 2

    def test_kbs_postgis_basket_handling(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbschema = "kbs_lv95_v1_3_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
            consider_basket_handling=True,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project(context={"catalogue_datasetname": CATALOGUE_DATASETNAME})
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the system group for the basket layers
        system_group = qgis_project.layerTreeRoot().findGroup("system")
        assert system_group is not None
        system_group_layers = system_group.findLayers()
        assert {layer.name() for layer in system_group_layers} == {
            "t_ili2db_dataset",
            "t_ili2db_basket",
        }
        """ Temporarily - since ModelBaker does not set the OID correctly - the t_ili2db_basket table is not read only)"""
        assert [
            layer.name() == "t_ili2db_dataset"
            and layer.layer().readOnly()
            or layer.name() == "t_ili2db_basket"
            and not layer.layer().readOnly()
            for layer in system_group_layers
        ] == [
            True,
            True,
        ]

        """ Reuse this test when the layers are both read only again
        assert [layer.layer().readOnly() for layer in system_group_layers] == [
            True,
            True,
        ]
        """

        count = 0
        for layer in available_layers:
            # check the widget configuration of the t_basket field
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig("t_basket")
                assert map["Relation"] == "belasteter_standort_t_basket_fkey"
                assert (
                    map["FilterExpression"]
                    == f"\"topic\" IN ('KbS_LV95_V1_3.Belastete_Standorte') and attribute(get_feature('t_ili2db_dataset', 't_id', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                )

            # check the display expression of the basket table
            if layer.name == "t_ili2db_basket":
                count += 1
                display_expression = layer.layer.displayExpression()
                assert (
                    display_expression
                    == "coalesce(attribute(get_feature('t_ili2db_dataset', 't_id', dataset), 'datasetname') || ' (' || topic || ') ', coalesce( attribute(get_feature('t_ili2db_dataset', 't_id', dataset), 'datasetname'), t_ili_tid))"
                )

        # check if the layers have been considered
        assert count == 2

    def test_kbs_geopackage_basket_handling(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(
            DbIliMode.ili2gpkg, uri, "smart1", consider_basket_handling=True
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project(context={"catalogue_datasetname": CATALOGUE_DATASETNAME})
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the system group for the basket layers
        system_group = qgis_project.layerTreeRoot().findGroup("system")
        assert system_group is not None
        system_group_layers = system_group.findLayers()
        assert {layer.name() for layer in system_group_layers} == {
            "T_ILI2DB_DATASET",
            "T_ILI2DB_BASKET",
        }

        """ Temporarily - since ModelBaker does not set the OID correctly - the t_ili2db_basket table is not read only)"""
        assert [
            layer.name() == "T_ILI2DB_DATASET"
            and layer.layer().readOnly()
            or layer.name() == "T_ILI2DB_BASKET"
            and not layer.layer().readOnly()
            for layer in system_group_layers
        ] == [
            True,
            True,
        ]

        """ Reuse this test when the layers are both read only again
        assert [layer.layer().readOnly() for layer in system_group_layers] == [
            True,
            True,
        ]
        """

        count = 0
        for layer in available_layers:
            # check the widget configuration of the t_basket field
            if layer.name == "belasteter_standort":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                map = edit_form_config.widgetConfig("T_basket")
                assert (
                    map["Relation"]
                    == "belasteter_standort_T_basket_T_ILI2DB_BASKET_T_Id"
                )
                assert (
                    map["FilterExpression"]
                    == f"\"topic\" IN ('KbS_LV95_V1_3.Belastete_Standorte') and attribute(get_feature('T_ILI2DB_DATASET', 'T_Id', \"dataset\"), 'datasetname') != '{CATALOGUE_DATASETNAME}'"
                )

            # check the display expression of the basket table
            if layer.name == "T_ILI2DB_BASKET":
                count += 1
                display_expression = layer.layer.displayExpression()
                assert (
                    display_expression
                    == "coalesce(attribute(get_feature('T_ILI2DB_DATASET', 'T_Id', dataset), 'datasetname') || ' (' || topic || ') ', coalesce( attribute(get_feature('T_ILI2DB_DATASET', 'T_Id', dataset), 'datasetname'), T_Ili_Tid))"
                )

        # check if the layers have been considered
        assert count == 2

    def test_kbs_postgis_toppings(self):
        """
        Reads this metaconfig found in ilidata.xml according to the modelname KbS_LV95_V1_4

        [CONFIGURATION]
        qgis.modelbaker.layertree=file:testdata/ilirepo/usabilityhub/projecttopping/opengis_layertree_KbS_LV95_V1_4.yaml
        ch.interlis.referenceData=ilidata:ch.sh.ili.catalogue.KbS_Codetexte_V1_4

        [ch.ehi.ili2db]
        defaultSrsCode=3857
        models=KbS_Basis_V1_4
        preScript=file:testdata/ilirepo/usabilityhub/sql/opengisch_KbS_LV95_V1_4_test.sql
        iliMetaAttrs=ilidata:ch.opengis.config.KbS_LV95_V1_4_toml

        [qgis.modelbaker.qml]
        "Belasteter_Standort (Geo_Lage_Polygon)"=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001
        "Belasteter_Standort (Geo_Lage_Punkt)"=file:testdata/ilirepo/usabilityhub/layerstyle/opengisch_KbS_LV95_V1_4_001_belasteterstandort_punkt.qml
        Parzellenidentifikation=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005
        """

        toppings_test_path = os.path.join(
            test_path, "testdata", "ilirepo", "usabilityhub"
        )

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(
            importer.tool,
            os.path.join(test_path, "testdata", "ilirepo", "usabilityhub"),
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbschema = "toppings_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        # get the metaconfiguration
        ilimetaconfigcache = IliDataCache(
            configuration=importer.configuration.base_configuration,
            models="KbS_LV95_V1_4",
        )
        ilimetaconfigcache.refresh()

        self._sleep(ilimetaconfigcache.model)

        matches_on_id = ilimetaconfigcache.model.match(
            ilimetaconfigcache.model.index(0, 0),
            int(IliDataItemModel.Roles.ID),
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_localfiletest",
            1,
            Qt.MatchFlag.MatchExactly,
        )
        assert bool(matches_on_id) is True

        repository = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ILIREPO)
        )
        url = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.URL)
        )
        path = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.RELATIVEFILEPATH)
        )
        dataset_id = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ID)
        )

        metaconfig_path = ilimetaconfigcache.download_file(
            repository, url, path, dataset_id
        )
        metaconfig = self.load_metaconfig(
            os.path.join(toppings_test_path, metaconfig_path)
        )

        # Read ili2db settings
        assert "ch.ehi.ili2db" in metaconfig.sections()
        ili2db_metaconfig = metaconfig["ch.ehi.ili2db"]
        model_list = importer.configuration.ilimodels.strip().split(
            ";"
        ) + ili2db_metaconfig.get("models").strip().split(";")
        importer.configuration.ilimodels = ";".join(model_list)
        assert importer.configuration.ilimodels == "KbS_LV95_V1_4;KbS_Basis_V1_4"
        srs_code = ili2db_metaconfig.get("defaultSrsCode")
        importer.configuration.srs_code = srs_code
        assert importer.configuration.srs_code == "3857"
        command = importer.command(True)
        assert "KbS_LV95_V1_4;KbS_Basis_V1_4" in command
        assert "3857" in command

        # read and download topping files in ili2db settings (prefixed with ilidata or file - means they are found in ilidata.xml or referenced locally)
        ili_meta_attrs_list = ili2db_metaconfig.get("iliMetaAttrs").split(";")
        ili_meta_attrs_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, ili_meta_attrs_list
        )
        # absolute path since it's defined as ilidata:...
        expected_ili_meta_attrs_file_path_list = [
            os.path.join(toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml")
        ]
        assert expected_ili_meta_attrs_file_path_list == ili_meta_attrs_file_path_list
        importer.configuration.tomlfile = ili_meta_attrs_file_path_list[0]

        prescript_list = ili2db_metaconfig.get("preScript").split(";")
        prescript_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, prescript_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_prescript_file_path_list = [
            os.path.join(toppings_test_path, "sql/opengisch_KbS_LV95_V1_4_test.sql")
        ]
        assert expected_prescript_file_path_list == prescript_file_path_list
        importer.configuration.pre_script = prescript_file_path_list[0]

        command = importer.command(True)
        assert "opengisch_KbS_LV95_V1_4_test.sql" in command
        assert "sh_KbS_LV95_V1_4.toml" in command

        # and override defaultSrsCode manually
        importer.configuration.srs_code = "2056"

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        # Toppings legend and layers: apply
        assert "CONFIGURATION" in metaconfig.sections()
        configuration_section = metaconfig["CONFIGURATION"]
        assert "qgis.modelbaker.layertree" in configuration_section
        layertree_data_list = configuration_section["qgis.modelbaker.layertree"].split(
            ";"
        )
        layertree_data_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, layertree_data_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_layertree_data_file_path_list = [
            os.path.join(
                toppings_test_path,
                "projecttopping/opengis_layertree_KbS_LV95_V1_4.yaml",
            )
        ]
        assert layertree_data_file_path_list == expected_layertree_data_file_path_list
        layertree_data_file_path = layertree_data_file_path_list[0]

        custom_layer_order_structure = list()
        with open(layertree_data_file_path) as yamlfile:
            layertree_data = yaml.safe_load(yamlfile)
            assert "legend" in layertree_data
            legend = generator.legend(
                available_layers, layertree_structure=layertree_data["legend"]
            )
            assert "layer-order" in layertree_data
            custom_layer_order_structure = layertree_data["layer-order"]

        assert len(custom_layer_order_structure) == 2

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.custom_layer_order_structure = custom_layer_order_structure
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the legend with layers, groups and subgroups
        belasteter_standort_group = qgis_project.layerTreeRoot().findGroup(
            "Belasteter Standort"
        )
        assert belasteter_standort_group is not None
        belasteter_standort_group_layer = belasteter_standort_group.findLayers()
        assert [layer.name() for layer in belasteter_standort_group_layer] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort (Geo_Lage_Polygon)",
        ]
        informationen_group = qgis_project.layerTreeRoot().findGroup("Informationen")
        assert informationen_group is not None
        informationen_group_layers = informationen_group.findLayers()
        assert [layer.name() for layer in informationen_group_layers] == [
            "EGRID_",
            "Deponietyp_",
            "ZustaendigkeitKataster",
            "Untersuchungsmassnahmen_Definition",
            "StatusAltlV_Definition",
            "Standorttyp_Definition",
            "Deponietyp_Definition",
            "Parzellenidentifikation",
            "UntersMassn_",
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]

        text_infos_group = informationen_group.findGroup("Text Infos")
        assert text_infos_group is not None
        text_infos_group_layers = text_infos_group.findLayers()
        assert [layer.name() for layer in text_infos_group_layers] == [
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
        ]
        other_infos_group = informationen_group.findGroup("Other Infos")
        self.assertIsNotNone(other_infos_group)
        other_infos_group_layers = other_infos_group.findLayers()
        assert [layer.name() for layer in other_infos_group_layers] == [
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]
        # check the node properties
        belasteter_standort_punkt_layer = None
        belasteter_standort_polygon_layer = None
        for layer in belasteter_standort_group_layer:
            if layer.name() == "Belasteter_Standort (Geo_Lage_Punkt)":
                belasteter_standort_punkt_layer = layer
            if layer.name() == "Belasteter_Standort (Geo_Lage_Polygon)":
                belasteter_standort_polygon_layer = layer
        assert belasteter_standort_punkt_layer is not None
        assert belasteter_standort_polygon_layer is not None
        assert belasteter_standort_group.isMutuallyExclusive() is True
        assert (
            belasteter_standort_punkt_layer.isVisible() is False
        )  # because of the mutually-child
        assert (
            belasteter_standort_polygon_layer.isVisible() is True
        )  # because of the mutually-child
        assert belasteter_standort_punkt_layer.isExpanded() is False
        assert belasteter_standort_polygon_layer.isExpanded() is True
        assert (
            bool(belasteter_standort_punkt_layer.customProperty("showFeatureCount"))
            is True
        )
        assert (
            bool(belasteter_standort_polygon_layer.customProperty("showFeatureCount"))
            is False
        )
        egrid_layer = None
        zustaendigkeitkataster_layer = None
        for layer in informationen_group_layers:
            if layer.name() == "EGRID_":
                egrid_layer = layer
            if layer.name() == "ZustaendigkeitKataster":
                zustaendigkeitkataster_layer = layer
        assert egrid_layer is not None
        assert zustaendigkeitkataster_layer is not None
        assert bool(egrid_layer.customProperty("showFeatureCount")) is False
        assert (
            bool(zustaendigkeitkataster_layer.customProperty("showFeatureCount"))
            is True
        )
        assert text_infos_group.isExpanded() is True
        assert text_infos_group.isVisible() is False
        assert other_infos_group.isVisible() is True
        assert other_infos_group.isExpanded() is False

        # check the custom layer order
        assert bool(qgis_project.layerTreeRoot().hasCustomLayerOrder()) is True
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[0].name()
            == "Belasteter_Standort (Geo_Lage_Polygon)"
        )
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[1].name()
            == "Belasteter_Standort (Geo_Lage_Punkt)"
        )

        # and read qml part, download files and check the form configurations set by the qml
        assert "qgis.modelbaker.qml" in metaconfig.sections()
        qml_section = dict(metaconfig["qgis.modelbaker.qml"])
        assert list(qml_section.values()) == [
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            "file:testdata/ilirepo/usabilityhub/layerstyle/opengisch_KbS_LV95_V1_4_004_belasteterstandort_punkt.qml",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005",
        ]
        qml_file_model = self.get_topping_file_model(
            importer.configuration.base_configuration,
            list(qml_section.values()),
            test_path,
        )
        for layer in project.layers:
            if layer.alias:
                if any(layer.alias.lower() == s for s in qml_section):
                    layer_qml = layer.alias.lower()
                elif any(f'"{layer.alias.lower()}"' == s for s in qml_section):
                    layer_qml = f'"{layer.alias.lower()}"'
                else:
                    continue
                matches = qml_file_model.match(
                    qml_file_model.index(0, 0),
                    Qt.ItemDataRole.DisplayRole,
                    qml_section[layer_qml],
                    1,
                )
                if matches:
                    style_file_path = matches[0].data(
                        int(IliToppingFileItemModel.Roles.LOCALFILEPATH)
                    )
                    layer.layer.loadNamedStyle(style_file_path)

        layer_names = {layer.name for layer in available_layers}
        assert layer_names == {
            "untersuchungsmassnahmen_definition",
            "statusaltlv_definition",
            "untersmassn",
            "deponietyp_definition",
            "parzellenidentifikation",
            "multilingualtext",
            "languagecode_iso639_1",
            "belasteter_standort",
            "zustaendigkeitkataster",
            "deponietyp_",
            "standorttyp",
            "localisedtext",
            "multilingualmtext",
            "untersmassn_",
            "statusaltlv",
            "localisedmtext",
            "standorttyp_definition",
            "egrid_",
            "deponietyp",
        }

        count = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert (
                    edit_form_config.layout()
                    == QgsEditFormConfig.EditorLayout.TabLayout
                )
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert tabs[0].name() == "Allgemein"
                field_names = {field.name() for field in tabs[0].children()}
                assert field_names == {
                    "geo_lage_polygon",
                    "bemerkung_de",
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "url_standort",
                    "bemerkung_rm",
                    "standorttyp",
                    "bemerkung_en",
                    "inbetrieb",
                    "geo_lage_punkt",
                    "bemerkung_it",
                    "url_kbs_auszug",
                    "bemerkung",
                    "nachsorge",
                    "ersteintrag",
                    "bemerkung_fr",
                    "katasternummer",
                    "statusaltlv",
                }

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

    def test_kbs_geopackage_toppings(self):
        """
        Reads this metaconfig found in ilidata.xml according to the modelname KbS_LV95_V1_4

        [CONFIGURATION]
        qgis.modelbaker.layertree=file:testdata/ilirepo/usabilityhub/projecttopping/opengis_layertree_KbS_LV95_V1_4_GPKG.yaml
        ch.interlis.referenceData=ilidata:ch.sh.ili.catalogue.KbS_Codetexte_V1_4

        [ch.ehi.ili2db]
        models = KbS_Basis_V1_4
        iliMetaAttrs=ilidata:ch.opengis.config.KbS_LV95_V1_4_toml
        preScript=file:testdata/ilirepo/usabilityhub/sql/opengisch_KbS_LV95_V1_4_test.sql
        defaultSrsCode=3857

        [qgis.modelbaker.qml]
        "Belasteter_Standort"=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001
        "Belasteter_Standort (Geo_Lage_Punkt)"=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004
        Parzellenidentifikation=ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005
        """

        toppings_test_path = os.path.join(
            test_path, "testdata", "ilirepo", "usabilityhub"
        )

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(
            importer.tool,
            os.path.join(test_path, "testdata", "ilirepo", "usabilityhub"),
        )
        importer.configuration.ilimodels = "KbS_LV95_V1_4"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_toppings_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )

        # get the metaconfiguration
        ilimetaconfigcache = IliDataCache(
            configuration=importer.configuration.base_configuration,
            models="KbS_LV95_V1_4",
        )
        ilimetaconfigcache.refresh()

        self._sleep(ilimetaconfigcache.model)

        matches_on_id = ilimetaconfigcache.model.match(
            ilimetaconfigcache.model.index(0, 0),
            int(IliDataItemModel.Roles.ID),
            "ch.opengis.ili.config.KbS_LV95_V1_4_config_V1_0_gpkg_localfiletest",
            1,
            Qt.MatchFlag.MatchExactly,
        )
        assert bool(matches_on_id) is True

        repository = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ILIREPO)
        )
        url = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.URL)
        )
        path = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.RELATIVEFILEPATH)
        )
        dataset_id = ilimetaconfigcache.model.data(
            matches_on_id[0], int(IliDataItemModel.Roles.ID)
        )

        metaconfig_path = ilimetaconfigcache.download_file(
            repository, url, path, dataset_id
        )
        metaconfig = self.load_metaconfig(
            os.path.join(toppings_test_path, metaconfig_path)
        )

        # Read ili2db settings
        assert "ch.ehi.ili2db" in metaconfig.sections()
        ili2db_metaconfig = metaconfig["ch.ehi.ili2db"]
        model_list = importer.configuration.ilimodels.strip().split(
            ";"
        ) + ili2db_metaconfig.get("models").strip().split(";")
        importer.configuration.ilimodels = ";".join(model_list)
        assert importer.configuration.ilimodels == "KbS_LV95_V1_4;KbS_Basis_V1_4"
        srs_code = ili2db_metaconfig.get("defaultSrsCode")
        importer.configuration.srs_code = srs_code
        assert importer.configuration.srs_code == "3857"
        command = importer.command(True)
        assert "KbS_LV95_V1_4;KbS_Basis_V1_4" in command
        assert "3857" in command

        # read and download topping files in ili2db settings (prefixed with ilidata or file - means they are found in ilidata.xml or referenced locally)
        ili_meta_attrs_list = ili2db_metaconfig.get("iliMetaAttrs").split(";")
        ili_meta_attrs_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, ili_meta_attrs_list
        )
        # absolute path since it's defined as ilidata:...
        expected_ili_meta_attrs_file_path_list = [
            os.path.join(toppings_test_path, "metaattributes/sh_KbS_LV95_V1_4.toml")
        ]
        assert expected_ili_meta_attrs_file_path_list == ili_meta_attrs_file_path_list
        importer.configuration.tomlfile = ili_meta_attrs_file_path_list[0]

        prescript_list = ili2db_metaconfig.get("preScript").split(";")
        prescript_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, prescript_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_prescript_file_path_list = [
            os.path.join(toppings_test_path, "sql/opengisch_KbS_LV95_V1_4_test.sql")
        ]
        assert expected_prescript_file_path_list == prescript_file_path_list
        importer.configuration.pre_script = prescript_file_path_list[0]

        command = importer.command(True)
        assert "opengisch_KbS_LV95_V1_4_test.sql" in command
        assert "sh_KbS_LV95_V1_4.toml" in command

        # and override defaultSrsCode manually
        importer.configuration.srs_code = "2056"

        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS
        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()
        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        available_layers = generator.layers()
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        # Toppings legend and layers: apply
        assert "CONFIGURATION" in metaconfig.sections()
        configuration_section = metaconfig["CONFIGURATION"]
        assert "qgis.modelbaker.layertree" in configuration_section
        layertree_data_list = configuration_section["qgis.modelbaker.layertree"].split(
            ";"
        )
        layertree_data_file_path_list = self.get_topping_file_list(
            importer.configuration.base_configuration, layertree_data_list
        )
        # relative path made absolute to modelbaker since it's defined as file:...
        expected_layertree_data_file_path_list = [
            os.path.join(
                toppings_test_path,
                "projecttopping/opengis_layertree_KbS_LV95_V1_4_GPKG.yaml",
            )
        ]
        assert layertree_data_file_path_list == expected_layertree_data_file_path_list
        layertree_data_file_path = layertree_data_file_path_list[0]

        custom_layer_order_structure = list()
        with open(layertree_data_file_path) as yamlfile:
            layertree_data = yaml.safe_load(yamlfile)
            assert "legend" in layertree_data
            legend = generator.legend(
                available_layers, layertree_structure=layertree_data["legend"]
            )
            assert "layer-order" in layertree_data
            custom_layer_order_structure = layertree_data["layer-order"]

        assert len(custom_layer_order_structure) == 2

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.custom_layer_order_structure = custom_layer_order_structure
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        # check the legend with layers, groups and subgroups
        belasteter_standort_group = qgis_project.layerTreeRoot().findGroup(
            "Belasteter Standort"
        )
        assert belasteter_standort_group is not None
        belasteter_standort_group_layer = belasteter_standort_group.findLayers()
        assert [layer.name() for layer in belasteter_standort_group_layer] == [
            "Belasteter_Standort (Geo_Lage_Punkt)",
            "Belasteter_Standort",
        ]

        informationen_group = qgis_project.layerTreeRoot().findGroup("Informationen")
        assert informationen_group is not None
        informationen_group_layers = informationen_group.findLayers()

        assert [layer.name() for layer in informationen_group_layers] == [
            "EGRID_",
            "Deponietyp_",
            "ZustaendigkeitKataster",
            "Untersuchungsmassnahmen_Definition",
            "StatusAltlV_Definition",
            "Standorttyp_Definition",
            "Deponietyp_Definition",
            "Parzellenidentifikation",
            "UntersMassn_",
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]

        text_infos_group = informationen_group.findGroup("Text Infos")
        assert text_infos_group is not None
        text_infos_group_layers = text_infos_group.findLayers()
        assert [layer.name() for layer in text_infos_group_layers] == [
            "MultilingualMText",
            "LocalisedMText",
            "MultilingualText",
            "LocalisedText",
        ]
        other_infos_group = informationen_group.findGroup("Other Infos")
        assert other_infos_group is not None
        other_infos_group_layers = other_infos_group.findLayers()
        assert [layer.name() for layer in other_infos_group_layers] == [
            "StatusAltlV",
            "Standorttyp",
            "UntersMassn",
            "Deponietyp",
            "LanguageCode_ISO639_1",
        ]
        # check the node properties
        belasteter_standort_punkt_layer = None
        belasteter_standort_polygon_layer = None
        for layer in belasteter_standort_group_layer:
            if layer.name() == "Belasteter_Standort (Geo_Lage_Punkt)":
                belasteter_standort_punkt_layer = layer
            if layer.name() == "Belasteter_Standort":
                belasteter_standort_polygon_layer = layer
        assert belasteter_standort_punkt_layer is not None
        assert belasteter_standort_polygon_layer is not None
        assert (
            belasteter_standort_punkt_layer.isVisible() is False
        )  # because of yaml setting
        assert (
            belasteter_standort_polygon_layer.isVisible() is True
        )  # because of yaml setting
        assert belasteter_standort_punkt_layer.isExpanded() is False
        assert belasteter_standort_polygon_layer.isExpanded() is True
        assert (
            bool(belasteter_standort_punkt_layer.customProperty("showFeatureCount"))
            is True
        )
        assert (
            bool(belasteter_standort_polygon_layer.customProperty("showFeatureCount"))
            is False
        )
        egrid_layer = None
        zustaendigkeitkataster_layer = None
        for layer in informationen_group_layers:
            if layer.name() == "EGRID_":
                egrid_layer = layer
            if layer.name() == "ZustaendigkeitKataster":
                zustaendigkeitkataster_layer = layer
        assert egrid_layer is not None
        assert zustaendigkeitkataster_layer is not None
        assert bool(egrid_layer.customProperty("showFeatureCount")) is False
        assert (
            bool(zustaendigkeitkataster_layer.customProperty("showFeatureCount"))
            is True
        )
        assert text_infos_group.isExpanded() is True
        assert text_infos_group.isVisible() is False
        assert other_infos_group.isVisible() is True
        assert other_infos_group.isExpanded() is False

        # check the custom layer order
        assert bool(qgis_project.layerTreeRoot().hasCustomLayerOrder()) is True
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[0].name()
            == "Belasteter_Standort"
        )
        assert (
            qgis_project.layerTreeRoot().customLayerOrder()[1].name()
            == "Belasteter_Standort (Geo_Lage_Punkt)"
        )

        # and read qml part, download files and check the form configurations set by the qml
        assert "qgis.modelbaker.qml" in metaconfig.sections()
        qml_section = dict(metaconfig["qgis.modelbaker.qml"])
        assert list(qml_section.values()) == [
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_001",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_004_GPKG",
            "ilidata:ch.opengis.topping.opengisch_KbS_LV95_V1_4_005",
        ]
        qml_file_model = self.get_topping_file_model(
            importer.configuration.base_configuration,
            list(qml_section.values()),
            test_path,
        )
        for layer in project.layers:
            if layer.alias:
                if any(layer.alias.lower() == s for s in qml_section):
                    layer_qml = layer.alias.lower()
                elif any(f'"{layer.alias.lower()}"' == s for s in qml_section):
                    layer_qml = f'"{layer.alias.lower()}"'
                else:
                    continue
                matches = qml_file_model.match(
                    qml_file_model.index(0, 0),
                    Qt.ItemDataRole.DisplayRole,
                    qml_section[layer_qml],
                    1,
                )
                if matches:
                    style_file_path = matches[0].data(
                        int(IliToppingFileItemModel.Roles.LOCALFILEPATH)
                    )
                    layer.layer.loadNamedStyle(style_file_path)

        layer_names = {layer.name for layer in available_layers}
        assert layer_names == {
            "untersuchungsmassnahmen_definition",
            "statusaltlv_definition",
            "untersmassn",
            "deponietyp_definition",
            "parzellenidentifikation",
            "multilingualtext",
            "languagecode_iso639_1",
            "belasteter_standort",
            "zustaendigkeitkataster",
            "deponietyp_",
            "standorttyp",
            "localisedtext",
            "multilingualmtext",
            "untersmassn_",
            "statusaltlv",
            "localisedmtext",
            "standorttyp_definition",
            "egrid_",
            "deponietyp",
            "belasteter_standort_geo_lage_punkt",
        }

        count = 0
        for layer in available_layers:
            if layer.name == "belasteter_standort":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert (
                    edit_form_config.layout()
                    == QgsEditFormConfig.EditorLayout.TabLayout
                )
                tabs = edit_form_config.tabs()
                assert len(tabs) == 5
                assert tabs[0].name() == "Allgemein"
                field_names = {field.name() for field in tabs[0].children()}
                assert field_names == {
                    "geo_lage_polygon",
                    "bemerkung_de",
                    "letzteanpassung",
                    "zustaendigkeitkataster",
                    "url_standort",
                    "bemerkung_rm",
                    "standorttyp",
                    "bemerkung_en",
                    "inbetrieb",
                    "geo_lage_punkt",
                    "bemerkung_it",
                    "url_kbs_auszug",
                    "bemerkung",
                    "nachsorge",
                    "ersteintrag",
                    "bemerkung_fr",
                    "katasternummer",
                    "statusaltlv",
                }

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

    def test_kbs_postgis_multisurface(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.tomlfile = testdata_path("toml/multisurface.toml")
        importer.configuration.dbschema = "kbs_lv95_v1_3_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            "smart1",
            importer.configuration.dbschema,
        )

        available_layers = generator.layers()

        count = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count += 1
                assert layer.alias == "Belasteter_Standort (Geo_Lage_Punkt)"

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count += 1
                assert layer.alias == "Belasteter_Standort (Geo_Lage_Polygon)"

        assert count == 2

    def test_kbs_geopackage_multisurface(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "KbS_LV95_V1_3"
        importer.configuration.tomlfile = testdata_path("toml/multisurface.toml")
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_import_kbs_gpkg_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.inheritance = "smart1"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart1")

        available_layers = generator.layers()

        count = 0
        for layer in available_layers:
            if (
                layer.name == "belasteter_standort_geo_lage_punkt"
                and layer.geometry_column == "geo_lage_punkt"
            ):
                count += 1
                assert layer.alias == "Belasteter_Standort (Geo_Lage_Punkt)"

            if (
                layer.name == "belasteter_standort"
                and layer.geometry_column == "geo_lage_polygon"
            ):
                count += 1
                assert layer.alias == "Belasteter_Standort"

        assert count == 2

    def test_unit(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool, "ilimodels")
        importer.configuration.ilimodels = (
            "ZG_Naturschutz_und_Erholungsinfrastruktur_V1"
        )

        importer.configuration.dbschema = "nue_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.create_basket_col = True
        importer.configuration.srs_code = 21781
        importer.configuration.inheritance = "smart2"
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

        infra_po = next(
            layer
            for layer in available_layers
            if layer.name == "erholungsinfrastruktur_punktobjekt"
        )
        naechste_kontrolle = next(
            field for field in infra_po.fields if field.name == "naechste_kontrolle"
        )
        assert naechste_kontrolle.alias == "Naechste_Kontrolle"

    def test_array_mapping_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/ArrayMapping.ili")
        importer.configuration.ilimodels = "ArrayMapping"
        importer.configuration.dbschema = "array_mapping_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "theclass":
                type = (
                    layer.layer.fields().field("itemsarray").editorWidgetSetup().type()
                )
                self.assertEqual(type, "List")
                type = (
                    layer.layer.fields()
                    .field("itemsarraybag")
                    .editorWidgetSetup()
                    .type()
                )
                self.assertEqual(type, "List")
                count += 1

        assert count == 1

    def test_array_mapping_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/ArrayMapping.ili")
        importer.configuration.ilimodels = "ArrayMapping"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_array_mapping_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

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

        count = 0
        for layer in available_layers:
            if layer.name == "theclass":
                type = (
                    layer.layer.fields().field("itemsarray").editorWidgetSetup().type()
                )
                self.assertEqual(type, "List")
                type = (
                    layer.layer.fields()
                    .field("itemsarraybag")
                    .editorWidgetSetup()
                    .type()
                )
                self.assertEqual(type, "List")
                count += 1

        assert count == 1

    def test_array_mapping_mssql(self):

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2mssql
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/ArrayMapping.ili")
        importer.configuration.ilimodels = "ArrayMapping"
        importer.configuration.dbschema = "array_mapping_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )

        importer.configuration.inheritance = "smart2"
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
        relations, _ = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend
        project.post_generate()

        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)

        count = 0
        for layer in available_layers:
            if layer.name == "theclass":
                type = (
                    layer.layer.fields().field("itemsarray").editorWidgetSetup().type()
                )
                self.assertEqual(type, "List")
                count += 1

        assert count == 1

    def test_catalogue_reference_layer_bag_of_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/gebaeude_bag_of_V1_6.ili"
        )
        importer.configuration.ilimodels = "Gebaeudeinventar_Bag_Of_V1_6"
        importer.configuration.dbschema = (
            "catalogue_ref_bag_of_{:%Y%m%d%H%M%S%f}".format(datetime.datetime.now())
        )

        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
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
        relations, bags_of = generator.relations(available_layers)

        layer_count_before = len(available_layers)
        relation_count_before = len(relations)

        available_layers, relations = generator.suppress_catalogue_reference_layers(
            available_layers, relations, bags_of
        )

        layer_count_after = len(available_layers)
        relation_count_after = len(relations)

        # Test that no reference layer and therefore, no relation, has been removed
        assert layer_count_before == layer_count_after
        assert relation_count_before == relation_count_after

    def test_catalogue_reference_layer_bag_of_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/gebaeude_bag_of_V1_6.ili"
        )
        importer.configuration.ilimodels = "Gebaeudeinventar_Bag_Of_V1_6"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_catalogue_ref_bag_of_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS
        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, bags_of = generator.relations(available_layers)

        layer_count_before = len(available_layers)
        relation_count_before = len(relations)

        available_layers, relations = generator.suppress_catalogue_reference_layers(
            available_layers, relations, bags_of
        )

        layer_count_after = len(available_layers)
        relation_count_after = len(relations)

        # Test that no reference layer and therefore, no relation, has been removed
        assert layer_count_before == layer_count_after
        assert relation_count_before == relation_count_after

    def test_catalogue_reference_layer_list_of_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/gebaeude_list_of_V1_6.ili"
        )
        importer.configuration.ilimodels = "Gebaeudeinventar_List_Of_V1_6"
        importer.configuration.dbschema = (
            "catalogue_ref_list_of_{:%Y%m%d%H%M%S%f}".format(datetime.datetime.now())
        )

        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
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
        relations, bags_of = generator.relations(available_layers)

        layer_count_before = len(available_layers)
        relation_count_before = len(relations)

        available_layers, relations = generator.suppress_catalogue_reference_layers(
            available_layers, relations, bags_of
        )

        layer_count_after = len(available_layers)
        relation_count_after = len(relations)

        # Test that no reference layer and therefore, no relation, has been removed
        assert layer_count_before == layer_count_after
        assert relation_count_before == relation_count_after

    def test_catalogue_reference_layer_list_of_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/gebaeude_list_of_V1_6.ili"
        )
        importer.configuration.ilimodels = "Gebaeudeinventar_List_Of_V1_6"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_catalogue_ref_list_of_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS
        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, bags_of = generator.relations(available_layers)

        layer_count_before = len(available_layers)
        relation_count_before = len(relations)

        available_layers, relations = generator.suppress_catalogue_reference_layers(
            available_layers, relations, bags_of
        )

        layer_count_after = len(available_layers)
        relation_count_after = len(relations)

        # Test that no reference layer and therefore, no relation, has been removed
        assert layer_count_before == layer_count_after
        assert relation_count_before == relation_count_after

    def test_catalogue_reference_layer_no_bag_of_postgis(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/gebaeude_V1_6.ili")
        importer.configuration.ilimodels = "Gebaeudeinventar_V1_6"
        importer.configuration.dbschema = (
            "catalogue_ref_no_bag_of_{:%Y%m%d%H%M%S%f}".format(datetime.datetime.now())
        )

        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
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
        relations, bags_of = generator.relations(available_layers)

        layer_count_before = len(available_layers)
        relation_count_before = len(relations)

        available_layers, relations = generator.suppress_catalogue_reference_layers(
            available_layers, relations, bags_of
        )

        layer_count_after = len(available_layers)
        relation_count_after = len(relations)

        # Test that one layer and one relation have been removed
        assert layer_count_before == layer_count_after + 1
        assert relation_count_before == relation_count_after + 1

    def test_catalogue_reference_layer_no_bag_of_geopackage(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/gebaeude_V1_6.ili")
        importer.configuration.ilimodels = "Gebaeudeinventar_V1_6"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_catalogue_ref_no_bag_of_{:%Y%m%d%H%M%S%f}.gpkg".format(
                datetime.datetime.now()
            ),
        )
        importer.configuration.srs_code = 2056
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS
        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

        available_layers = generator.layers()
        relations, bags_of = generator.relations(available_layers)

        layer_count_before = len(available_layers)
        relation_count_before = len(relations)

        available_layers, relations = generator.suppress_catalogue_reference_layers(
            available_layers, relations, bags_of
        )

        layer_count_after = len(available_layers)
        relation_count_after = len(relations)

        # Test that one layer and one relation have been removed
        assert layer_count_before == layer_count_after + 1
        assert relation_count_before == relation_count_after + 1

    def test_relation_editor_widget_for_no_geometry_layers(self):

        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path("ilimodels/Maps_V1.ili")
        importer.configuration.ilimodels = "Maps_V1"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_array_mapping_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.srs_code = 3116
        importer.configuration.inheritance = "smart2"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        config_manager = GpkgCommandConfigManager(importer.configuration)
        uri = config_manager.get_uri()

        generator = Generator(DbIliMode.ili2gpkg, uri, "smart2")

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

        count = 0
        for layer in available_layers:
            if layer.name == "amap":
                count += 1
                edit_form_config = layer.layer.editFormConfig()
                assert (
                    edit_form_config.layout()
                    == QgsEditFormConfig.EditorLayout.TabLayout
                )
                tabs = edit_form_config.tabs()

                if Qgis.QGIS_VERSION_INT >= 31600:
                    tab_list = [tab.name() for tab in tabs]
                    expected_tab_list = [
                        "General",
                        "MapHierItem",
                    ]
                    assert set(tab_list) == set(expected_tab_list)
                    assert len(tab_list) == len(expected_tab_list)

        assert count == 1

        count = 0
        # when the referencing layer is a structure, it should be a composition
        for relation in relations:
            if relation.referencing_layer.name == "maphierref":
                assert relation.strength == QgsRelation.RelationStrength.Composition
                count += 1

        assert count == 2

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()

    def load_metaconfig(self, path):
        metaconfig = configparser.ConfigParser()
        metaconfig.clear()
        metaconfig.read_file(open(path))
        metaconfig.read(path)
        return metaconfig

    # that's the same like in generate_project.py and workflow_wizard.py
    def get_topping_file_list(self, base_config, id_list):
        topping_file_model = self.get_topping_file_model(
            base_config, id_list, test_path
        )
        file_path_list = []

        for file_id in id_list:
            matches = topping_file_model.match(
                topping_file_model.index(0, 0), Qt.ItemDataRole.DisplayRole, file_id, 1
            )
            if matches:
                file_path = matches[0].data(int(topping_file_model.Roles.LOCALFILEPATH))
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, base_config, id_list, tool_dir=None):
        topping_file_cache = IliToppingFileCache(base_config, id_list, tool_dir)

        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        topping_file_cache.download_finished_and_model_fresh.connect(
            lambda: loop.quit()
        )
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(30000)

        topping_file_cache.refresh()

        if len(topping_file_cache.downloaded_files) != len(id_list):
            loop.exec()

        # since the local download is quicker than the delay in the model refresh, we make one here as well
        self._sleep(mili=3000)

        return topping_file_cache.model

    def _sleep(self, model=None, mili=10000):
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        if model:
            model.modelReset.connect(lambda: loop.quit())
        timer.start(mili)
        loop.exec()

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
