# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-07-17
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
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
import os

from ..libs.toppingmaker import Target
from ..libs.toppingmaker.utils import slugify


class IliTarget(Target):
    """
    Extended class of toppingmaker.Target containing additional parameters like owner, publishing_date and version.
    And a path_resolver adding an id to the toppingfile in the toppingfile_list.
    """

    def __init__(
        self,
        projectname: str = "project",
        main_dir: str = None,
        sub_dir: str = None,
        path_resolver=None,
        owner="owner",
        publishing_date=None,
        version=None,
    ):
        if not path_resolver:
            path_resolver = self.ilidata_path_resolver
        super().__init__(projectname, main_dir, sub_dir, path_resolver)
        self.default_owner = owner
        self.default_publishing_date = (
            publishing_date or datetime.datetime.now().strftime("%Y-%m-%d")
        )
        self.default_version = version or datetime.datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def ilidata_path_resolver(target, name, type):
        """
        A path_resolver adding an id to the toppingfile in the toppingfile_list.

        The id is created with the type (like defintionfile, metaconfig etc.) and the filename.
        For uniqueness there is an incrementing number appended.

        Returns the id with the prefix "ilidata:". When using it as link, modelbaker knows that it has to look the id up in the ilidata.xml.
        """
        _, relative_filedir_path = target.filedir_path(type)

        id = target.unique_id_in_target_scope(target, slugify(f"{type}_{name}_001"))
        path = os.path.join(relative_filedir_path, name)
        type = type
        toppingfile = {"id": id, "path": path, "type": type}
        target.toppingfileinfo_list.append(toppingfile)
        return f"ilidata:{id}"

    @staticmethod
    def unique_id_in_target_scope(target, id):
        for toppingfileinfo in target.toppingfileinfo_list:
            if "id" in toppingfileinfo and toppingfileinfo["id"] == id:
                iterator = int(id[-3:])
                iterator += 1
                id = f"{id[:-3]}{iterator:03}"
                return target.unique_id_in_target_scope(target, id)
        return id
