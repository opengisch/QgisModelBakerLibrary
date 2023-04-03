"""
/***************************************************************************
        begin                : 18.08.2021
        git sha              : :%H$
        copyright            : (C) 2021 by Dave Signer
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

from qgis.core import (
    QgsApplication,
    QgsAuthMethodConfig,
    QgsDataSourceUri,
    QgsMessageLog,
)

from ..db_factory.db_simple_factory import DbSimpleFactory
from ..dbconnector.db_connector import DBConnectorError
from ..iliwrapper.globals import DbIliMode
from ..libs import pgserviceparser
from .qt_utils import slugify


def get_schema_identificator_from_sourceprovider(provider):
    if provider.name() == "postgres" or provider.name() == "mssql":
        layer_source = QgsDataSourceUri(provider.dataSourceUri())
        return slugify(
            f"{layer_source.host()}_{layer_source.database()}_{layer_source.schema()}"
        )
    elif provider.name() == "ogr" and provider.storageType() == "GPKG":
        return slugify(provider.dataSourceUri().split("|")[0].strip())
    return ""


def get_schema_identificator_from_configuration(configuration):
    if configuration.tool == DbIliMode.pg or configuration.tool == DbIliMode.mssql:
        return slugify(
            f"{configuration.dbhost}_{configuration.database}_{configuration.dbschema}"
        )
    elif configuration.tool == DbIliMode.gpkg:
        return slugify(configuration.dbfile)
    return ""


def get_authconfig_map(authconfigid):
    # to get username and password from the authconfig
    auth_mgr = QgsApplication.authManager()
    auth_cfg = QgsAuthMethodConfig()
    auth_mgr.loadAuthenticationConfig(authconfigid, auth_cfg, True)
    return auth_cfg.configMap()


def get_configuration_from_sourceprovider(provider, configuration):
    """
    Determines the connection parameters from a layer source provider.
    On service in postgres it preferences the static parameters over the ones in the service file if available.
    Returns:
        valid (boolean): if the needed database connection parameters are determined
        mode (DbIliMode): Kind of database like pg, gpkg or mssql
        configuration (Ili2DbCommandConfiguration): config with the determined parameters
    """
    mode = ""
    valid = False
    if provider.name() == "postgres":
        layer_source = QgsDataSourceUri(provider.dataSourceUri())
        mode = DbIliMode.pg
        configuration.dbservice = layer_source.service()
        service_map = pgserviceparser.service_config(configuration.dbservice)
        if layer_source.authConfigId():
            configuration.dbauthid = layer_source.authConfigId()
            authconfig_map = get_authconfig_map(configuration.dbauthid)
            configuration.dbusr = authconfig_map.get("username")
            configuration.dbpwd = authconfig_map.get("password")
        else:
            configuration.dbusr = layer_source.username() or service_map.get("user")
            configuration.dbpwd = layer_source.password() or service_map.get("password")
        configuration.dbhost = layer_source.host() or service_map.get("host")
        configuration.database = layer_source.database() or service_map.get("dbname")
        configuration.dbschema = layer_source.schema()
        valid = bool(
            configuration.dbusr
            and configuration.dbpwd
            and configuration.dbhost
            and configuration.database
            and configuration.dbschema
        )
    elif provider.name() == "ogr" and provider.storageType() == "GPKG":
        mode = DbIliMode.gpkg
        configuration.dbfile = provider.dataSourceUri().split("|")[0].strip()
        valid = bool(configuration.dbfile)
    elif provider.name() == "mssql":
        mode = DbIliMode.mssql
        layer_source = QgsDataSourceUri(provider.dataSourceUri())
        configuration.dbhost = layer_source.host()
        configuration.dbusr = layer_source.username()
        configuration.dbpwd = layer_source.password()
        configuration.database = layer_source.database()
        configuration.dbschema = layer_source.schema()
        valid = bool(
            configuration.dbusr
            and configuration.dbpwd
            and configuration.dbhost
            and configuration.database
            and configuration.dbschema
        )
    return valid, mode


def get_db_connector(configuration):
    db_simple_factory = DbSimpleFactory()
    schema = configuration.dbschema

    db_factory = db_simple_factory.create_factory(configuration.tool)
    config_manager = db_factory.get_db_command_config_manager(configuration)
    uri_string = config_manager.get_uri(configuration.db_use_super_login)

    try:
        return db_factory.get_db_connector(uri_string, schema)
    except DBConnectorError as db_connector_error:
        QgsMessageLog.logMessage(
            "There was an error connecting to the database. Check connection parameters. Error details: {}".format(
                db_connector_error
            ),
            "QGIS Model Baker",
        )
        return None
    except FileNotFoundError as file_not_found_error:
        QgsMessageLog.logMessage(
            "There was an error connecting to the database. Check connection parameters. Error details: {}".format(
                file_not_found_error
            ),
            "QGIS Model Baker",
        )
        return None


def db_ili_version(configuration):
    """
    Returns the ili2db version the database has been created with or None if the database
    could not be detected as a ili2db database
    """
    db_connector = get_db_connector(configuration)
    if db_connector:
        return db_connector.ili_version()
