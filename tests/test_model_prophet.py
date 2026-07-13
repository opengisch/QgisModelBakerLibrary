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
from modelbaker.ili2pytools.prophets import SettingsProphet
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
        settings_prophet = SettingsProphet(index, model_name, MODELS_BLACKLIST)

        assert settings_prophet.has_basket_oids() is True
        assert settings_prophet.has_extended_topics() is False
        assert settings_prophet.needs_basket_column() is True
        assert settings_prophet.has_arcs() is True
        assert settings_prophet.has_multiple_geometry_columns() is False
        assert settings_prophet.has_enumerations() is True
        assert settings_prophet.has_extended_enumerations() is False

        is_translation, languages, _ = settings_prophet.language_infos()
        assert is_translation is False
        assert set(languages) == {"de"}

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

        settings_prophet = SettingsProphet(index, model_name, MODELS_BLACKLIST)

        assert settings_prophet.has_basket_oids() is False
        assert settings_prophet.has_extended_topics() is True
        assert settings_prophet.needs_basket_column() is True
        assert settings_prophet.has_arcs() is True
        assert settings_prophet.has_multiple_geometry_columns() is True
        assert settings_prophet.has_enumerations() is False
        assert settings_prophet.has_extended_enumerations() is False

        is_translation, languages, _ = settings_prophet.language_infos()
        assert is_translation is False
        assert set(languages) == {"de", "eo"}

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

        settings_prophet = SettingsProphet(index, model_name, MODELS_BLACKLIST)

        assert settings_prophet.has_basket_oids() is False
        assert settings_prophet.has_extended_topics() is False
        assert settings_prophet.needs_basket_column() is False
        assert settings_prophet.has_arcs() is False
        assert settings_prophet.has_multiple_geometry_columns() is True
        assert settings_prophet.has_enumerations() is True
        assert settings_prophet.has_extended_enumerations() is False

        is_translation, languages, _ = settings_prophet.language_infos()
        assert is_translation is False
        assert set(languages) == {"de"}

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

        settings_prophet = SettingsProphet(index, model_name, MODELS_BLACKLIST)

        assert settings_prophet.has_basket_oids() is False
        assert settings_prophet.has_extended_topics() is False
        assert settings_prophet.needs_basket_column() is False

        assert settings_prophet.has_arcs() is False
        assert settings_prophet.has_multiple_geometry_columns() is False
        assert settings_prophet.has_enumerations() is True
        assert settings_prophet.has_extended_enumerations() is True

        is_translation, languages, _ = settings_prophet.language_infos()
        assert is_translation is False
        assert set(languages) == {"es"}

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
        settings_prophet = SettingsProphet(index, model_name, MODELS_BLACKLIST)

        assert settings_prophet.has_basket_oids() is True
        assert settings_prophet.has_extended_topics() is False
        assert settings_prophet.needs_basket_column() is True
        assert settings_prophet.has_arcs() is True
        assert settings_prophet.has_multiple_geometry_columns() is False
        assert settings_prophet.has_enumerations() is True
        assert settings_prophet.has_extended_enumerations() is False

        (
            is_translation,
            languages,
            preferred_language,
        ) = settings_prophet.language_infos()
        assert is_translation is True
        assert set(languages) == {"de", "fr"}
        assert preferred_language == "de"  # original language

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
        settings_prophet = SettingsProphet(index, model_name, MODELS_BLACKLIST)

        assert settings_prophet.has_basket_oids() is True
        assert settings_prophet.has_extended_topics() is False
        assert settings_prophet.needs_basket_column() is True
        assert settings_prophet.has_arcs() is True
        assert settings_prophet.has_multiple_geometry_columns() is False
        assert settings_prophet.has_enumerations() is True
        assert settings_prophet.has_extended_enumerations() is False

        (
            is_translation,
            languages,
            preferred_language,
        ) = settings_prophet.language_infos()
        assert is_translation is True
        assert set(languages) == {"de", "it"}
        assert preferred_language == "de"  # original language
