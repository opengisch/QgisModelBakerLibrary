"""
/***************************************************************************
    begin                :    08/04/19
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

import logging
from typing import Optional

from ..iliwrapper.globals import DbIliMode
from .db_factory import DbFactory

available_database_factories = dict()
try:
    from .pg_factory import PgFactory

    available_database_factories.update({DbIliMode.pg: PgFactory})
except ModuleNotFoundError:
    pass
try:
    from .gpkg_factory import GpkgFactory

    available_database_factories.update({DbIliMode.gpkg: GpkgFactory})
except ModuleNotFoundError:
    pass
try:
    from .mssql_factory import MssqlFactory

    available_database_factories.update({DbIliMode.mssql: MssqlFactory})
except ModuleNotFoundError:
    pass


class DbSimpleFactory:
    """Provides a single point (simple factory) to create a database factory (:class:`DbFactory`)."""

    def create_factory(self, ili_mode: DbIliMode) -> Optional[DbFactory]:
        """Creates an instance of :class:`DbFactory` based on ili_mode parameter.

        :param ili_mode: Value specifying which factory will be instantiated.
        :type ili_mode: :class:`DbIliMode`
        :return: A database factory
        """
        if not ili_mode:
            return None

        index = ili_mode & (~DbIliMode.ili)
        result = None

        if DbIliMode(index) in available_database_factories:
            result = available_database_factories[
                DbIliMode(index)
            ]()  # instantiate factory
        else:
            logger = logging.getLogger(__name__)
            logger.warning("Database factory not found for '{}'".format(index.name))

        return result

    def get_db_list(self, is_schema_import: bool = False) -> list[DbIliMode]:
        """Gets a list containing the databases available in modelbaker.

        This list can be used to show the available databases in GUI, for example, **QComboBox source**
        in **Import Data Dialog**.

        :param bool is_schema_import: *True* to include interlis operation values, *False* otherwise.
        :return: A list containing the databases available.
        :rtype: list
        """
        ili = []
        result = available_database_factories.keys()

        if is_schema_import:
            for item in result:
                ili += [item | DbIliMode.ili]

            result = ili + list(result)

        return result

    @property
    def default_database(self) -> DbIliMode:
        """Gets a default database for modelbaker.

        :return: Default database for modelbaker.
        :rtype: :class:`DbIliMode`
        """
        return list(available_database_factories.keys())[0]
