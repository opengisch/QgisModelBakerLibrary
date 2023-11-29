"""
/***************************************************************************
    begin                :    05/03/18
    git sha              :    :%H$
    copyright            :    (C) 2018 by Germán Carrillo (BSF-Swissphoto)
    email                :    gcarrillo@linuxmail.org
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

from qgis.core import (
    Qgis,
    QgsAttributeEditorContainer,
    QgsAttributeEditorField,
    QgsDefaultValue,
    QgsExpressionContextUtils,
    QgsLayerTreeLayer,
    QgsLayerTreeNode,
    QgsMapLayer,
    QgsProject,
    QgsWkbTypes,
)

layer_order = [
    "point",  # QgsWkbTypes.PointGeometry
    "line",  # QgsWkbTypes.LineGeometry
    "polygon",  # QgsWkbTypes.PolygonGeometry
    "raster",  # QgsMapLayer.RasterLayer
    "table",  # QgsWkbTypes.NullGeometry
    "unknown",
]  # Anything else like geometry collections or plugin layers


def get_first_index_for_layer_type(layer_type, group, ignore_node_names=None):
    """
    Finds the first index (from top to bottom) in the layer tree where a
    specific layer type is found. This function works only for the given group.
    """
    if ignore_node_names is None:
        ignore_node_names = []

    tree_nodes = group.children()

    for current, tree_node in enumerate(tree_nodes):
        if tree_node.name() in ignore_node_names:
            # Some groups (e.g., validation errors) might be useful on a
            # specific position (e.g., at the top), so, skip it to get indices
            continue
        if (
            tree_node.nodeType() == QgsLayerTreeNode.NodeGroup
            and layer_type != "unknown"
        ):
            return None
        elif (
            tree_node.nodeType() == QgsLayerTreeNode.NodeGroup
            and layer_type == "unknown"
        ):
            # We've reached the lowest index in the layer tree before a group
            return current

        # Make this check because children() sometimes returns nodes of type QgsLayerTreeNode instead.
        # This is a workaround for a weird behavior of QGIS.
        if isinstance(tree_node, QgsLayerTreeLayer):
            layer = tree_node.layer()
            if get_layer_type(layer) == layer_type:
                return current

    return None


def get_suggested_index_for_layer(layer, group, ignore_node_names=None):
    """
    Returns the index where a layer can be inserted, taking other layer types
    into account. For instance, if a line layer is given, this function will
    return the index of the first line layer in the layer tree (if above it
    there are no lower-ordered layers like tables, otherwise this returns that
    table index), and if there are no line layers in it, it will continue with
    the first index of polygons , rasters, tables, or groups. Always following
    the order given in the global layer_order variable.
    """
    indices = []
    index = None
    for layer_type in layer_order[
        layer_order.index(get_layer_type(layer)) :
    ]:  # Slice from current until last
        index = get_first_index_for_layer_type(layer_type, group, ignore_node_names)
        if index is not None:
            indices.append(index)

    if indices:
        index = min(indices)
    if index is None:
        return -1  # Send it to the last position in layer tree
    else:
        return index


def get_layer_type(layer):
    """
    To deal with all layer types, map their types to known values
    """
    if layer.type() == QgsMapLayer.VectorLayer:
        if layer.isSpatial():
            if layer.geometryType() == QgsWkbTypes.UnknownGeometry:
                return "unknown"
            else:
                return layer_order[layer.geometryType()]  # Point, Line or Polygon
        else:
            return "table"
    elif layer.type() == QgsMapLayer.RasterLayer:
        return "raster"
    else:
        return "unknown"


def get_group_non_recursive(group, group_name):
    groups = (
        group.findGroups(False)
        if Qgis.QGIS_VERSION_INT >= 31800
        else group.findGroups()
    )
    for group in groups:
        if group.name() == group_name:
            return group

    return None


class QgisProjectUtils:
    def __init__(self, project: QgsProject = None):
        self.project = project

    def get_oid_settings(self):
        """Returns a dictionary like:
        {
            "Strasse":
            {
                "oid_domain": "STANDARDOID",
                "interlis_topic" : "OIDMadness_V1",
                "default_value_expression": "uuid()",
                "in_form": True
                "layer": QgsVectorLayer
            }
        }
        """

        oid_settings = {}

        root = self.project.layerTreeRoot()

        tree_layers = root.findLayers()
        for tree_layer in tree_layers:
            # get t_ili_tid field OID field
            if tree_layer.layer().type() != QgsMapLayer.VectorLayer:
                continue
            fields = tree_layer.layer().fields()
            field_idx = fields.lookupField("t_ili_tid")
            if field_idx < 0:
                continue

            t_ili_tid_field = fields.field(field_idx)

            oid_setting = {}

            # get oid type and all possible topics (for information) (comma sparated)
            oid_setting["oid_domain"] = (
                QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                    "oid_domain"
                )
                or ""
            )
            oid_setting["interlis_topic"] = (
                QgsExpressionContextUtils.layerScope(tree_layer.layer()).variable(
                    "interlis_topic"
                )
                or ""
            )

            # QgsVectorLayer (for information)
            oid_setting["layer"] = tree_layer.layer()

            # get the default value expression
            oid_setting["default_value_expression"] = (
                t_ili_tid_field.defaultValueDefinition().expression() or ""
            )

            # check if t_ili_tid is exposed in form
            efc = tree_layer.layer().editFormConfig()
            root_container = efc.invisibleRootContainer()
            oid_setting["in_form"] = bool(
                self._found_tilitid(root_container) is not None
            )
            oid_settings[tree_layer.layer().name()] = oid_setting

        return oid_settings

    def set_oid_settings(self, oid_settings):
        for layer_name in oid_settings.keys():
            layers = self.project.mapLayersByName(layer_name)
            if layers:
                layer = layers[0]
                oid_setting = oid_settings[layer_name]

                fields = layer.fields()
                field_idx = fields.lookupField("t_ili_tid")
                t_ili_tid_field = fields.field(field_idx)

                # set the default value expression
                default_value = QgsDefaultValue(oid_setting["default_value_expression"])
                layer.setDefaultValueDefinition(field_idx, default_value)

                # we have to check if the field is already exposed in the form
                efc = layer.editFormConfig()
                root_container = efc.invisibleRootContainer()
                found_container = self._found_tilitid(root_container)
                tilitid_in_form = bool(found_container is not None)

                if (not tilitid_in_form) and oid_setting["in_form"]:
                    # needs to be added
                    if root_container.children() and isinstance(
                        root_container.children()[0], QgsAttributeEditorContainer
                    ):
                        # add it to the first tab
                        container = root_container.children()[0]
                    else:
                        # add it to top level (rootContainer)
                        container = root_container
                    widget = QgsAttributeEditorField(
                        t_ili_tid_field.name(), field_idx, container
                    )
                    container.addChildElement(widget)

                if tilitid_in_form and not oid_setting["in_form"]:
                    # needs to be removed
                    preserved_container = found_container.clone(
                        found_container.parent()
                    )
                    found_container.clear()

                    for child in preserved_container.children():
                        if child.name().lower() == "t_ili_tid":
                            continue
                        found_container.addChildElement(child.clone(found_container))

    def _found_tilitid(self, container):
        """Recursive function to dig into the form containers for the t_ili_tid returning true on success."""
        for element in container.children():
            if isinstance(element, QgsAttributeEditorContainer):
                found_here = self._found_tilitid(element)
                if found_here is not None:
                    return found_here
            elif (
                isinstance(element, QgsAttributeEditorField)
                and element.name().lower() == "t_ili_tid"
            ):
                return container
        return None
