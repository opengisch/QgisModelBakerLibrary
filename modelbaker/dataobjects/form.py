"""
/***************************************************************************
                              -------------------
        begin                : 08/08/17
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

from typing import TYPE_CHECKING, Optional, Union

from qgis.core import (
    Qgis,
    QgsAttributeEditorContainer,
    QgsAttributeEditorElement,
    QgsAttributeEditorField,
    QgsAttributeEditorRelation,
    QgsEditFormConfig,
    QgsVectorLayer,
)

if TYPE_CHECKING:
    from .layers import Layer
    from .project import Project
    from .relations import Relation


class FormFieldWidget:
    def __init__(self, name: str, field_name: str) -> None:
        self.name = name if name else field_name
        self.field_name = field_name

    def create(
        self, parent: QgsAttributeEditorElement, layer: QgsVectorLayer
    ) -> QgsAttributeEditorField:
        index = layer.fields().indexOf(self.field_name)
        widget = QgsAttributeEditorField(self.field_name, index, parent)
        return widget


class FormRelationWidget:
    def __init__(
        self, relation: Relation, nm_relation: Optional[Relation] = None
    ) -> None:
        self.relation = relation
        self.nm_relation = nm_relation

    def create(
        self, parent: QgsAttributeEditorElement, _layer
    ) -> QgsAttributeEditorRelation:
        try:
            widget = QgsAttributeEditorRelation(self.relation.id, parent)
        except TypeError:
            # Feed deprecated API for 3.0.0 and 3.0.1
            widget = QgsAttributeEditorRelation(
                self.relation.id, self.relation.id, parent
            )
        if self.nm_relation:
            widget.setNmRelationId(self.nm_relation.id)

        if Qgis.QGIS_VERSION_INT >= 31800:
            widget.setRelationWidgetTypeId("linking_relation_editor")

            if not self.nm_relation and self.relation.cardinality_max == "1":
                configuration = widget.relationEditorConfiguration()
                configuration["one_to_one"] = True
                widget.setRelationEditorConfiguration(configuration)

        return widget


class FormTab:
    def __init__(self, name: str, columns: int = 1) -> None:
        self.name = name
        self.children = list()
        self.columns = columns

    def addChild(self, child: Union[FormFieldWidget, FormRelationWidget]) -> None:
        self.children.append(child)

    def create(
        self, parent: QgsAttributeEditorElement, layer: QgsVectorLayer
    ) -> QgsAttributeEditorContainer:
        container = QgsAttributeEditorContainer(self.name, parent)
        container.setIsGroupBox(False)
        container.setColumnCount(self.columns)

        for child in self.children:
            container.addChildElement(child.create(container, layer))
        return container


class Form:
    def __init__(self) -> None:
        self.__elements = list()

    def elements(self) -> list[Union[FormFieldWidget, FormRelationWidget]]:
        return self.__elements

    def create(
        self, layer: Layer, qgis_layer: QgsVectorLayer, project: Project
    ) -> QgsEditFormConfig:
        edit_form_config = qgis_layer.editFormConfig()
        root_container = edit_form_config.invisibleRootContainer()
        root_container.clear()
        for element in self.__elements:
            root_container.addChildElement(element.create(root_container, qgis_layer))
        edit_form_config.setLayout(QgsEditFormConfig.EditorLayout.TabLayout)
        # set nm-rel if referencing tables are junction table
        for relation in project.relations:
            if relation.referenced_layer == layer:
                # get other relations, that have the same referencing_layer and set the first as nm-rel
                for other_relation in project.relations:
                    if (
                        other_relation.referencing_field != relation.referencing_field
                        and other_relation.referencing_layer
                        == relation.referencing_layer
                        and relation.referencing_layer.is_nmrel
                        and not other_relation.referenced_layer.is_basket_table
                    ):
                        edit_form_config.setWidgetConfig(
                            relation.id, {"nm-rel": other_relation.id}
                        )
                        break
        return edit_form_config

    def add_element(self, element: Union[FormTab, FormFieldWidget]) -> None:
        self.__elements.append(element)


class FormGroupBox:
    def __init__(self, name: str, columns: int = 1) -> None:
        self.name = name
        self.children = list()
        self.columns = columns

    def addChild(self, child) -> None:
        self.children.append(child)

    def create(self, _parent, layer) -> QgsAttributeEditorContainer:
        container = QgsAttributeEditorContainer(self.name)
        container.setIsGroupBox(True)
        container.setColumnCount(self.columns)

        for child in self.children:
            container.addChildElement(child, layer)
        return container
