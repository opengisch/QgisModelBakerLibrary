"""
/***************************************************************************
                              -------------------
        begin                : 2016-12-21
        git sha              : :%H$
        copyright            : (C) 2016 by OPENGIS.ch
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

from typing import Any, Optional, Union

from qgis.core import (
    QgsLayerDefinition,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsProject,
)

from ..utils.qgis_utils import get_group_non_recursive, get_suggested_index_for_layer
from .layers import Layer


class LegendGroup:
    def __init__(
        self,
        name: str = None,
        expanded: bool = True,
        ignore_node_names: bool = None,
        static_sorting: bool = False,
    ) -> None:
        self.name = name
        self.items = list()
        self.expanded = expanded
        self.checked = True
        self.mutually_exclusive = False
        self.mutually_exclusive_child = -1
        self.definitionfile = None

        self.static_sorting = static_sorting

        # When adding layers in order, one could want to ignore nodes (e.g.,
        # groups that should be always on top)
        self.ignore_node_names = ignore_node_names

    def dump(self) -> list[dict[str, Any]]:
        definition = list()
        for item in self.items:
            definition.append(item.dump())
        return definition

    def append(self, item: Union[LegendGroup, Layer]) -> None:
        self.items.append(item)

    def __getitem__(self, item: str) -> Union[LegendGroup, Layer]:
        for i in self.items:
            try:
                if i.name == item:
                    return i
            except AttributeError:
                if i.table_name == item:
                    return i

        raise KeyError(item)

    def load(self, definition: list[Union[LegendGroup, Layer]]) -> None:
        self.items = definition

    def create(
        self, qgis_project: QgsProject, group: Optional[QgsLayerTreeGroup] = None
    ) -> None:
        if not group:
            group = qgis_project.layerTreeRoot()

        existing_layer_source_uris = [
            found_layer.layer().dataProvider().dataSourceUri()
            for found_layer in qgis_project.layerTreeRoot().findLayers()
            if found_layer.layer().dataProvider()
        ]

        static_index = 0
        for item in self.items:
            if isinstance(item, LegendGroup):
                if item.definitionfile:
                    QgsLayerDefinition.loadLayerDefinition(
                        item.definitionfile, qgis_project, group
                    )
                else:
                    subgroup = get_group_non_recursive(group, item.name)
                    if subgroup is None:
                        subgroup = group.addGroup(item.name)
                    item.create(qgis_project, subgroup)
                    subgroup.setExpanded(item.expanded)
                    subgroup.setItemVisibilityChecked(item.checked)
                    subgroup.setIsMutuallyExclusive(
                        item.mutually_exclusive, item.mutually_exclusive_child
                    )
            else:
                layer = item.layer
                if (
                    not layer.dataProvider()
                    or layer.dataProvider().dataSourceUri()
                    not in existing_layer_source_uris
                ):
                    if self.static_sorting:
                        index = static_index
                    elif layer.isSpatial():
                        index = get_suggested_index_for_layer(
                            layer, group, self.ignore_node_names
                        )
                    else:
                        index = 0
                    layernode = QgsLayerTreeLayer(layer)
                    layernode.setExpanded(item.expanded)
                    layernode.setItemVisibilityChecked(item.checked)
                    layernode.setCustomProperty("showFeatureCount", item.featurecount)
                    group.insertChildNode(index, layernode)
            static_index += 1

    def is_empty(self) -> bool:
        return not bool(self.items)
