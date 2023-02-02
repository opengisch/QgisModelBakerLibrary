"""
/***************************************************************************
                              -------------------
        begin                : 11/11/21
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

import xml.etree.ElementTree as CET
from enum import Enum

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from .ili2dbconfig import ValidateConfiguration
from .iliexecutable import IliExecutable


class Validator(IliExecutable):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _create_config(self):
        return ValidateConfiguration()


class ValidationResultModel(QStandardItemModel):
    """
    Model containing all the error/warning data of the current xtf file.
    """

    class Roles(Enum):
        ID = Qt.UserRole + 1
        MESSAGE = Qt.UserRole + 2
        TYPE = Qt.UserRole + 3
        OBJ_TAG = Qt.UserRole + 4
        TID = Qt.UserRole + 5
        TECH_ID = Qt.UserRole + 6
        USER_ID = Qt.UserRole + 7
        ILI_Q_NAME = Qt.UserRole + 8
        DATA_SOURCE = Qt.UserRole + 9
        LINE = Qt.UserRole + 10
        COORD_X = Qt.UserRole + 11
        COORD_Y = Qt.UserRole + 12
        TECH_DETAILS = Qt.UserRole + 13

        FIXED = Qt.UserRole + 14

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()
        self.configuration = ValidateConfiguration()
        self.valid = False

    def get_element_text(self, element):
        if element is not None:
            return element.text
        return None

    def reload(self):
        self.beginResetModel()
        if self.configuration.xtflog:
            try:
                root = CET.parse(self.configuration.xtflog).getroot()
            except CET.ParseError as e:
                print(
                    self.tr(
                        "Could not parse ilidata file `{file}` ({exception})".format(
                            file=self.configuration.xtflog, exception=str(e)
                        )
                    )
                )
            if root:
                ns = "{http://www.interlis.ch/INTERLIS2.3}"
                for error in root.iter(ns + "IliVErrors.ErrorLog.Error"):
                    id = error.attrib["TID"]
                    message = self.get_element_text(error.find(ns + "Message"))
                    type = self.get_element_text(error.find(ns + "Type"))
                    obj_tag = self.get_element_text(error.find(ns + "ObjTag"))
                    tid = self.get_element_text(error.find(ns + "Tid"))
                    tech_id = self.get_element_text(error.find(ns + "TechId"))
                    user_id = self.get_element_text(error.find(ns + "UserId"))
                    ili_q_name = self.get_element_text(error.find(ns + "IliQName"))
                    data_source = self.get_element_text(error.find(ns + "DataSource"))
                    line = self.get_element_text(error.find(ns + "Line"))
                    coord_x = None
                    coord_y = None
                    geometry = error.find(ns + "Geometry")
                    if geometry:
                        coord = geometry.find(ns + "COORD")
                        if coord:
                            coord_x = self.get_element_text(coord.find(ns + "C1"))
                            coord_y = self.get_element_text(coord.find(ns + "C2"))
                    tech_details = self.get_element_text(error.find(ns + "TechDetails"))

                    if type in ["Error", "Warning"] and message != "...validate failed":
                        item = QStandardItem()
                        item.setData(id, int(ValidationResultModel.Roles.ID))
                        item.setData(message, int(ValidationResultModel.Roles.MESSAGE))
                        item.setData(type, int(ValidationResultModel.Roles.TYPE))
                        item.setData(obj_tag, int(ValidationResultModel.Roles.OBJ_TAG))
                        item.setData(tid, int(ValidationResultModel.Roles.TID))
                        item.setData(tech_id, int(ValidationResultModel.Roles.TECH_ID))
                        item.setData(user_id, int(ValidationResultModel.Roles.USER_ID))
                        item.setData(
                            ili_q_name, int(ValidationResultModel.Roles.ILI_Q_NAME)
                        )
                        item.setData(
                            data_source, int(ValidationResultModel.Roles.DATA_SOURCE)
                        )
                        item.setData(line, int(ValidationResultModel.Roles.LINE))
                        item.setData(coord_x, int(ValidationResultModel.Roles.COORD_X))
                        item.setData(coord_y, int(ValidationResultModel.Roles.COORD_Y))
                        item.setData(
                            tech_details, int(ValidationResultModel.Roles.TECH_DETAILS)
                        )
                        item.setData(False, int(ValidationResultModel.Roles.FIXED))
                        self.appendRow(item)
        self.endResetModel()
