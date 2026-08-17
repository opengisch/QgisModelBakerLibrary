"""
Metadata:
    Creation Date: 2026-07-07
    Copyright: (C) 2026 by Dave Signer
    Contact: david@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""

import os
import sys
import tempfile

from qgis.testing import start_app, unittest

from modelbaker.utils.globals import MODELS_BLACKLIST

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "modelbaker", "libs")
)
from modelbaker.ili2pytools.prophets import ModelProphet, SettingsProphet
from modelbaker.ili2pytools.pythonizer import BakerPyIndex
from modelbaker.iliwrapper.ili2dbconfig import BaseConfiguration
from modelbaker.utils.ili2db_utils import Ili2DbUtils
from tests.utils import testdata_path

start_app()


class TestSettingsProphet(unittest.TestCase):
    """Tests the SettingsProphet convenience functions.

    Also covers its base class ModelProphet and the BakerPyIndex.
    """

    @classmethod
    def setUpClass(cls):
        """Runs before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.base_config = BaseConfiguration()

    def test_settings_prophet_nupla(self):
        """
        Test the SettingsProphet / ModelProphet with a model having:
        - BASKET OIDs and no extended topics -> needs basket column
        - ARCS
        - No multiple geometry columns
        - Enumerations
        - No extended enumerations
        - It's not translation and language is DE
        """

        ili_file = testdata_path("ilimodels/Nutzungsplanung_V1_2.ili")

        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)
        model_name = "Nutzungsplanung_V1_2"

        model_prophet = ModelProphet(index, model_name, MODELS_BLACKLIST)
        settings_prophet = SettingsProphet({model_name: index}, MODELS_BLACKLIST)

        self.assertTrue(model_prophet.has_basket_oids())
        self.assertFalse(model_prophet.has_extended_topics())
        self.assertTrue(settings_prophet.needs_basket_column())
        self.assertTrue(settings_prophet.contains_arcs())
        self.assertFalse(settings_prophet.contains_multiple_geometry_columns())
        self.assertFalse(settings_prophet.contains_extended_enumerations())

        is_translation, languages, _ = settings_prophet.language_infos()
        self.assertFalse(is_translation)
        self.assertEqual(set(languages), {"de"})

    def test_settings_prophet_arcs(self):
        """
        Test the SettingsProphet / ModelProphet with a model having:
        - No BASKET OIDs but extended topics -> needs basket column
        - ARCS
        - Multiple geometry columns
        - No Enumerations
        - No extended enumerations
        - It's not translation and language is EO (and the parent (not original) is DE)
        """

        ili_file = testdata_path("ilimodels/KT_ArcInfrastruktur_V1.ili")
        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)
        model_name = "KT_ArcInfrastruktur_V1"

        model_prophet = ModelProphet(index, model_name, MODELS_BLACKLIST)
        settings_prophet = SettingsProphet({model_name: index}, MODELS_BLACKLIST)

        self.assertFalse(model_prophet.has_basket_oids())
        self.assertTrue(model_prophet.has_extended_topics())
        self.assertTrue(settings_prophet.needs_basket_column())
        self.assertTrue(settings_prophet.contains_arcs())
        self.assertTrue(settings_prophet.contains_multiple_geometry_columns())
        self.assertFalse(settings_prophet.contains_enumerations())
        self.assertFalse(settings_prophet.contains_extended_enumerations())

        is_translation, languages, _ = settings_prophet.language_infos()
        self.assertFalse(is_translation)
        self.assertEqual(set(languages), {"de", "eo"})

    def test_settings_prophet_kbs(self):
        """
        Test the SettingsProphet / ModelProphet with a model having:
        - No BASKET OIDs and no extended topics -> needs no basket column
        - No ARCS
        - Multiple geometry columns
        - Enumerations
        - No extended enumerations
        - It's not translation and language is DE
        """

        ili_file = testdata_path("ilimodels/KbS_V1_5.ili")
        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)
        model_name = "KbS_V1_5"

        model_prophet = ModelProphet(index, model_name, MODELS_BLACKLIST)
        settings_prophet = SettingsProphet({model_name: index}, MODELS_BLACKLIST)

        self.assertFalse(model_prophet.has_basket_oids())
        self.assertFalse(model_prophet.has_extended_topics())
        self.assertFalse(settings_prophet.needs_basket_column())
        self.assertFalse(settings_prophet.contains_arcs())
        self.assertTrue(settings_prophet.contains_multiple_geometry_columns())
        self.assertTrue(settings_prophet.contains_enumerations())
        self.assertFalse(settings_prophet.contains_extended_enumerations())

        is_translation, languages, _ = settings_prophet.language_infos()
        self.assertFalse(is_translation)
        self.assertEqual(set(languages), {"de"})

    def test_settings_prophet_color_enums(self):
        """
        Test the SettingsProphet / ModelProphet with a model having:
        - No BASKET OIDs and no extended topics -> needs no basket column
        - No ARCS
        - No Multiple geometry columns
        - Enumerations
        - Extended enumerations
        - It's not translation and language is ES
        """
        ili_file = testdata_path("ilimodels/ColorsParentChildDomain_V2.ili")
        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)
        model_name = "Colors_V2"

        model_prophet = ModelProphet(index, model_name, MODELS_BLACKLIST)
        settings_prophet = SettingsProphet({model_name: index}, MODELS_BLACKLIST)

        self.assertFalse(model_prophet.has_basket_oids())
        self.assertFalse(model_prophet.has_extended_topics())
        self.assertFalse(settings_prophet.needs_basket_column())

        self.assertFalse(settings_prophet.contains_arcs())
        self.assertFalse(settings_prophet.contains_multiple_geometry_columns())
        self.assertTrue(settings_prophet.contains_enumerations())
        self.assertTrue(settings_prophet.contains_extended_enumerations())

        is_translation, languages, _ = settings_prophet.language_infos()
        self.assertFalse(is_translation)
        self.assertEqual(set(languages), {"es"})

    def test_settings_prophet_nupla_fr(self):
        """
        Test the SettingsProphet / ModelProphet with a model having:
        - BASKET OIDs and no extended topics -> needs basket column
        - ARCS
        - No multiple geometry columns
        - Enumerations
        - No extended enumerations
        - It's a translation and language is FR
        """

        ili_file = testdata_path("ilimodels/PlansDAffectation_V1_2.ili")

        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)
        model_name = "PlansDAffectation_V1_2"

        model_prophet = ModelProphet(index, model_name, MODELS_BLACKLIST)
        settings_prophet = SettingsProphet({model_name: index}, MODELS_BLACKLIST)

        self.assertTrue(model_prophet.has_basket_oids())
        self.assertFalse(model_prophet.has_extended_topics())
        self.assertTrue(settings_prophet.needs_basket_column())
        self.assertTrue(settings_prophet.contains_arcs())
        self.assertFalse(settings_prophet.contains_multiple_geometry_columns())
        self.assertTrue(settings_prophet.contains_enumerations())
        self.assertFalse(settings_prophet.contains_extended_enumerations())

        (
            is_translation,
            languages,
            preferred_language,
        ) = settings_prophet.language_infos()
        self.assertTrue(is_translation)
        self.assertEqual(set(languages), {"de", "fr"})
        self.assertEqual(preferred_language, "de")  # original language

    def test_settings_prophet_nupla_it(self):
        """
        Test the SettingsProphet / ModelProphet with a model having:
        - BASKET OIDs and no extended topics -> needs basket column
        - ARCS
        - No multiple geometry columns
        - Enumerations
        - No extended enumerations
        - It's a translation and language is IT
        """

        ili_file = testdata_path("ilimodels/PianiDiUtilizzazione_V1_2.ili")

        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)
        model_name = "PianiDiUtilizzazione_V1_2"
        model_prophet = ModelProphet(index, model_name, MODELS_BLACKLIST)
        settings_prophet = SettingsProphet({model_name: index}, MODELS_BLACKLIST)

        self.assertTrue(model_prophet.has_basket_oids())
        self.assertFalse(model_prophet.has_extended_topics())
        self.assertTrue(settings_prophet.needs_basket_column())
        self.assertTrue(settings_prophet.contains_arcs())
        self.assertFalse(settings_prophet.contains_multiple_geometry_columns())
        self.assertTrue(settings_prophet.contains_enumerations())
        self.assertFalse(settings_prophet.contains_extended_enumerations())

        (
            is_translation,
            languages,
            preferred_language,
        ) = settings_prophet.language_infos()
        self.assertTrue(is_translation)
        self.assertEqual(set(languages), {"de", "it"})
        self.assertEqual(preferred_language, "de")  # original language
