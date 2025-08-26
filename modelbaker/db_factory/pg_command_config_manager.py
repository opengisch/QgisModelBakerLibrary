"""
/***************************************************************************
    begin                :    13/05/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
    email                :    yesidpol.3@gmail.com
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
from __future__ import annotations

from qgis.PyQt.QtCore import QSettings

from ..iliwrapper.ili2dbconfig import Ili2DbCommandConfiguration
from ..utils import db_utils
from .db_command_config_manager import DbCommandConfigManager


class PgCommandConfigManager(DbCommandConfigManager):
    """Manages a configuration object to return specific information of Postgres/Postgis.

    Provides database uri, arguments to ili2db and a way to save and load configurations parameters
    based on a object configuration.

    :ivar configuration object that will be managed
    """

    _settings_base_path = "ili2pg/"

    def __init__(self, configuration: Ili2DbCommandConfiguration) -> None:
        DbCommandConfigManager.__init__(self, configuration)

    def get_uri(
        self, su: bool = False, qgis: bool = False, fallback_user: str = None
    ) -> str:
        uri = []

        if su:
            uri += [
                "user={}".format(self.configuration.base_configuration.super_pg_user)
            ]
            if self.configuration.base_configuration.super_pg_password:
                uri += [
                    "password={}".format(
                        self.configuration.base_configuration.super_pg_password
                    )
                ]
            if self.configuration.sslmode:
                uri += ["sslmode='{}'".format(self.configuration.sslmode)]
            uri += ["host={}".format(self.configuration.dbhost)]
            if self.configuration.dbport:
                uri += ["port={}".format(self.configuration.dbport)]
            uri += ["dbname='{}'".format(self.configuration.database)]
            return " ".join(uri)

        if self.configuration.dbservice:
            uri += ["service='{}'".format(self.configuration.dbservice)]

        # only set the params when they are not available in the service
        service_config, _ = db_utils.get_service_config(self.configuration.dbservice)
        if not service_config or not service_config.get("sslmode", None):
            if self.configuration.sslmode:
                uri += ["sslmode='{}'".format(self.configuration.sslmode)]

        if not service_config or not service_config.get("host", None):
            uri += ["host={}".format(self.configuration.dbhost)]

        if not service_config or not service_config.get("port", None):
            if self.configuration.dbport:
                uri += ["port={}".format(self.configuration.dbport)]

        if not service_config or not service_config.get("dbname", None):
            uri += ["dbname='{}'".format(self.configuration.database)]

        if self.configuration.dbauthid and (
            not service_config
            or not (
                service_config.get("user", None)
                and service_config.get("password", None)
            )
        ):
            # only provide authcfg to the uri when it's needed for QGIS specific things
            if qgis:
                uri += ["authcfg={}".format(self.configuration.dbauthid)]
            else:
                # Operations like export do not require superuser
                # login and may be run with the credentials from the authconfig
                authconfig_map = db_utils.get_authconfig_map(
                    self.configuration.dbauthid
                )
                if authconfig_map:
                    uri += ["user={}".format(authconfig_map.get("username"))]
                    uri += ["password={}".format(authconfig_map.get("password"))]
                elif fallback_user:
                    # if the authconfig is not available, we use the fallback and get no password
                    uri += ["user={}".format(fallback_user)]
        else:
            if not service_config or not service_config.get("user", None):
                if self.configuration.dbusr:
                    uri += ["user={}".format(self.configuration.dbusr)]
                elif fallback_user:
                    uri += ["user={}".format(fallback_user)]
            if not service_config or not service_config.get("password", None):
                if self.configuration.dbpwd:
                    uri += ["password={}".format(self.configuration.dbpwd)]

        return " ".join(uri)

    def get_db_args(self, hide_password: bool = False, su: bool = False) -> list[str]:
        db_args = list()
        db_args += ["--dbhost", self.configuration.dbhost]
        if self.configuration.dbport:
            db_args += ["--dbport", self.configuration.dbport]
        if su:
            if self.configuration.base_configuration.super_pg_user:
                db_args += [
                    "--dbusr",
                    self.configuration.base_configuration.super_pg_user,
                ]
        else:
            if self.configuration.dbusr:
                db_args += ["--dbusr", self.configuration.dbusr]
        if (
            not su
            and self.configuration.dbpwd
            or su
            and self.configuration.base_configuration.super_pg_password
        ):
            if (
                self.configuration.dbpwd
                or self.configuration.base_configuration.super_pg_password
            ):
                if hide_password:
                    db_args += ["--dbpwd", "******"]
                else:
                    if su:
                        db_args += [
                            "--dbpwd",
                            self.configuration.base_configuration.super_pg_password,
                        ]
                    else:
                        db_args += ["--dbpwd", self.configuration.dbpwd]
        db_args += ["--dbdatabase", self.configuration.database]
        db_args += [
            "--dbschema",
            self.configuration.dbschema or self.configuration.database,
        ]
        return db_args

    def get_schema_import_args(self) -> list[str]:
        args = list()
        args += ["--setupPgExt"]
        return args

    def save_config_in_qsettings(self) -> None:
        settings = QSettings()
        # PostgreSQL specific options
        settings.setValue(self._settings_base_path + "host", self.configuration.dbhost)
        settings.setValue(self._settings_base_path + "port", self.configuration.dbport)
        settings.setValue(self._settings_base_path + "user", self.configuration.dbusr)
        settings.setValue(
            self._settings_base_path + "database", self.configuration.database
        )
        settings.setValue(
            self._settings_base_path + "schema", self.configuration.dbschema
        )
        settings.setValue(
            self._settings_base_path + "password", self.configuration.dbpwd
        )
        settings.setValue(
            self._settings_base_path + "usesuperlogin",
            self.configuration.db_use_super_login,
        )
        settings.setValue(
            self._settings_base_path + "authid", self.configuration.dbauthid
        )
        settings.setValue(
            self._settings_base_path + "service", self.configuration.dbservice
        )
        settings.setValue(
            self._settings_base_path + "sslmode", self.configuration.sslmode
        )

    def load_config_from_qsettings(self) -> None:
        settings = QSettings()

        self.configuration.dbhost = settings.value(
            self._settings_base_path + "host", "localhost"
        )
        self.configuration.dbport = settings.value(self._settings_base_path + "port")
        self.configuration.dbusr = settings.value(self._settings_base_path + "user")
        self.configuration.database = settings.value(
            self._settings_base_path + "database"
        )
        self.configuration.dbschema = settings.value(
            self._settings_base_path + "schema"
        )
        self.configuration.dbpwd = settings.value(self._settings_base_path + "password")
        self.configuration.dbauthid = settings.value(
            self._settings_base_path + "authid"
        )
        self.configuration.dbservice = settings.value(
            self._settings_base_path + "service"
        )
        self.configuration.db_use_super_login = settings.value(
            self._settings_base_path + "usesuperlogin", defaultValue=False, type=bool
        )
        self.configuration.sslmode = settings.value(
            self._settings_base_path + "sslmode"
        )
