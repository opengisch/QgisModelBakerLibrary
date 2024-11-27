"""
/***************************************************************************
                              -------------------
        begin                : 20.11.2024
        git sha              : :%H$
        copyright            : (C) 2024 by Germán Carrillo
        email                : german at opengis ch
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
import shutil
import tempfile

from qgis.testing import start_app, unittest

from modelbaker.iliwrapper import iliimporter, ilimetaconfigexporter
from modelbaker.iliwrapper.globals import DbIliMode
from tests.utils import iliimporter_config, ilimetaconfigexporter_config, testdata_path

start_app()


class TestExportMetaConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()

    def test_exportmetaconfig_postgis(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2pg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbschema = "any_{:%Y%m%d%H%M%S%f}".format(
            datetime.datetime.now()
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # ExportMetaConfig
        exportMetaConfig = ilimetaconfigexporter.MetaConfigExporter()
        exportMetaConfig.tool = DbIliMode.ili2pg
        exportMetaConfig.configuration = ilimetaconfigexporter_config(importer.tool)
        metaconfig_file = os.path.join(
            self.basetestpath, "tmp_exported_metaconfig_pg.ini"
        )
        exportMetaConfig.configuration.metaconfigoutputfile = metaconfig_file
        exportMetaConfig.stdout.connect(self.print_info)
        exportMetaConfig.stderr.connect(self.print_error)
        assert (
            exportMetaConfig.run() == ilimetaconfigexporter.MetaConfigExporter.SUCCESS
        )

        # Check output metaConfig file
        assert os.path.isfile(metaconfig_file)

        config = configparser.ConfigParser()
        config.read(metaconfig_file)
        assert "CONFIGURATION" in config
        assert "ch.ehi.ili2db" in config
        params = dict(config["ch.ehi.ili2db"])

        expected_key_values = {
            "iligml20": "false",
            "beautifyenumdispname": "false",
            "createbasketcol": "false",
            "createdatasetcol": "false",
            "createdatetimechecks": "false",
            "createenumcolasitfcode": "false",
            "createenumtxtcol": "false",
            "createfk": "false",
            "createfkidx": "false",
            "creategeomidx": "false",
            "createimporttabs": "false",
            "createmandatorychecks": "false",
            "createmetainfo": "false",
            "createnlstab": "false",
            "createnumchecks": "false",
            "createstdcols": "false",
            "createtextchecks": "false",
            "createtidcol": "false",
            "createtypeconstraint": "false",
            "createtypediscriminator": "false",
            "createunique": "false",
            "disableareavalidation": "false",
            "disableboundaryrecoding": "true",
            "disablenameoptimization": "false",
            "disablerounding": "false",
            "disablevalidation": "true",
            "exporttid": "false",
            "forcetypevalidation": "false",
            "importbid": "false",
            "importtid": "false",
            "keeparearef": "false",
            "multisrs": "false",
            "namebytopic": "false",
            "nosmartmapping": "true",
            "skipgeometryerrors": "false",
            "skipreferenceerrors": "false",
            "sqlcolsastext": "false",
            "sqlenablenull": "false",
            "sqlextrefcols": "false",
            "strokearcs": "false",
            "ver3-translation": "false",
        }

        for k, v in expected_key_values.items():
            assert k in params and params[k] == v

    def test_exportmetaconfig_geopackage(self):
        # Schema Import
        importer = iliimporter.Importer()
        importer.tool = DbIliMode.ili2gpkg
        importer.configuration = iliimporter_config(importer.tool)
        importer.configuration.ilifile = testdata_path(
            "ilimodels/PipeBasketTest_V1.ili"
        )
        importer.configuration.ilimodels = "PipeBasketTest"
        importer.configuration.dbfile = os.path.join(
            self.basetestpath, "tmp_delete_dataset_gpkg.gpkg"
        )
        importer.configuration.inheritance = "smart2"
        importer.configuration.create_basket_col = True
        importer.stdout.connect(self.print_info)
        importer.stderr.connect(self.print_error)
        assert importer.run() == iliimporter.Importer.SUCCESS

        # ExportMetaConfig
        exportMetaConfig = ilimetaconfigexporter.MetaConfigExporter()
        exportMetaConfig.tool = DbIliMode.ili2gpkg
        exportMetaConfig.configuration = ilimetaconfigexporter_config(importer.tool)
        exportMetaConfig.configuration.dbfile = importer.configuration.dbfile
        metaconfig_file = os.path.join(
            self.basetestpath, "tmp_exported_metaconfig_gpkg.ini"
        )
        exportMetaConfig.configuration.metaconfigoutputfile = metaconfig_file
        exportMetaConfig.stdout.connect(self.print_info)
        exportMetaConfig.stderr.connect(self.print_error)
        assert (
            exportMetaConfig.run() == ilimetaconfigexporter.MetaConfigExporter.SUCCESS
        )

        # Check output metaConfig file
        assert os.path.isfile(metaconfig_file)

        config = configparser.ConfigParser()
        config.read(metaconfig_file)
        assert "CONFIGURATION" in config
        assert "ch.ehi.ili2db" in config
        params = dict(config["ch.ehi.ili2db"])

        expected_key_values = {
            "iligml20": "false",
            "beautifyenumdispname": "true",
            "coalescearray": "true",
            "coalescecatalogueref": "true",
            "coalescejson": "true",
            "coalescemultiline": "true",
            "coalescemultipoint": "true",
            "coalescemultisurface": "true",
            "createbasketcol": "true",
            "createdatasetcol": "false",
            "createdatetimechecks": "false",
            "createenumcolasitfcode": "false",
            "createenumtabswithid": "true",
            "createenumtxtcol": "false",
            "createfk": "true",
            "createfkidx": "true",
            "creategeomidx": "true",
            "createimporttabs": "false",
            "createmandatorychecks": "false",
            "createmetainfo": "true",
            "createnlstab": "true",
            "createnumchecks": "true",
            "createstdcols": "false",
            "createtextchecks": "false",
            "createtidcol": "true",
            "createtypeconstraint": "true",
            "createtypediscriminator": "false",
            "createunique": "true",
            "defaultsrsauth": "EPSG",
            "defaultsrscode": "2056",
            "disableareavalidation": "false",
            "disableboundaryrecoding": "true",
            "disablenameoptimization": "false",
            "disablerounding": "false",
            "disablevalidation": "true",
            "expandlocalised": "true",
            "expandmultilingual": "true",
            "exporttid": "false",
            "forcetypevalidation": "false",
            "importbid": "false",
            "importtid": "false",
            "keeparearef": "false",
            "maxnamelength": "60",
            "multisrs": "false",
            "namebytopic": "false",
            "skipgeometryerrors": "false",
            "skipreferenceerrors": "false",
            "smart2inheritance": "true",
            "sqlcolsastext": "false",
            "sqlenablenull": "false",
            "sqlextrefcols": "false",
            "strokearcs": "true",
            "ver3-translation": "false",
        }

        for k, v in expected_key_values.items():
            assert k in params and params[k] == v

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)

    @classmethod
    def tearDownClass(cls):
        """Run after all tests."""
        shutil.rmtree(cls.basetestpath, True)
