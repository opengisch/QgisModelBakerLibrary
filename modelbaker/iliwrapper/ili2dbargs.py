"""
/***************************************************************************
                              -------------------
        begin                : 07.03.2022
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer / (C) 2021 Germán Carrillo
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

import logging

from qgis.PyQt.QtCore import QDir, QFile

from ..utils.db_utils import get_authconfig_map
from .globals import DbIliMode
from .ili2dbconfig import SchemaImportConfiguration


def get_ili2db_args(configuration, hide_password=False):
    """Gets a complete list of ili2db arguments in order to execute the app.

    :param bool hide_password: *True* to mask the password, *False* otherwise.
    :return: ili2db arguments list.
    :rtype: list
    """
    db_args = _get_db_args(configuration, hide_password)

    if type(configuration) is SchemaImportConfiguration:
        db_args += _get_schema_import_args(configuration.tool)

    return configuration.to_ili2db_args(db_args)


def _get_db_args(configuration, hide_password=False):
    su = configuration.db_use_super_login  # Boolean
    db_args = list()

    if configuration.tool in DbIliMode.ili2gpkg:
        db_args = ["--dbfile", configuration.dbfile]
    elif configuration.tool in DbIliMode.ili2pg:
        db_args += ["--dbhost", configuration.dbhost]
        if configuration.dbport:
            db_args += ["--dbport", configuration.dbport]
        if su:
            db_args += ["--dbusr", configuration.base_configuration.super_pg_user]
        elif configuration.dbauthid and get_authconfig_map(configuration.dbauthid):
            # Operations like export do not require superuser
            # login and may be run with the credentials from the authconfig
            authconfig_map = get_authconfig_map(configuration.dbauthid)
            db_args += ["--dbusr", authconfig_map.get("username")]
        else:
            db_args += ["--dbusr", configuration.dbusr]
        if (
            not su
            and (configuration.dbpwd or configuration.dbauthid)
            or su
            and configuration.base_configuration.super_pg_password
        ):
            if hide_password:
                # only append placeholder for password if it has one at all
                if configuration.dbpwd:
                    db_args += ["--dbpwd", "******"]
                elif configuration.dbauthid and get_authconfig_map(
                    configuration.dbauthid
                ):
                    authconfig_map = get_authconfig_map(configuration.dbauthid)
                    db_args += ["--dbpwd", "******"]
            else:
                if su:
                    db_args += [
                        "--dbpwd",
                        configuration.base_configuration.super_pg_password,
                    ]
                elif configuration.dbpwd:
                    db_args += ["--dbpwd", configuration.dbpwd]
                elif configuration.dbauthid and get_authconfig_map(
                    configuration.dbauthid
                ):
                    # Operations like export do not require superuser
                    # login and may be run with the credentials from the authconfig
                    authconfig_map = get_authconfig_map(configuration.dbauthid)
                    db_args += ["--dbpwd", authconfig_map.get("password")]

        db_args += ["--dbdatabase", configuration.database]
        db_args += ["--dbschema", configuration.dbschema or configuration.database]

        if configuration.sslmode:
            if "sslmode" not in configuration.base_configuration.dbparam_map:
                configuration.base_configuration.dbparam_map[
                    "sslmode"
                ] = configuration.sslmode
        if configuration.base_configuration.dbparam_map:
            temporary_filename = "{}/modelbaker-dbargs.conf".format(QDir.tempPath())
            temporary_file = QFile(temporary_filename)
            if temporary_file.open(QFile.OpenModeFlag.WriteOnly):
                if configuration.base_configuration.dbparam_map:
                    for key in configuration.base_configuration.dbparam_map.keys():
                        temporary_file.write(
                            "{}={}\n".format(
                                key, configuration.base_configuration.dbparam_map[key]
                            ).encode("utf-8")
                        )
                temporary_file.close()
                db_args += ["--dbparams", temporary_filename]
            else:
                logger = logging.getLogger(__name__)
                logger.warning(
                    "Could not open termporary file for writing: '{}'".format(
                        temporary_filename
                    )
                )

    elif configuration.tool in DbIliMode.ili2mssql:
        db_args += ["--dbhost", configuration.dbhost]
        if configuration.dbport:
            db_args += ["--dbport", configuration.dbport]
        db_args += ["--dbusr", configuration.dbusr]
        if configuration.dbpwd:
            if hide_password:
                db_args += ["--dbpwd", "******"]
            else:
                db_args += ["--dbpwd", configuration.dbpwd]
        db_args += ["--dbdatabase", configuration.database]
        db_args += ["--dbschema", configuration.dbschema or configuration.database]
        if configuration.dbinstance:
            db_args += ["--dbinstance", configuration.dbinstance]

    return db_args


def _get_schema_import_args(tool):
    args = list()
    if tool == DbIliMode.ili2pg:
        args += ["--setupPgExt"]
    return args
