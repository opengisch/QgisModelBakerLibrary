"""
/***************************************************************************
    begin                :    08.12.2025
        git sha              : :%H$
        copyright            : (C) 2025 by Dave Signer
        email                : david at opengis ch
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

import tempfile

from qgis.testing import start_app, unittest

from modelbaker.iliwrapper.ili2dbconfig import BaseConfiguration
from modelbaker.pythonizer.pythonizer import Pythonizer
from modelbaker.pythonizer.settings_prophet import ProphetTools, SettingsProphet
from tests.utils import testdata_path

start_app()


class TestPythonizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.base_config = BaseConfiguration()

    def test_settings_prophet_nupla(self):
        pythonizer = Pythonizer()
        base_configuration = BaseConfiguration()
        ili_file = testdata_path("ilimodels/Nutzungsplanung_V1_2.ili")
        john_wayne, imd_file = pythonizer.compile(base_configuration, ili_file)
        index, lib = pythonizer.pythonize(imd_file)
        prophet = SettingsProphet(index)

        assert prophet.has_basket_oids()
        assert prophet.has_arcs()
        assert not prophet.has_multiple_geometrie_columms()

        expected_multigeometries = {}
        assert prophet.multi_geometry_structures_on_23() == expected_multigeometries

    def test_settings_prophet_arcmodel(self):
        pythonizer = Pythonizer()
        base_configuration = BaseConfiguration()
        ili_file = testdata_path("ilimodels/KT_ArcInfrastruktur.ili")
        john_wayne, imd_file = pythonizer.compile(base_configuration, ili_file)
        index, lib = pythonizer.pythonize(imd_file)
        prophet = SettingsProphet(index)

        assert not prophet.has_basket_oids()
        assert prophet.has_arcs()
        assert prophet.has_multiple_geometrie_columms()

        expected_multigeometries = {}
        assert prophet.multi_geometry_structures_on_23() == expected_multigeometries

    def test_settings_prophet_arcs(self):
        pythonizer = Pythonizer()
        base_configuration = BaseConfiguration()
        ili_file = testdata_path("ilimodels/KbS_V1_5.ili")
        john_wayne, imd_file = pythonizer.compile(base_configuration, ili_file)
        index, lib = pythonizer.pythonize(imd_file)
        prophet = SettingsProphet(index)

        assert not prophet.has_basket_oids()
        assert not prophet.has_arcs()
        assert prophet.has_multiple_geometrie_columms()

        expected_multigeometries = {}
        assert prophet.multi_geometry_structures_on_23() == expected_multigeometries

        prophet_tools = ProphetTools()
        prophet_tools.temp_meta_attr_file(expected_multigeometries)
