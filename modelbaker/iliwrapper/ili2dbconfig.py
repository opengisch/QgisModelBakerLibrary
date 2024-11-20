"""
/***************************************************************************
                              -------------------
        begin                : 23/03/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF-Swissphoto)
        email                : gcarrillo@linuxmail.org
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

from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkProxy

from .globals import DbIliMode
from .ili2dbutils import get_all_modeldir_in_path


class BaseConfiguration:
    def __init__(self):
        self.super_pg_user = "postgres"
        self.super_pg_password = "postgres"

        self.custom_model_directories_enabled = False
        self.custom_model_directories = ""
        self.java_path = ""
        self.logfile_path = ""

        self.debugging_enabled = False

    def save(self, settings):
        settings.setValue("SuperUser", self.super_pg_user)
        settings.setValue("SuperPassword", self.super_pg_password)
        settings.setValue(
            "CustomModelDirectoriesEnabled", self.custom_model_directories_enabled
        )
        settings.setValue("CustomModelDirectories", self.custom_model_directories)
        settings.setValue("JavaPath", self.java_path)
        settings.setValue("LogfilePath", self.logfile_path)
        settings.setValue("DebuggingEnabled", self.debugging_enabled)

    def restore(self, settings):
        self.super_pg_user = settings.value("SuperUser", "postgres", str)
        self.super_pg_password = settings.value("SuperPassword", "postgres", str)
        self.custom_model_directories_enabled = settings.value(
            "CustomModelDirectoriesEnabled", False, bool
        )
        self.custom_model_directories = settings.value(
            "CustomModelDirectories", "", str
        )
        self.java_path = settings.value("JavaPath", "", str)
        self.debugging_enabled = settings.value("DebuggingEnabled", False, bool)
        self.logfile_path = settings.value("LogfilePath", "", str)

    def to_ili2db_args(self, with_modeldir=True, with_usabilityhub_repo=False):
        """
        Create an ili2db command line argument string from this configuration
        """
        args = list()

        if with_modeldir:
            if self.custom_model_directories_enabled and self.custom_model_directories:
                str_model_directories = [
                    get_all_modeldir_in_path(path)
                    for path in self.custom_model_directories.split(";")
                ]
                str_model_directories = ";".join(str_model_directories)
                args += ["--modeldir", str_model_directories]
        if with_usabilityhub_repo:
            if not self.custom_model_directories_enabled:
                # Workaround for https://github.com/opengisch/QgisModelBaker/issues/784.
                # Can be removed when ili2db has access to the UsabILIty Hub repository.
                args += [
                    "--modeldir",
                    "%ILI_FROM_DB;%XTF_DIR;http://models.interlis.ch/;%JAR_DIR;https://models.opengis.ch/",
                ]
        if self.debugging_enabled and self.logfile_path:
            args += ["--trace"]
            args += ["--log", self.logfile_path]
        return args

    @property
    def model_directories(self):
        dirs = list()
        if self.custom_model_directories_enabled and self.custom_model_directories:
            dirs = self.custom_model_directories.split(";")
        else:
            dirs = [
                "%ILI_FROM_DB",
                "%XTF_DIR",
                "http://models.interlis.ch/",
                "%JAR_DIR",
            ]
        return dirs

    @property
    def ilidata_directories(self):
        dirs = list()
        if self.custom_model_directories_enabled and self.custom_model_directories:
            dirs = self.custom_model_directories.split(";")
        else:
            dirs = ["https://models.opengis.ch/"]
        return dirs


class Ili2DbCommandConfiguration:
    def __init__(self, other=None):
        if not isinstance(other, Ili2DbCommandConfiguration):
            self.base_configuration = BaseConfiguration()

            self.dbport = ""
            self.dbhost = ""
            self.dbpwd = ""
            self.dbusr = ""
            self.dbauthid = ""
            self.db_use_super_login = False
            self.database = ""
            self.dbschema = ""
            self.dbfile = ""
            self.dbservice = None
            self.sslmode = None
            self.tool = None
            self.ilifile = ""
            self.ilimodels = ""
            self.tomlfile = ""
            self.dbinstance = ""
            self.db_odbc_driver = ""
            self.disable_validation = False
            self.metaconfig = None
            self.metaconfig_id = None
            self.metaconfig_params_only = False
            self.db_ili_version = None
        else:
            # We got an 'other' object from which we'll get parameters
            self.__dict__ = other.__dict__.copy()

    def append_args(self, args, values, consider_metaconfig=False, force_append=False):

        if not force_append and self.metaconfig and self.metaconfig_id and values:
            if self.metaconfig_params_only:
                return
            if consider_metaconfig and "ch.ehi.ili2db" in self.metaconfig.sections():
                metaconfig_ili2db_params = self.metaconfig["ch.ehi.ili2db"]
                if values[0][2:] in metaconfig_ili2db_params.keys():
                    # if the value is set in the metaconfig, then we do consider it instead
                    return
        args += values

    def to_ili2db_args(self):

        # Valid ili file, don't pass --modeldir (it can cause ili2db errors)
        with_modeldir = not self.ilifile

        args = self.base_configuration.to_ili2db_args(
            with_modeldir=with_modeldir, with_usabilityhub_repo=bool(self.metaconfig_id)
        )

        proxy = QgsNetworkAccessManager.instance().fallbackProxy()
        if proxy.type() == QNetworkProxy.HttpProxy:
            self.append_args(args, ["--proxy", proxy.hostName()], force_append=True)
            self.append_args(
                args, ["--proxyPort", str(proxy.port())], force_append=True
            )

        if self.ilimodels:
            self.append_args(args, ["--models", self.ilimodels])

        if self.tomlfile:
            self.append_args(args, ["--iliMetaAttrs", self.tomlfile])

        elif self.db_ili_version is None or self.db_ili_version > 3:
            self.append_args(args, ["--iliMetaAttrs", "NULL"])

        # needs to start with "ilidata:" or should be a local file path
        if self.metaconfig_id:
            self.append_args(
                args,
                ["--metaConfig", self.metaconfig_id],
                force_append=True,
            )

        return args


class ExportConfiguration(Ili2DbCommandConfiguration):
    def __init__(self, other: Ili2DbCommandConfiguration = None):
        super().__init__(other)
        self.xtffile = ""
        self.with_exporttid = False
        self.iliexportmodels = ""
        self.dataset = ""
        self.baskets = list()

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        self.append_args(args, extra_args)

        if with_action:
            self.append_args(args, ["--export"])

        if self.disable_validation:
            self.append_args(args, ["--disableValidation"])

        if self.with_exporttid:
            self.append_args(args, ["--exportTid"])

        if self.iliexportmodels:
            self.append_args(args, ["--exportModels", self.iliexportmodels])

        if self.db_ili_version == 3:
            self.append_args(args, ["--export3"])

        if self.dataset:
            self.append_args(args, ["--dataset", self.dataset])

        if self.baskets:
            self.append_args(args, ["--baskets", ";".join(self.baskets)])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        self.append_args(args, [self.xtffile])

        return args


class SchemaImportConfiguration(Ili2DbCommandConfiguration):
    def __init__(self, other: Ili2DbCommandConfiguration = None):
        super().__init__(other)
        self.inheritance = "smart1"
        self.create_basket_col = False
        self.create_import_tid = True
        self.srs_auth = "EPSG"  # Default SRS auth in ili2db
        self.srs_code = 2056  # Default SRS code in ili2db
        self.create_gpkg_multigeom = False
        self.stroke_arcs = True
        self.pre_script = ""
        self.post_script = ""

    def to_ili2db_args(self, extra_args=[], with_action=True):
        """
        Create an ili2db argument array, with the password masked with ****** and optionally with the ``action``
        argument (--schemaimport) removed
        """
        args = list()

        if with_action:
            self.append_args(args, ["--schemaimport"], force_append=True)

        self.append_args(args, extra_args, force_append=True)

        self.append_args(args, ["--coalesceCatalogueRef"], True)

        if self.disable_validation:
            self.append_args(args, ["--sqlEnableNull"], force_append=True)
            self.append_args(args, ["--sqlColsAsText"], force_append=True)
        else:
            self.append_args(args, ["--createNumChecks"], True)
            self.append_args(args, ["--createUnique"], True)
            self.append_args(args, ["--createFk"], True)

        self.append_args(args, ["--createFkIdx"], True)
        self.append_args(args, ["--coalesceMultiSurface"], True)
        self.append_args(args, ["--coalesceMultiLine"], True)
        self.append_args(args, ["--coalesceMultiPoint"], True)
        self.append_args(args, ["--coalesceArray"], True)
        self.append_args(args, ["--beautifyEnumDispName"], True)
        self.append_args(args, ["--createGeomIdx"], True)
        self.append_args(args, ["--createMetaInfo"], True)
        self.append_args(args, ["--expandMultilingual"], True)

        if self.db_ili_version is None or self.db_ili_version > 3:
            self.append_args(args, ["--createTypeConstraint"], True)
            self.append_args(args, ["--createEnumTabsWithId"], True)
            self.append_args(args, ["--createTidCol"], True)
        else:
            # version 3 backwards compatibility (not needed in newer versions)
            self.append_args(args, ["--createEnumTabs"], True)
            if self.create_import_tid:
                self.append_args(args, ["--importTid"])

        if self.inheritance == "smart1":
            self.append_args(args, ["--smart1Inheritance"])
        elif self.inheritance == "smart2":
            self.append_args(args, ["--smart2Inheritance"])
        else:
            self.append_args(args, ["--noSmartMapping"])

        if self.stroke_arcs:
            self.append_args(args, ["--strokeArcs"])
        elif self.db_ili_version is None or self.db_ili_version > 3:
            self.append_args(args, ["--strokeArcs=False"])

        if self.tool and (self.tool & DbIliMode.gpkg):
            if self.create_gpkg_multigeom:
                self.append_args(args, ["--gpkgMultiGeomPerTable"], True)
            elif self.db_ili_version is None or self.db_ili_version > 3:
                self.append_args(args, ["--gpkgMultiGeomPerTable=False"])

        if self.create_basket_col:
            self.append_args(args, ["--createBasketCol"])
        elif self.db_ili_version is None or self.db_ili_version > 3:
            self.append_args(args, ["--createBasketCol=False"])

        self.append_args(args, ["--defaultSrsAuth", self.srs_auth])

        self.append_args(args, ["--defaultSrsCode", "{}".format(self.srs_code)])

        if self.pre_script:
            self.append_args(args, ["--preScript", self.pre_script])
        elif self.db_ili_version is None or self.db_ili_version > 3:
            self.append_args(args, ["--preScript", "NULL"])

        if self.post_script:
            self.append_args(args, ["--postScript", self.post_script])
        elif self.db_ili_version is None or self.db_ili_version > 3:
            self.append_args(args, ["--postScript", "NULL"])

        if self.db_ili_version is None or self.db_ili_version > 3:
            self.append_args(args, ["--createNlsTab"])

        self.append_args(
            args, Ili2DbCommandConfiguration.to_ili2db_args(self), force_append=True
        )

        if self.ilifile:
            self.append_args(args, [self.ilifile], force_append=True)

        return args


class ImportDataConfiguration(SchemaImportConfiguration):
    def __init__(self, other: Ili2DbCommandConfiguration = None):
        super().__init__(other)
        self.xtffile = ""
        self.delete_data = False
        self.with_importtid = False
        self.dataset = ""
        self.baskets = list()
        self.with_schemaimport = False

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            self.append_args(args, ["--import"])

        if self.with_schemaimport:
            self.append_args(args, ["--doSchemaImport"])

        if self.disable_validation:
            self.append_args(args, ["--disableValidation"])

        if self.delete_data:
            self.append_args(args, ["--deleteData"])

        if self.with_importtid:
            self.append_args(args, ["--importTid"])

        if self.dataset:
            self.append_args(args, ["--dataset", self.dataset])

        if self.baskets:
            self.append_args(args, ["--baskets", ";".join(self.baskets)])

        if self.with_schemaimport:
            self.append_args(
                args,
                SchemaImportConfiguration.to_ili2db_args(
                    self, extra_args=extra_args, with_action=False
                ),
            )
        else:
            self.append_args(args, extra_args)

            self.append_args(
                args, Ili2DbCommandConfiguration.to_ili2db_args(self), force_append=True
            )

        self.append_args(args, [self.xtffile])

        return args


class UpdateDataConfiguration(Ili2DbCommandConfiguration):
    def __init__(self, other: Ili2DbCommandConfiguration = None):
        super().__init__(other)
        self.xtffile = ""
        self.dataset = ""
        self.delete_data = False
        self.with_importtid = False
        self.with_importbid = False

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            if self.delete_data:
                self.append_args(args, ["--replace"])
            else:
                self.append_args(args, ["--update"])

        self.append_args(args, extra_args)

        if self.disable_validation:
            self.append_args(args, ["--disableValidation"])

        if self.with_importtid:
            self.append_args(args, ["--importTid"])

        if self.with_importbid:
            self.append_args(args, ["--importBid"])

        self.append_args(args, ["--dataset", self.dataset])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        self.append_args(args, [self.xtffile])

        return args


class ValidateConfiguration(Ili2DbCommandConfiguration):
    def __init__(self, other: Ili2DbCommandConfiguration = None):
        super().__init__(other)
        self.ilimodels = ""
        self.topics = ""
        self.dataset = ""
        self.baskets = list()
        self.iliexportmodels = ""
        self.with_exporttid = False
        self.xtflog = ""
        self.skip_geometry_errors = False
        self.valid_config = ""
        self.xtffile = ""

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            self.append_args(args, ["--validate"])

        self.append_args(args, extra_args)

        if self.ilimodels:
            self.append_args(args, ["--models", self.ilimodels])

        if self.iliexportmodels:
            self.append_args(args, ["--exportModels", self.iliexportmodels])

        if self.topics:
            self.append_args(args, ["--topics", self.topics])

        if self.dataset:
            self.append_args(args, ["--dataset", self.dataset])

        if self.baskets:
            self.append_args(args, ["--baskets", ";".join(self.baskets)])

        if self.with_exporttid:
            self.append_args(args, ["--exportTid"])

        if self.db_ili_version == 3:
            self.append_args(args, ["--export3"])

        if self.xtflog:
            self.append_args(args, ["--xtflog", self.xtflog])

        if self.skip_geometry_errors:
            self.append_args(args, ["--skipGeometryErrors"])
            self.append_args(args, ["--disableAreaValidation"])

        if self.valid_config:
            self.append_args(args, ["--validConfig", self.valid_config])

        if self.db_ili_version == 3:
            self.append_args(args, [self.xtffile])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        return args


class DeleteConfiguration(Ili2DbCommandConfiguration):
    def __init__(self, other: Ili2DbCommandConfiguration = None):
        super().__init__(other)
        self.dataset = ""
        self.baskets = ""

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            self.append_args(args, ["--delete"])

        self.append_args(args, extra_args)

        if self.dataset:
            self.append_args(args, ["--dataset", self.dataset])

        if self.baskets:
            self.append_args(args, ["--baskets", self.baskets])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        return args


class ExportMetaConfigConfiguration(Ili2DbCommandConfiguration):
    def __init__(self, other: Ili2DbCommandConfiguration = None):
        super().__init__(other)
        self.metaconfigoutputfile = ""

    def to_ili2db_args(self, extra_args=[], with_action=True):
        args = list()

        if with_action:
            self.append_args(args, ["--exportMetaConfig"])

        self.append_args(args, extra_args)

        self.append_args(args, ["--metaConfig", self.metaconfigoutputfile])

        self.append_args(args, Ili2DbCommandConfiguration.to_ili2db_args(self))

        return args
