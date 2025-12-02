"""
Metadata:
    Creation Date: 2017-10-03
    Copyright: (C) 2017 by Matthias Kuhn
    Contact: matthias@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""
from enum import IntFlag


class DbIliMode(IntFlag):
    pg = 1
    gpkg = 2
    mssql = 4

    ili = 1024

    ili2pg = ili | pg
    ili2gpkg = ili | gpkg
    ili2mssql = ili | mssql
