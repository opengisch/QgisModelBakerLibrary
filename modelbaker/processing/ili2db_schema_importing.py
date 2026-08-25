"""
Metadata:
    Creation Date: 2026-08-07
    Copyright: (C) 2026 by Germán Carrillo
    Contact: german@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""

from typing import Any, Optional

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputBoolean,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterString,
)

from ..iliwrapper import iliimporter
from ..iliwrapper.globals import DbIliMode
from ..iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
    SchemaImportConfiguration,
)
from ..iliwrapper.ili2dbutils import JavaNotFoundError
from .ili2db_algorithm import Ili2gpkgAlgorithm, Ili2pgAlgorithm
from .ili2db_operating import ProcessOperatorBase


class ProcessSchemaImporter(ProcessOperatorBase):

    # Settings
    CRS = "CRS"
    INHERITANCE = "INHERITANCE"
    BASKETCOL = "BASKETCOL"
    ENUMHANDLING = "ENUMHANDLING"
    MULTIGEOMSPERTABLE = "MULTIGEOMSPERTABLE"
    STROKEARCS = "STROKEARCS"
    MODELS = "MODELS"  # StringList
    LANGUAGE = "LANGUAGE"  # String (2)
    ILIFILE = "ILIFILE"  # File

    # Result
    ISVALID = "ISVALID"

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def import_input_params(self):
        params = []

        crs_param = QgsProcessingParameterCrs(
            self.CRS,
            self.tr("Coordinate Reference System"),
            defaultValue="EPSG:2056",
            optional=True,
        )
        crs_param.setHelp(
            self.tr("The reference system for geometry columns in the database.")
        )
        params.append(crs_param)

        inheritance_param = QgsProcessingParameterEnum(
            self.INHERITANCE,
            self.tr("Inheritance type"),
            ["smart1", "smart2", "nosmart"],
            allowMultiple=False,
            defaultValue="smart2",
            optional=False,
            usesStaticStrings=True,
        )
        inheritance_param.setHelp(
            self.tr(
                "Defines the strategy to implement class inheritance. Choose 'nosmart' to disable all optimizations."
            )
        )
        params.append(inheritance_param)

        basket_col_param = QgsProcessingParameterBoolean(
            self.BASKETCOL,
            self.tr("Create basket column"),
            defaultValue=False,
            optional=False,
        )
        basket_col_param.setHelp(
            self.tr("Creates a basket column in all the tables from the model.")
        )
        params.append(basket_col_param)

        enum_handling_param = QgsProcessingParameterEnum(
            self.ENUMHANDLING,
            self.tr("Enumeration handling"),
            ["createEnumTypesWithId", "createEnumTabs", "createEnumSingleTab"],
            allowMultiple=False,
            defaultValue="createEnumTypesWithId",
            optional=False,
            usesStaticStrings=True,
        )
        enum_handling_param.setHelp(
            self.tr(
                """<html><head/><body>
            <p><b>createEnumTypesWithId:</b> creates a table per enum-domain and links via Foreign Keys to it.</p>
            <p><b>createEnumTabs:</b> creates a table per enum-domain without Foreign Keys to it.</p>
            <p><b>createEnumSingleTab:</b> creates one table for all the enum-domains.</p>
            </body></html>"""
            )
        )
        params.append(enum_handling_param)

        if self.parent.ili2dbtool() == DbIliMode.ili2gpkg:
            multigeom_columns_param = QgsProcessingParameterBoolean(
                self.MULTIGEOMSPERTABLE,
                self.tr("Multiple geometry columns per table"),
                defaultValue=False,
                optional=False,
            )
            multigeom_columns_param.setHelp(
                self.tr(
                    "Creates multiple geometry columns per table if there is more than one geometry attribute in a class/table."
                )
            )
            params.append(multigeom_columns_param)

        stroke_arcs_param = QgsProcessingParameterBoolean(
            self.STROKEARCS,
            self.tr("Stroke arcs"),
            defaultValue=False,
            optional=False,
        )
        stroke_arcs_param.setHelp(
            self.tr(
                "Replaces any curved geometry column by its linear equivalent (e.g., CompoundCurve by LineString or MultiSurface by MultiPolygon)."
            )
        )
        params.append(stroke_arcs_param)

        language_param = QgsProcessingParameterString(
            self.LANGUAGE, self.tr("Language (semicolon-separated)"), optional=True
        )
        language_param.setHelp(
            self.tr(
                """<html><head/><body>
            <p>Defines the language for database objects like tables and columns (e.g., de, fr, it, en, es).</p>
            <p>The model definition needs to be declared as a translated version (i.e., with TRANSLATION OF keywords).</p>
            <p>Multiple languages can be separated by semicolon to regulate priority. If the given language is not provided by the model, the original model language will be used.</p>
            </body></html>"""
            )
        )
        params.append(language_param)

        models_param = QgsProcessingParameterString(
            self.MODELS, self.tr("Models (semicolon-separated)"), optional=True
        )
        models_param.setHelp(
            self.tr(
                "Name of the model(s) to import. If there are several, they can be separated by semicolon."
            )
        )
        params.append(models_param)

        ilifile_param = QgsProcessingParameterFile(
            self.ILIFILE,
            self.tr("INTERLIS Model file (.ili)"),
            extension="ili",
            optional=True,
        )
        ilifile_param.setHelp(
            self.tr(
                "Path to a local INTERLIS file with the model definition. If passed, the 'Models' parameter can be omitted, since ili2db will import the last model in the ilifile."
            )
        )
        params.append(ilifile_param)

        return params

    def import_output_params(self):
        params = [
            QgsProcessingOutputBoolean(self.ISVALID, self.tr("Schema Import Result"))
        ]

        return params

    def initParameters(self):
        for connection_input_param in self.parent.connection_input_params():
            self.parent.addParameter(connection_input_param)
        for connection_output_param in self.parent.connection_output_params():
            self.parent.addOutput(connection_output_param)

        for import_input_param in self.import_input_params():
            self.parent.addParameter(import_input_param)
        for import_output_param in self.import_output_params():
            self.parent.addOutput(import_output_param)

    def run(self, configuration, feedback):

        # run
        importer = iliimporter.Importer(self)
        importer.tool = configuration.tool

        # to do superuser finden? und auch dpparams?
        importer.configuration = configuration
        importer.stdout.connect(feedback.pushInfo)
        importer.stderr.connect(feedback.pushInfo)

        if feedback.isCanceled():
            return {}

        isvalid = False
        try:
            feedback.pushInfo(f"Run: {importer.command(True)}")
            result = importer.run(None)
            if result == iliimporter.Importer.SUCCESS:
                feedback.pushInfo(self.tr("... import succeeded"))
                isvalid = True
            else:
                feedback.pushWarning(self.tr("... import failed"))
        except JavaNotFoundError as e:
            raise QgsProcessingException(
                self.tr("Java not found error:").format(e.error_string)
            )

        return {self.ISVALID: isvalid}

    def get_configuration_from_input(self, parameters, context, tool):

        configuration = Ili2DbCommandConfiguration()
        configuration.base_configuration = self.parent.current_baseconfig()
        configuration.tool = tool

        # get database settings from the parent
        if not self.parent.get_db_configuration_from_input(
            parameters, context, configuration
        ):
            return None

        configuration = SchemaImportConfiguration(configuration)

        # get settings from the input
        crs = self.parent.parameterAsCrs(parameters, self.CRS, context)
        crsinfo = crs.authid().split(":")
        if len(crsinfo) != 2:
            return None
        configuration.srs_auth = crsinfo[0].upper()
        configuration.srs_code = crsinfo[1]

        configuration.inheritance = self.parent.parameterAsEnum(
            parameters, self.INHERITANCE, context
        )
        configuration.create_basket_col = self.parent.parameterAsBool(
            parameters, self.BASKETCOL, context
        )
        configuration.enum_tabs = self.parent.parameterAsString(
            parameters, self.ENUMHANDLING, context
        )

        if self.parent.ili2dbtool() == DbIliMode.ili2gpkg:
            configuration.create_gpkg_multigeom = self.parent.parameterAsBool(
                parameters, self.MULTIGEOMSPERTABLE, context
            )

        configuration.stroke_arcs = self.parent.parameterAsBool(
            parameters, self.STROKEARCS, context
        )
        configuration.name_lang = self.parent.parameterAsString(
            parameters, self.LANGUAGE, context
        )
        configuration.ilimodels = self.parent.parameterAsString(
            parameters, self.MODELS, context
        )
        configuration.ilifile = self.parent.parameterAsFile(
            parameters, self.ILIFILE, context
        )

        return configuration


class SchemaImportingPGAlgorithm(Ili2pgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data import to a PostgreSQL database.
    """

    def __init__(self):
        super().__init__()

        # initialize the importer with self as parent
        self.importer = ProcessSchemaImporter(self)

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2pg_schema_importer"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Schema Import with ili2pg (PostGIS)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "schema",
            "import",
            "ili2db",
            "ili2pg",
            "Postgres",
            "PostGIS",
        ]

    def shortDescription(self) -> str:
        """
        Returns the tooltip text when hovering the algorithm
        """
        return self.tr(
            """<html><head/><body>
            <p>Imports INTERLIS models to a PostgreSQL schema file with ili2pg.</p>
            <p>The ili2pg parameters are set in the same way as in the Model Baker Plugin.</p>
            <p>General Model Baker settings like custom model directories or db parameters are concerned.</p>
        </body></html>
        """
        )

    def shortHelpString(self) -> str:
        """
        Returns the help text on the right.
        """
        return self.tr(
            """<html><head/><body>
            <p>Imports INTERLIS models to a PostgreSQL schema file with ili2pg.</p>
            <p>The ili2pg parameters are set in the same way as in the Model Baker Plugin.</p>
            <p>General Model Baker settings like custom model directories or db parameters are concerned.</p>
        </body></html>
        """
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.importer.initParameters()

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        output_map = {}
        configuration = self.importer.get_configuration_from_input(
            parameters, context, DbIliMode.pg
        )
        if not configuration:
            raise QgsProcessingException(
                self.tr("Invalid input parameters. Cannot start import")
            )
        else:
            output_map.update(self.importer.run(configuration, feedback))
            output_map.update(self.get_output_from_db_configuration(configuration))
        return output_map


class SchemaImportingGPKGAlgorithm(Ili2gpkgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data import to a GeoPackage file.
    """

    def __init__(self):
        super().__init__()

        self._db_file_should_exist = False  # Allow DB destination param as input

        # initialize the importer with self as parent
        self.importer = ProcessSchemaImporter(self)

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_ili2gpkg_schema_importer"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Schema import with ili2gpkg (GeoPackage)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "schema",
            "import",
            "ili2db",
            "ili2gpkg",
            "GeoPackage",
            "GPKG",
        ]

    def shortDescription(self) -> str:
        """
        Returns the tooltip text when hovering the algorithm
        """
        return self.tr(
            """<html><head/><body>
            <p>Imports INTERLIS models to a GeoPackage file with ili2gpkg.</p>
            <p>The ili2gpkg parameters are set in the same way as in the Model Baker Plugin.</p>
            <p>General Model Baker settings like custom model directories concerned.</p>
        </body></html>
        """
        )

    def shortHelpString(self) -> str:
        """
        Returns the help text on the right.
        """
        return self.tr(
            """<html><head/><body>
            <p>Imports INTERLIS models to a GeoPackage file with ili2gpkg.</p>
            <p>The ili2gpkg parameters are set in the same way as in the Model Baker Plugin.</p>
            <p>General Model Baker settings like custom model directories concerned.</p>
        </body></html>
        """
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.importer.initParameters()

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        output_map = {}
        configuration = self.importer.get_configuration_from_input(
            parameters, context, DbIliMode.gpkg
        )
        if not configuration:
            raise QgsProcessingException(
                self.tr("Invalid input parameters. Cannot start import")
            )
        else:
            output_map.update(self.importer.run(configuration, feedback))
            output_map.update(self.get_output_from_db_configuration(configuration))
        return output_map
