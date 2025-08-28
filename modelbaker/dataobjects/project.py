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

from typing import Any, Optional

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

from ..utils.globals import LogLevel, OptimizeStrategy, default_log_function
from .layers import Layer
from .legend import LegendGroup
from .relations import Relation

ENUM_THIS_CLASS_COLUMN = "thisclass"


class Project(QObject):
    layer_added = pyqtSignal(str)

    def __init__(
        self,
        auto_transaction: str = "True",  # TODO: Change default value when dropping QGIS <3.26 support
        evaluate_default_values: bool = True,
        context: dict[str, str] = {},
        optimize_strategy: OptimizeStrategy = OptimizeStrategy.NONE,
        log_function=None,
    ) -> None:
        QObject.__init__(self)
        self.crs = None
        self.name = "Not set"
        self.layers = list[Layer]
        self.legend = LegendGroup()
        self.custom_layer_order_structure = list()
        self.auto_transaction = auto_transaction
        self.evaluate_default_values = evaluate_default_values
        self.relations = list[Relation]
        self.custom_variables = {}
        self.layouts = {}
        self.mapthemes = {}
        self.context = context
        self.optimize_strategy = optimize_strategy
        self.log_function = log_function

        if not log_function:
            self.log_function = default_log_function

        # {Layer_class_name: {dbattribute: {Layer_class, cardinality, Layer_domain, key_field, value_field]}
        self.bags_of_enum = dict()

    def add_layer(self, layer: Layer) -> None:
        self.layers.append(layer)

    def dump(self) -> dict[str, Any]:
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

    def load(self, definition: dict[str, Any]) -> None:
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
        self,
        path: str,
        qgis_project: QgsProject,
        group: Optional[QgsLayerTreeGroup] = None,
    ) -> None:
        if Qgis.QGIS_VERSION_INT < 32600:
            # set auto_transaction as boolean
            qgis_project.setAutoTransaction(self.auto_transaction == "True")
        else:
            # set auto_transaction mode
            mode = Qgis.TransactionMode.Disabled
            if (
                self.auto_transaction == Qgis.TransactionMode.AutomaticGroups.name
                or self.auto_transaction == "True"  # Legacy
            ):
                mode = Qgis.TransactionMode.AutomaticGroups
            elif self.auto_transaction == Qgis.TransactionMode.BufferedGroups.name:
                mode = Qgis.TransactionMode.BufferedGroups
            qgis_project.setTransactionMode(mode)

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
            if not rel.isValid():
                self.log_function(
                    f"The relation from {relation.referencing_layer.name} ({relation.referencing_layer.create().name()}) to {relation.referenced_layer.name} ({relation.referenced_layer.create().name()}) is not valid. The project may be corrupt.",
                    LogLevel.FAIL,
                )
                continue

            referenced_layer = dict_layers.get(rel.referencedLayerId(), None)
            referencing_layer = dict_layers.get(rel.referencingLayerId(), None)

            # on enumeration tables we use value relation, because it's less resource intensive - still when it has a display expression (defined by meta attribute or because it's a translated model, we still use relation reference)
            if (
                referenced_layer
                and referenced_layer.is_enum
                and not referenced_layer.display_expression
            ):
                editor_widget_setup = QgsEditorWidgetSetup(
                    "ValueRelation",
                    {
                        "AllowMulti": False,
                        "UseCompleter": False,
                        "Value": referenced_layer.provider_names_map.get(
                            "dispname_name"
                        ),
                        "OrderByValue": False
                        if Qgis.QGIS_VERSION_INT >= 34200
                        else True,  # order by value if order by field is not available yet
                        "AllowNull": True,
                        "Layer": rel.referencedLayerId(),
                        "FilterExpression": "\"{}\" = '{}'".format(
                            ENUM_THIS_CLASS_COLUMN, relation.child_domain_name
                        )
                        if relation.child_domain_name
                        else "",
                        "Key": referenced_layer.provider_names_map.get("tid_name"),
                        "NofColumns": 1,
                        "OrderByField": True,
                        "OrderByFieldName": "seq",
                    },
                )
            elif referenced_layer and referenced_layer.is_domain:
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

                qgis_relations.append(rel)
            elif referenced_layer and referenced_layer.is_basket_table:
                # list the topics we filter the basket with. On NONE strategy those should be all topics the class could be in. On optimized strategies GROUP/HIDE only the relevant topics should be listed.
                filter_topics = (
                    referencing_layer.all_topics
                    if self.optimize_strategy == OptimizeStrategy.NONE
                    else referencing_layer.relevant_topics
                )
                editor_widget_setup = QgsEditorWidgetSetup(
                    "RelationReference",
                    {
                        "Relation": rel.id(),
                        "ShowForm": False,
                        "OrderByValue": True,
                        "ShowOpenFormButton": False,
                        "AllowNULL": True,
                        "AllowAddFeatures": False,
                        "FilterExpression": "\"topic\" IN ({}) and attribute(get_feature('{}', '{}', \"dataset\"), 'datasetname') != '{}'".format(
                            ",".join(
                                [f"'{topic}'" for topic in sorted(filter_topics)]
                            ),  # create comma separated string
                            referenced_layer.provider_names_map.get(
                                "datasettable_name"
                            ),
                            referenced_layer.provider_names_map.get("tid_name"),
                            self.context.get("catalogue_datasetname", ""),
                        )
                        if filter_topics
                        else "",  # no filter if no topics (means could be everywhere)
                        "FilterFields": list(),
                    },
                )
                qgis_relations.append(rel)
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
                qgis_relations.append(rel)

            referencing_layer = rel.referencingLayer()
            referencing_layer.setEditorWidgetSetup(
                rel.referencingFields()[0], editor_widget_setup
            )
        qgis_project.relationManager().setRelations(qgis_relations)

        # Set Bag of Enum widget
        for layer_name, bag_of_enum in self.bags_of_enum.items():
            current_layer = None
            for attribute, bag_of_enum_info in bag_of_enum.items():
                layer_obj = bag_of_enum_info[0]
                cardinality = bag_of_enum_info[1]
                domain_table = bag_of_enum_info[2]
                key_field = bag_of_enum_info[3]
                value_field = bag_of_enum_info[4]

                minimal_selection = cardinality.startswith("1")

                if not current_layer:
                    # create the layer only once
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
            if layer.layer.type() == QgsMapLayer.LayerType.VectorLayer:
                # even when a style will be loaded we create the form because not sure if the style contains form settngs
                layer.create_form(self)
                layer.store_variables(self)
            layer.load_styles()

        if self.legend:
            self.legend.create(qgis_project, group)

        self.load_custom_layer_order(qgis_project)

        self.load_mapthemes(qgis_project)

        self.load_custom_variables(qgis_project)

        self.load_layouts(qgis_project)

        self.store_project_variables(qgis_project)

        if path:
            qgis_project.write(path)

    def load_custom_layer_order(self, qgis_project: QgsProject) -> None:
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

    def load_custom_variables(self, qgis_project: QgsProject) -> None:
        for key in self.custom_variables.keys():
            QgsExpressionContextUtils.setProjectVariable(
                qgis_project, key, self.custom_variables[key]
            )

    def load_layouts(self, qgis_project: QgsProject) -> None:
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

    def load_mapthemes(self, qgis_project: QgsProject) -> None:
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

    def store_project_variables(self, qgis_project: QgsProject) -> None:
        QgsExpressionContextUtils.setProjectVariable(
            qgis_project, "optimize_strategy", self.optimize_strategy.name
        )

    def post_generate(self) -> None:
        for layer in self.layers:
            layer.post_generate(self)
