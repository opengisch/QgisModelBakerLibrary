"""
Metadata:
    Creation Date: 2024-10-31
    Copyright: (C) 2024 by Germán Carrillo
    Contact: german@opengisch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""


import datetime
import logging
import os
import pathlib
import shutil
import tempfile

from qgis.core import QgsProject
from qgis.testing import start_app, unittest

import modelbaker.utils.db_utils as db_utils
from modelbaker.dataobjects.project import Project
from modelbaker.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager
from modelbaker.generator.generator import Generator
from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import get_pg_connection_string, iliimporter_config

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestTranslations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_translated_db_objects_gpkg(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "PlansDAffectation_V1_2"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_translated_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
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
            preferred_language="fr",
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
        fr_layer = None
        for layer in available_layers:
            if layer.name == "grundnutzung_zonenflaeche":
                assert layer.alias == "AffectationPrimaire_SurfaceDeZones"
                fr_layer = layer.layer
                count += 1
                fields = fr_layer.fields()
                field_idx = fields.lookupField("publiziertab")
                assert field_idx != -1
                field = fields.field(field_idx)
                assert field.name() == "publiziertab"
                assert field.alias() == "publieDepuis"

                edit_form_config = fr_layer.editFormConfig()
                tabs = edit_form_config.tabs()
                tab_list = [tab.name() for tab in tabs]
                expected_tab_list = [
                    "General",
                    "Document",
                    "ContenuPonctuel",
                    "ZoneSuperposee",
                    "ContenuLineaire",
                ]
                assert len(tab_list) == len(expected_tab_list)
                assert set(tab_list) == set(expected_tab_list)

            # check domain table and translated domains
            if layer.name == "rechtsstatus":
                count += 1
                assert layer.alias == "StatutJuridique"
                assert layer.layer.displayExpression() == "\n".join(
                    [
                        "CASE",
                        "WHEN iliCode = 'AenderungOhneVorwirkung' THEN 'ModificationSansEffetAnticipe'",
                        "WHEN iliCode = 'inKraft' THEN 'enVigueur'",
                        "WHEN iliCode = 'AenderungMitVorwirkung' THEN 'ModificationAvecEffetAnticipe'",
                        "END",
                    ]
                )

        # check if the layers have been considered
        assert count == 2
        assert fr_layer

        # Check translated relation
        rels = qgis_project.relationManager().referencedRelations(fr_layer)
        assert len(rels) == 1
        assert (
            rels[0].id()
            == "geometrie_dokument_geometrie_grundnutzung_zonenflaeche_grundnutzung_zonenflaeche_T_Id"
        )
        assert (
            rels[0].name()
            == "Geometrie_Document_(Geometrie)_AffectationPrimaire_SurfaceDeZones_(T_Id)"
        )

    def test_translated_db_objects_pg(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "PlansDAffectation_V1_2"
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
            preferred_language="fr",
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
        fr_layer = None
        for layer in available_layers:
            if layer.name == "grundnutzung_zonenflaeche":
                assert layer.alias == "AffectationPrimaire_SurfaceDeZones"
                fr_layer = layer.layer
                count += 1
                fields = fr_layer.fields()
                field_idx = fields.lookupField("publiziertab")
                assert field_idx != -1
                field = fields.field(field_idx)
                assert field.name() == "publiziertab"
                assert field.alias() == "publieDepuis"

                edit_form_config = fr_layer.editFormConfig()
                tabs = edit_form_config.tabs()
                tab_list = [tab.name() for tab in tabs]
                expected_tab_list = [
                    "General",
                    "Document",
                    "ContenuPonctuel",
                    "ZoneSuperposee",
                    "ContenuLineaire",
                ]
                assert len(tab_list) == len(expected_tab_list)
                assert set(tab_list) == set(expected_tab_list)

            # check domain table and translated domains
            if layer.name == "rechtsstatus":
                count += 1
                assert layer.alias == "StatutJuridique"
                assert layer.layer.displayExpression() == "\n".join(
                    [
                        "CASE",
                        "WHEN iliCode = 'AenderungOhneVorwirkung' THEN 'ModificationSansEffetAnticipe'",
                        "WHEN iliCode = 'AenderungMitVorwirkung' THEN 'ModificationAvecEffetAnticipe'",
                        "WHEN iliCode = 'inKraft' THEN 'enVigueur'",
                        "END",
                    ]
                )

        # check if the layers have been considered
        assert count == 2
        assert fr_layer

        # Check translated relation
        rels = qgis_project.relationManager().referencedRelations(fr_layer)
        assert len(rels) == 1
        assert rels[0].id() == "geometrie_dokument_geometr_grndntzng_znnflche_fkey"
        assert (
            rels[0].name()
            == "Geometrie_Document_(Geometrie)_AffectationPrimaire_SurfaceDeZones_(t_id)"
        )

    def test_translated_available_langs_gpkg(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "PlansDAffectation_V1_2"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_translated_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        db_connector = db_utils.get_db_connector(importer.configuration)

        # Translation handling is active
        assert db_connector.get_translation_handling()

        # Get the translated models
        assert {"PlansDAffectation_V1_2"} == set(db_connector.get_translation_models())

        # Get all languages
        assert {"en", "de", "fr"} == set(db_connector.get_available_languages())

        # ... without irrelevant models
        irrelevants = [
            "AdministrativeUnits_V1",
            "AdministrativeUnitsCH_V1",
            "Dictionaries_V1",
            "DictionariesCH_V1",
        ]
        assert {"de", "fr"} == set(db_connector.get_available_languages(irrelevants))

        # ... and the language of the translated model only
        assert {"fr"} == set(
            db_connector.get_available_languages([], ["PlansDAffectation_V1_2"])
        )

        # --- and nonsense use case for the validation, get only of an english model
        assert {"en"} == set(
            db_connector.get_available_languages([], ["AdministrativeUnits_V1"])
        )

        # ... as well as ignoring the translated models and alowing it again and the english one
        assert {"de", "en"} == set(
            db_connector.get_available_languages(["PlansDAffectation_V1_2"])
        )

    def test_translated_available_langs_pg(self):
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "PlansDAffectation_V1_2"
        importer.configuration.dbschema = "tid_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        db_connector = db_utils.get_db_connector(importer.configuration)

        # Translation handling is active
        assert db_connector.get_translation_handling()

        # Get the translated models
        assert {"PlansDAffectation_V1_2"} == set(db_connector.get_translation_models())

        # Get all languages
        assert {"en", "de", "fr"} == set(db_connector.get_available_languages())

        # ... without irrelevant models
        irrelevants = [
            "AdministrativeUnits_V1",
            "AdministrativeUnitsCH_V1",
            "Dictionaries_V1",
            "DictionariesCH_V1",
        ]
        assert {"de", "fr"} == set(db_connector.get_available_languages(irrelevants))

        # ... and the language of the translated model only
        assert {"fr"} == set(
            db_connector.get_available_languages([], ["PlansDAffectation_V1_2"])
        )

        # --- and nonsense use case for the validation, get only of an english model
        assert {"en"} == set(
            db_connector.get_available_languages([], ["AdministrativeUnits_V1"])
        )

        # ... as well as ignoring the translated models and alowing it again and the english one
        assert {"de", "en"} == set(
            db_connector.get_available_languages(["PlansDAffectation_V1_2"])
        )

    def test_translated_namelang_gpkg(self):
        # same as translated_db_objects but this time is the schema in French (namelang) and the preferred language German.
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "PlansDAffectation_V1_2"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath,
            "tmp_translated_{:%Y%m%d%H%M%S%f}.gpkg".format(datetime.datetime.now()),
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.configuration.name_lang = "fr"
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
            preferred_language="de",
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
            if layer.name == "affectationprimaire_surfacedezones":
                assert layer.alias == "Grundnutzung_Zonenflaeche"
                de_layer = layer.layer
                count += 1
                fields = de_layer.fields()
                field_idx = fields.lookupField("publiedepuis")
                assert field_idx != -1
                field = fields.field(field_idx)
                assert field.name() == "publiedepuis"
                assert field.alias() == "publiziertAb"

                edit_form_config = de_layer.editFormConfig()
                tabs = edit_form_config.tabs()
                tab_list = [tab.name() for tab in tabs]
                expected_tab_list = [
                    "General",
                    "Dokument",
                    "Objektbezogene_Festlegung",
                    "Ueberlagernde_Festlegung",
                    "Linienbezogene_Festlegung",
                ]
                assert len(tab_list) == len(expected_tab_list)
                assert set(tab_list) == set(expected_tab_list)

            # check domain table and translated domains
            if layer.name == "statutjuridique":
                count += 1
                assert layer.alias == "RechtsStatus"
                assert layer.layer.displayExpression() == "\n".join(
                    [
                        "CASE",
                        "WHEN iliCode = 'AenderungOhneVorwirkung' THEN 'AenderungOhneVorwirkung'",
                        "WHEN iliCode = 'inKraft' THEN 'inKraft'",
                        "WHEN iliCode = 'AenderungMitVorwirkung' THEN 'AenderungMitVorwirkung'",
                        "END",
                    ]
                )

        # check if the layers have been considered
        assert count == 2
        assert de_layer

        # Check translated relation
        rels = qgis_project.relationManager().referencedRelations(de_layer)
        assert len(rels) == 1
        assert (
            rels[0].id()
            == "geometrie_document_geometrie_affectationprimaire_surfacedezones_affectationprimaire_surfacedezones_T_Id"
        )
        assert (
            rels[0].name()
            == "Geometrie_Dokument_(Geometrie)_Grundnutzung_Zonenflaeche_(T_Id)"
        )

    def test_translated_namelang_pg(self):
        # same as translated_db_objects but this time is the schema in French (namelang) and the preferred language German.
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilimodels = "PlansDAffectation_V1_2"
        importer.configuration.dbschema = "tid_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.configuration.name_lang = "fr"
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        generator = Generator(
            DbIliMode.ili2pg,
            get_pg_connection_string(),
            importer.configuration.inheritance,
            importer.configuration.dbschema,
            consider_basket_handling=True,
            preferred_language="de",
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
            if layer.name == "affectationprimaire_surfacedezones":
                assert layer.alias == "Grundnutzung_Zonenflaeche"
                de_layer = layer.layer
                count += 1
                fields = de_layer.fields()
                field_idx = fields.lookupField("publiedepuis")
                assert field_idx != -1
                field = fields.field(field_idx)
                assert field.name() == "publiedepuis"
                assert field.alias() == "publiziertAb"

                edit_form_config = de_layer.editFormConfig()
                tabs = edit_form_config.tabs()
                tab_list = [tab.name() for tab in tabs]
                expected_tab_list = [
                    "General",
                    "Dokument",
                    "Objektbezogene_Festlegung",
                    "Ueberlagernde_Festlegung",
                    "Linienbezogene_Festlegung",
                ]
                assert len(tab_list) == len(expected_tab_list)
                assert set(tab_list) == set(expected_tab_list)

            # check domain table and translated domains
            if layer.name == "statutjuridique":
                count += 1
                assert layer.alias == "RechtsStatus"
                assert layer.layer.displayExpression() == "\n".join(
                    [
                        "CASE",
                        "WHEN iliCode = 'AenderungMitVorwirkung' THEN 'AenderungMitVorwirkung'",
                        "WHEN iliCode = 'AenderungOhneVorwirkung' THEN 'AenderungOhneVorwirkung'",
                        "WHEN iliCode = 'inKraft' THEN 'inKraft'",
                        "END",
                    ]
                )

        # check if the layers have been considered
        assert count == 2
        assert de_layer

        # Check translated relation
        rels = qgis_project.relationManager().referencedRelations(de_layer)
        assert len(rels) == 1
        assert rels[0].id() == "geometrie_document_geomtr_ffcttnrmr_srfcdznes_fkey"
        assert (
            rels[0].name()
            == "Geometrie_Dokument_(Geometrie)_Grundnutzung_Zonenflaeche_(t_id)"
        )

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
