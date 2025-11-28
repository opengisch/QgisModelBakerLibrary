"""
Metadata:
    Creation Date: 2017-03-23
    Copyright: (C) 2017 by OPENGIS.ch
    Contact: info@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""


from .ili2dbconfig import UpdateDataConfiguration
from .iliexecutable import IliExecutable


class Updater(IliExecutable):
    """Executes an update operation on ili2db."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_config(self) -> UpdateDataConfiguration:
        return UpdateDataConfiguration()
