"""
/***************************************************************************
        begin                : 2026-07-03
        git sha              : :%H$
        copyright            : (C) 2026 by Dave Signer
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

import datetime
import logging
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET

from qgis.testing import start_app, unittest

from modelbaker.iliwrapper import ilicompiler
from tests.utils import ilicompiler_config, testdata_path

start_app()


class TestCompile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_compile_simplemodel_1(self):
        # Schema Import
        compiler = ilicompiler.IliCompiler()
        compiler.configuration = ilicompiler_config()
        compiler.configuration.ilifile = testdata_path("ilimodels/RoadsSimple.ili")
        compiler.configuration.imdfile = os.path.join(
            self.basetestpath,
            "metamodel_{:%Y%m%d%H%M%S%f}.imd".format(datetime.datetime.now()),
        )
        compiler.stdout.connect(self.print_info)
        compiler.stderr.connect(self.print_error)
        assert compiler.run() == ilicompiler.IliCompiler.SUCCESS

        assert os.path.exists(compiler.configuration.imdfile)

        namespaces = {
            "ili": "http://www.interlis.ch/xtf/2.4/INTERLIS",
            "IlisMeta16": "http://www.interlis.ch/xtf/2.4/IlisMeta16",
        }

        tree = ET.parse(compiler.configuration.imdfile)
        root = tree.getroot()

        # Check some random items

        # Class Street
        street_class = root.find(
            ".//IlisMeta16:Class[@ili:tid='RoadsSimple.Roads.Street']", namespaces
        )
        assert street_class is not None
        assert street_class.find("IlisMeta16:Name", namespaces).text == "Street"
        assert street_class.find("IlisMeta16:Kind", namespaces).text == "Class"

        # Association StreetAxisAssoc
        assoc_class = root.find(
            ".//IlisMeta16:Class[@ili:tid='RoadsSimple.Roads.StreetAxisAssoc']",
            namespaces,
        )
        assert assoc_class is not None
        assert assoc_class.find("IlisMeta16:Name", namespaces).text == "StreetAxisAssoc"
        assert assoc_class.find("IlisMeta16:Kind", namespaces).text == "Association"

        # Enum Water
        water_enum = root.find(
            ".//IlisMeta16:EnumNode[@ili:tid='RoadsSimple.Roads.LandCover.Type.TYPE.TOP.water']",
            namespaces,
        )
        assert water_enum is not None
        assert water_enum.find("IlisMeta16:Name", namespaces).text == "water"

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
