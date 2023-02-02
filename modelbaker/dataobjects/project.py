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
from typing import List

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsEditorWidgetSetup,
    QgsExpressionContextUtils,
    QgsLayerTreeGroup,
    QgsMapLayer,
    QgsMapThemeCollection,
    QgsPrintLayout,
    QgsProject,
    QgsReadWriteContext,
)
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.PyQt.QtXml import QDomDocument

from .layers import Layer
from .legend import LegendGroup
from .relations import Relation

ENUM_THIS_CLASS_COLUMN = "thisclass"


class Project(QObject):
    layer_added = pyqtSignal(str)

    def __init__(self, auto_transaction=True, evaluate_default_values=True, context={}):
        QObject.__init__(self)
        self.crs = None
        self.name = "Not set"
        self.layers = List[Layer]
        self.legend = LegendGroup()
        self.custom_layer_order_structure = list()
        self.auto_transaction = auto_transaction
        self.evaluate_default_values = evaluate_default_values
        self.relations = List[Relation]
        self.custom_variables = {}
        self.layouts = {}
        self.mapthemes = {}
        self.context = context

        # {Layer_class_name: {dbattribute: {Layer_class, cardinality, Layer_domain, key_field, value_field]}
        self.bags_of_enum = dict()

    def add_layer(self, layer):
        self.layers.append(layer)

    def dump(self):
        definition = dict()
        definition["crs"] = self.crs.toWkt()
        definition["auto_transaction"] = self.auto_transaction
        definition["evaluate_default_values"] = self.evaluate_default_values

        legend = list()
        for layer in self.layers:
            legend.append(layer.dump())

        definition["custom_layer_order_structure"] = self.custom_layer_order_structure
        relations = list()

        for relation in self.relations:
            relations.append(relation.dump())

        definition["legend"] = legend
        definition["relations"] = relations
        definition["custom_variables"] = self.custom_variables
        definition["layouts"] = self.layouts
        definition["mapthemes"] = self.mapthemes

        return definition

    def load(self, definition):
        self.crs = definition["crs"]
        self.auto_transaction = definition["auto_transaction"]
        self.evaluate_default_values = definition["evaluate_default_values"]

        self.layers = list()
        for layer_definition in definition["layers"]:
            layer = Layer()
            layer.load(layer_definition)
            self.layers.append(layer)

        self.custom_layer_order_structure = definition["custom_layer_order_structure"]
        self.custom_variables = definition["custom_variables"]
        self.layouts = definition["layouts"]
        self.mapthemes = definition["mapthemes"]

    def create(
        self, path: str, qgis_project: QgsProject, group: QgsLayerTreeGroup = None
    ):
        qgis_project.setAutoTransaction(self.auto_transaction)
        qgis_project.setEvaluateDefaultValues(self.evaluate_default_values)
        qgis_layers = list()
        for layer in self.layers:
            qgis_layer = layer.create()
            self.layer_added.emit(qgis_layer.id())
            if not self.crs and qgis_layer.isSpatial():
                self.crs = qgis_layer.crs()

            qgis_layers.append(qgis_layer)

        qgis_project.addMapLayers(qgis_layers, not self.legend)

        if self.crs:
            if isinstance(self.crs, QgsCoordinateReferenceSystem):
                qgis_project.setCrs(self.crs)
            else:
                crs = QgsCoordinateReferenceSystem.fromEpsgId(self.crs)
                if not crs.isValid():
                    crs = QgsCoordinateReferenceSystem(self.crs)  # Fallback
                qgis_project.setCrs(crs)

        qgis_relations = list(qgis_project.relationManager().relations().values())
        dict_layers = {layer.layer.id(): layer for layer in self.layers}
        for relation in self.relations:
            rel = relation.create(qgis_project, qgis_relations)
            assert rel.isValid()
            qgis_relations.append(rel)

            referenced_layer = dict_layers.get(rel.referencedLayerId(), None)
            referencing_layer = dict_layers.get(rel.referencingLayerId(), None)

            if referenced_layer and referenced_layer.is_domain:
                editor_widget_setup = QgsEditorWidgetSetup(
                    "RelationReference",
                    {
                        "Relation": rel.id(),
                        "ShowForm": False,
                        "OrderByValue": True,
                        "ShowOpenFormButton": False,
                        "AllowNULL": True,
                        "FilterExpression": "\"{}\" = '{}'".format(
                            ENUM_THIS_CLASS_COLUMN, relation.child_domain_name
                        )
                        if relation.child_domain_name
                        else "",
                        "FilterFields": list(),
                    },
                )
            elif referenced_layer and referenced_layer.is_basket_table:
                editor_widget_setup = QgsEditorWidgetSetup(
                    "RelationReference",
                    {
                        "Relation": rel.id(),
                        "ShowForm": False,
                        "OrderByValue": True,
                        "ShowOpenFormButton": False,
                        "AllowNULL": True,
                        "AllowAddFeatures": False,
                        "FilterExpression": "\"topic\" = '{}' and attribute(get_feature('{}', 't_id', \"dataset\"), 'datasetname') != '{}'".format(
                            referencing_layer.model_topic_name,
                            "T_ILI2DB_DATASET"
                            if referenced_layer.provider == "ogr"
                            else "t_ili2db_dataset",
                            self.context.get("catalogue_datasetname", ""),
                        )
                        if referencing_layer.model_topic_name
                        else "",
                        "FilterFields": list(),
                    },
                )
            else:
                editor_widget_setup = QgsEditorWidgetSetup(
                    "RelationReference",
                    {
                        "Relation": rel.id(),
                        "ShowForm": False,
                        "OrderByValue": True,
                        "ShowOpenFormButton": False,
                        "AllowAddFeatures": True,
                        "AllowNULL": True,
                    },
                )

            referencing_layer = rel.referencingLayer()
            referencing_layer.setEditorWidgetSetup(
                rel.referencingFields()[0], editor_widget_setup
            )

        qgis_project.relationManager().setRelations(qgis_relations)

        # Set Bag of Enum widget
        for layer_name, bag_of_enum in self.bags_of_enum.items():
            for attribute, bag_of_enum_info in bag_of_enum.items():
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]

                minimal_selection = cardinality.startswith("1")

                current_layer = layer_obj.create()

                field_widget = "ValueRelation"
                field_widget_config = {
                    "AllowMulti": True,
                    "UseCompleter": False,
                    "Value": value_field,
                    "OrderByValue": False,
                    "AllowNull": True,
                    "Layer": domain_table.create().id(),
                    "FilterExpression": "",
                    "Key": key_field,
                    "NofColumns": 1,
                }
                field_idx = current_layer.fields().indexOf(attribute)
                setup = QgsEditorWidgetSetup(field_widget, field_widget_config)
                current_layer.setEditorWidgetSetup(field_idx, setup)
                if minimal_selection:
                    constraint_expression = 'array_length("{}")>0'.format(attribute)
                    current_layer.setConstraintExpression(
                        field_idx,
                        constraint_expression,
                        self.tr("The minimal selection is 1"),
                    )

        for layer in self.layers:
            if layer.layer.type() == QgsMapLayer.VectorLayer:
                # even when a style will be loaded we create the form because not sure if the style contains form settngs
                layer.create_form(self)
                layer.load_styles()

        if self.legend:
            self.legend.create(qgis_project, group)

        self.load_custom_layer_order(qgis_project)

        self.load_mapthemes(qgis_project)

        self.load_custom_variables(qgis_project)

        self.load_layouts(qgis_project)

        if path:
            qgis_project.write(path)

    def load_custom_layer_order(self, qgis_project):
        custom_layer_order = list()
        for custom_layer_name in self.custom_layer_order_structure:
            custom_layer = qgis_project.mapLayersByName(custom_layer_name)
            if custom_layer:
                custom_layer_order.append(custom_layer[0])
        if custom_layer_order:
            root = qgis_project.layerTreeRoot()
            order = root.customLayerOrder() if root.hasCustomLayerOrder() else []
            order.extend(custom_layer_order)
            root.setCustomLayerOrder(custom_layer_order)
            root.setHasCustomLayerOrder(True)

    def load_custom_variables(self, qgis_project):
        for key in self.custom_variables.keys():
            QgsExpressionContextUtils.setProjectVariable(
                qgis_project, key, self.custom_variables[key]
            )

    def load_layouts(self, qgis_project):
        for layout_name in self.layouts.keys():
            # create the layout
            layout = QgsPrintLayout(qgis_project)
            # initializes default settings for blank print layout canvas
            layout.initializeDefaults()
            # load template from file
            templatefile = self.layouts[layout_name]["templatefile"]
            with open(templatefile) as f:
                template_file_content = f.read()
                doc = QDomDocument()
                doc.setContent(template_file_content)
                layout.loadFromTemplate(doc, QgsReadWriteContext())
                # name it according the settings
                layout.setName(layout_name)
                qgis_project.layoutManager().addLayout(layout)

    def load_mapthemes(self, qgis_project):
        if self.mapthemes:
            for name in self.mapthemes.keys():
                map_theme_record = QgsMapThemeCollection.MapThemeRecord()

                nodes = self.mapthemes[name]
                for node_name in nodes.keys():
                    node_properties = nodes[node_name]
                    if node_properties.get("group"):
                        # it's a group node
                        if node_properties.get("expanded"):
                            map_theme_record.setHasExpandedStateInfo(True)
                            expanded_group_nodes = map_theme_record.expandedGroupNodes()
                            expanded_group_nodes.add(node_name)
                            map_theme_record.setExpandedGroupNodes(expanded_group_nodes)
                        if node_properties.get("checked"):
                            if Qgis.QGIS_VERSION_INT >= 33000:
                                map_theme_record.setHasCheckedStateInfo(True)
                            checked_group_nodes = map_theme_record.checkedGroupNodes()
                            checked_group_nodes.add(node_name)
                            map_theme_record.setCheckedGroupNodes(checked_group_nodes)
                    else:
                        # it's not group node
                        if (
                            qgis_project.mapLayersByName(node_name)
                            and qgis_project.mapLayersByName(node_name)[0]
                        ):
                            map_theme_layer_record = (
                                QgsMapThemeCollection.MapThemeLayerRecord()
                            )
                            map_theme_layer_record.setLayer(
                                qgis_project.mapLayersByName(node_name)[0]
                            )
                            if node_properties.get("style"):
                                map_theme_layer_record.usingCurrentStyle = True
                                map_theme_layer_record.currentStyle = (
                                    node_properties.get("style")
                                )
                            # isVisible decides if at least one of the categories is visible (don't mix up with checked)
                            map_theme_layer_record.isVisible = node_properties.get(
                                "visible", False
                            )
                            map_theme_layer_record.expandedLayerNode = (
                                node_properties.get("expanded", False)
                            )
                            if node_properties.get("expanded_items"):
                                map_theme_layer_record.expandedLegendItems = set(
                                    node_properties.get("expanded_items", [])
                                )
                            if node_properties.get("checked_items"):
                                # if the value "checked_items" is there, we need to consider it, even if it's empty.
                                map_theme_layer_record.usingLegendItems = True
                                map_theme_layer_record.checkedLegendItems = set(
                                    node_properties.get("checked_items", [])
                                )
                            else:
                                # if the value "checked_items" is not there, we don't considere it. This means all entries are checked.
                                map_theme_layer_record.usingLegendItems = False

                            map_theme_record.addLayerRecord(map_theme_layer_record)

                qgis_project.mapThemeCollection().insert(name, map_theme_record)

    def post_generate(self):
        for layer in self.layers:
            layer.post_generate(self)
