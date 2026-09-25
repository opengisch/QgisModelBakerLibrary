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

from typing import Any, Optional

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingParameterDatabaseSchema,
    QgsProcessingParameterProviderConnection,
    QgsProviderConnectionException,
    QgsProviderRegistry,
)
from qgis.PyQt.QtCore import QCoreApplication

from ..iliwrapper.ili2dbconfig import Ili2DbCommandConfiguration
from ..utils.db_utils import get_configuration_from_data_connection
from .util_algorithm import UtilAlgorithm


class DataConnectionParsingPGAlgorithm(UtilAlgorithm):
    """
    This is an algorithm from Model Baker.

    It is meant for reading the data source parameters from the PostgreSQL data connections configured on the QGIS profile.
    """

    # Connection
    DATABASE = "DATABASE"

    # Results
    SERVICE = "SERVICE"
    HOST = "HOST"
    DBNAME = "DBNAME"
    PORT = "PORT"
    USER = "USER"
    PASSWORD = "PASSWORD"  # nosec # pragma: allowlist secret
    SSLMODE = "SSLMODE"
    AUTHCFG = "AUTHCFG"
    SCHEMA = "SCHEMA"
    ISVALID = "ISVALID"

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_util_pg_dataconnection"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Get connection from profile (PostGIS)")

    def tags(self) -> list[str]:

        return [
            "source",
            "database",
            "profile",
            "data",
            "modelbaker",
            "ili2db",
            "interlis",
            "postgis",
            "postgresql",
        ]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr(
            """<html><head/><body>
            <p>Receives PostGIS connection parameters from the data connections configured on the QGIS profile.</p>
            <p>Provides the parameters to be used in the Model Baker ili2db algorithms.</p>
            <p>Returns the authentication configuration ID and pg-service name, even if the username and password have already been parsed from it.</p>
        </body></html>
        """
        )

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr(
            """<html><head/><body>
            <p>Receives PostGIS connection parameters from the data connections configured on the QGIS profile.</p>
            <p>Provides the parameters to be used in the Model Baker ili2db algorithms.</p>
            <p>Returns the authentication configuration ID and pg-service name, even if the username and password have already been parsed from it.</p>
        </body></html>
        """
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        db_param = QgsProcessingParameterProviderConnection(
            self.DATABASE, self.tr("Data Connection"), "postgres"
        )
        db_param.setHelp(
            self.tr(
                "Data connections configured on the QGIS profile. If set, it will be prefered over the other connection settings."
            )
        )

        self.addParameter(db_param)

        schema_param = QgsProcessingParameterDatabaseSchema(
            self.SCHEMA,
            self.tr("Existing Schema"),
            defaultValue="public",
            connectionParameterName=self.DATABASE,
            optional=True,
        )
        schema_param.setHelp(
            self.tr(
                "Schema name to be used for the connection. If a new schema is created, this parameter will be ignored."
            )
        )

        self.addParameter(schema_param)

        self.addOutput(QgsProcessingOutputString(self.SERVICE, self.tr("Service")))
        self.addOutput(QgsProcessingOutputString(self.HOST, self.tr("Host")))
        self.addOutput(QgsProcessingOutputString(self.DBNAME, self.tr("Database")))
        self.addOutput(QgsProcessingOutputNumber(self.PORT, self.tr("Port")))
        self.addOutput(QgsProcessingOutputString(self.USER, self.tr("User")))
        self.addOutput(QgsProcessingOutputString(self.PASSWORD, self.tr("Password")))
        self.addOutput(QgsProcessingOutputString(self.SCHEMA, self.tr("Schema")))
        self.addOutput(QgsProcessingOutputString(self.SSLMODE, self.tr("SSL Mode")))
        self.addOutput(
            QgsProcessingOutputString(self.AUTHCFG, self.tr("Authentication"))
        )
        self.addOutput(QgsProcessingOutputString(self.ISVALID, self.tr("Is Valid")))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        is_valid = True
        configuration = Ili2DbCommandConfiguration()
        connection_name = self.parameterAsConnectionName(
            parameters, self.DATABASE, context
        )

        try:
            md = QgsProviderRegistry.instance().providerMetadata("postgres")
            conn = md.createConnection(connection_name)
            valid, mode = get_configuration_from_data_connection(conn, configuration)
            configuration.dbschema = self.parameterAsString(
                parameters, self.SCHEMA, context
            )

            if not (valid and mode):
                self.tr(
                    "Invalid connection settings. Please check the connection parameters. Nevertheless I provide you what I got."
                )
                is_valid = False

        except QgsProviderConnectionException:
            raise QgsProcessingException(
                self.tr("Could not retrieve connection details for {}").format(
                    connection_name
                )
            )

        if feedback.isCanceled():
            return {}

        return {
            self.SERVICE: configuration.dbservice,
            self.HOST: configuration.dbhost,
            self.PORT: configuration.dbport,
            self.DBNAME: configuration.database,
            self.USER: configuration.dbusr,
            self.PASSWORD: configuration.dbpwd,
            self.SCHEMA: configuration.dbschema,
            self.SSLMODE: configuration.sslmode,
            self.AUTHCFG: configuration.dbauthid,
            self.ISVALID: is_valid,
        }

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return self.__class__()


class DataConnectionParsingGPKGAlgorithm(UtilAlgorithm):
    """
    This is an algorithm from Model Baker.

    It is meant for reading the data source parameters from the GPKG data connections configured on the QGIS profile.
    """

    # Connection
    DATABASE = "DATABASE"
    ## GPKG
    DBPATH = "DBPATH"
    ISVALID = "ISVALID"

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_util_gpkg_dataconnection"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Get connection from profile (GeoPackage)")

    def tags(self) -> list[str]:

        return [
            "source",
            "database",
            "profile",
            "data",
            "modelbaker",
            "ili2db",
            "interlis",
            "gpkg",
            "geopackage",
        ]

    def shortDescription(self) -> str:
        """
        Returns a short description string for the algorithm.
        """
        return self.tr(
            """<html><head/><body>
            <p>Receives GeoPackage connection parameters from the data connections configured on the QGIS profile.</p>
            <p>Provides the parameters to be used in the Model Baker ili2db algorithms.</p>
        </body></html>
        """
        )

    def shortHelpString(self) -> str:
        """
        Returns a short helper string for the algorithm.
        """
        return self.tr(
            """<html><head/><body>
            <p>Receives GeoPackage connection parameters from the data connections configured on the QGIS profile.</p>
            <p>Provides the parameters to be used in the Model Baker ili2db algorithms.</p>
        </body></html>
        """
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        db_param = QgsProcessingParameterProviderConnection(
            self.DATABASE, self.tr("Data Connection"), "ogr"
        )
        db_param.setHelp(
            self.tr(
                "Data connections configured on the QGIS profile. If set, it will be prefered over the other connection settings."
            )
        )

        self.addParameter(db_param)

        self.addOutput(QgsProcessingOutputString(self.DBPATH, self.tr("Database Path")))
        self.addOutput(QgsProcessingOutputString(self.ISVALID, self.tr("Is Valid")))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        is_valid = True
        configuration = Ili2DbCommandConfiguration()
        connection_name = self.parameterAsConnectionName(
            parameters, self.DATABASE, context
        )

        try:
            md = QgsProviderRegistry.instance().providerMetadata("ogr")
            conn = md.createConnection(connection_name)
            valid, mode = get_configuration_from_data_connection(conn, configuration)

            if not (valid and mode):
                self.tr(
                    "Invalid connection settings. Please check the connection parameters."
                )
                return {self.ISVALID: False}

        except QgsProviderConnectionException:
            raise QgsProcessingException(
                self.tr("Could not retrieve connection details for {}").format(
                    connection_name
                )
            )

        if feedback.isCanceled():
            return {}

        return {
            self.ISVALID: is_valid,
            self.DBPATH: configuration.dbfile,
        }

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return self.__class__()
