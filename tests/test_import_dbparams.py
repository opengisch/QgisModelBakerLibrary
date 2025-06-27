"""
/***************************************************************************
                              -------------------
        begin                : 06/27/2025
        git sha              : :%H$
        copyright            : (C) 2025 by Dave Signer @ OPENGIS.ch
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
import pathlib
import tempfile

from qgis.testing import start_app, unittest

from modelbaker.iliwrapper import iliimporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import iliimporter_config

CATALOGUE_DATASETNAME = "Catset"

start_app()

test_path = pathlib.Path(__file__).parent.absolute()


class TestDbParams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_postgis_withandwithout_params(self):
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

        # now we remove the password - it should fail now
        importer.configuration.dbpwd = None
        assert importer.run() == iliimporter.Importer.ERROR

        # now we add the password by dbparams and it should succeed again
        importer.configuration.dbparam_map = {"password": "docker"}
        assert importer.run() == iliimporter.Importer.SUCCESS

        # now we add a wrong password by dbparams and it should fail again
        importer.configuration.dbparam_map = {"password": "ducker"}
        assert importer.run() == iliimporter.Importer.SUCCESS
