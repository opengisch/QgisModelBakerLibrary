"""
/***************************************************************************
                              -------------------
        begin                : 2017-04-12
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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

from typing import TYPE_CHECKING

from qgis.core import QgsDefaultValue, QgsEditorWidgetSetup, QgsFieldConstraints

if TYPE_CHECKING:
    from .layers import Layer


class Field:
    def __init__(self, name: str) -> None:
        self.name = name
        self.alias = None
        self.read_only = False
        self.widget = None
        self.widget_config = dict()
        self.default_value_expression = None
        self.enum_domain = None
        self.oid_domain = None

    def dump(self) -> dict:
        definition = dict()
        if self.alias:
            definition["alias"] = self.alias

        return definition

    def load(self, definition: dict) -> None:
        if "alias" in definition:
            self.alias = definition["alias"]

    def create(self, layer: Layer) -> None:
        field_idx = layer.layer.fields().indexOf(self.name)

        if self.alias:
            layer.layer.setFieldAlias(field_idx, self.alias)

        if self.widget:
            setup = QgsEditorWidgetSetup(self.widget, self.widget_config)
            layer.layer.setEditorWidgetSetup(field_idx, setup)

        if self.default_value_expression:
            default_value = QgsDefaultValue(self.default_value_expression)
            layer.layer.setDefaultValueDefinition(field_idx, default_value)

        if self.oid_domain:
            # if defined, then set not null and unique constraints
            layer.layer.setFieldConstraint(
                field_idx,
                QgsFieldConstraints.Constraint.ConstraintNotNull,
                QgsFieldConstraints.ConstraintStrength.ConstraintStrengthHard,
            )
            layer.layer.setFieldConstraint(
                field_idx,
                QgsFieldConstraints.Constraint.ConstraintUnique,
                QgsFieldConstraints.ConstraintStrength.ConstraintStrengthHard,
            )
