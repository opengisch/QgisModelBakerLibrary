"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
                              (C) 2016 by OPENGIS.ch
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
import re

from qgis.core import QgsApplication, QgsRelation, QgsWkbTypes
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QObject, pyqtSignal

from ..dataobjects.fields import Field
from ..dataobjects.layers import Layer
from ..dataobjects.legend import LegendGroup
from ..dataobjects.relations import Relation
from ..db_factory.db_simple_factory import DbSimpleFactory
from ..utils.globals import OptimizeStrategy
from ..utils.qt_utils import slugify
from .config import BASKET_FIELDNAMES, IGNORED_FIELDNAMES, READONLY_FIELDNAMES
from .domain_relations_generator import DomainRelationGenerator


class Generator(QObject):
    """Builds Model Baker objects from data extracted from databases."""

    stdout = pyqtSignal(str)
    new_message = pyqtSignal(int, str)

    def __init__(
        self,
        tool,
        uri,
        inheritance,
        schema=None,
        pg_estimated_metadata=False,
        parent=None,
        mgmt_uri=None,
        consider_basket_handling=False,
        optimize_strategy=OptimizeStrategy.NONE,
    ):
        """
        Creates a new Generator objects.
        :param uri: The uri that should be used in the resulting project. If authcfg is used, make sure the mgmt_uri is set as well.
        :param mgmt_uri: The uri that should be used to create schemas, tables and query meta information. Does not support authcfg.
        :consider_basket_handling: Makes the specific handling of basket tables depending if schema is created with createBasketCol.
        """
        QObject.__init__(self, parent)
        self.tool = tool
        self.uri = uri
        self.mgmt_uri = mgmt_uri
        self.inheritance = inheritance
        self.schema = schema or None
        self.pg_estimated_metadata = pg_estimated_metadata

        self.db_simple_factory = DbSimpleFactory()
        db_factory = self.db_simple_factory.create_factory(self.tool)
        self._db_connector = db_factory.get_db_connector(mgmt_uri or uri, schema)
        self._db_connector.stdout.connect(self.print_info)
        self._db_connector.new_message.connect(self.append_print_message)
        self.basket_handling = consider_basket_handling and self.get_basket_handling()
        self.optimize_strategy = optimize_strategy

        self._additional_ignored_layers = (
            []
        )  # List of layers to ignore set by 3rd parties

        self.collected_print_messages = []

    def print_info(self, text):
        self.stdout.emit(text)

    def print_messages(self):
        for message in self.collected_print_messages:
            self.new_message.emit(message["level"], message["text"])
        self.collected_print_messages.clear()

    def append_print_message(self, level, text):
        message = {"level": level, "text": text}

        if message not in self.collected_print_messages:
            self.collected_print_messages.append(message)

    def layers(self, filter_layer_list=[]):
        ignore_basket_tables = not self.basket_handling
        tables_info = self.get_tables_info_without_ignored_tables(ignore_basket_tables)
        layers = list()

        db_factory = self.db_simple_factory.create_factory(self.tool)

        layer_uri = db_factory.get_layer_uri(self.uri)
        layer_uri.pg_estimated_metadata = self.pg_estimated_metadata

        # When a table has multiple geometry columns, it will be loaded multiple times (supported e.g. by PostGIS).
        table_appearance_count = {}

        for record in tables_info:
            if self.schema:
                if record["schemaname"] != self.schema:
                    continue
            if filter_layer_list and record["tablename"] not in filter_layer_list:
                continue
            table_appearance_count[record["tablename"]] = (
                table_appearance_count.get(record["tablename"], 0) + 1
            )

        for record in tables_info:
            # When in PostGIS mode, leaving schema blank should load tables from
            # all schemas, except the ignored ones
            if self.schema:
                if record["schemaname"] != self.schema:
                    continue

            if filter_layer_list and record["tablename"] not in filter_layer_list:
                continue

            is_domain = (
                record.get("kind_settings") == "ENUM"
                or record.get("kind_settings") == "CATALOGUE"
            )
            is_attribute = bool(record.get("attribute_name"))
            is_structure = record.get("kind_settings") == "STRUCTURE"
            is_nmrel = record.get("kind_settings") == "ASSOCIATION"
            # only when the basked_handling is active we will consider the table as basket table (according to it's name)
            is_basket_table = self.basket_handling and (
                record.get("tablename") == self._db_connector.basket_table_name
            )
            is_dataset_table = self.basket_handling and (
                record.get("tablename") == self._db_connector.dataset_table_name
            )

            is_relevant = bool(
                record.get("relevance", True)
            )  # it can be not relevant and still be displayed (in case of NONE)

            base_topic = record["base_topic"] if "base_topic" in record else None

            # get all the topics
            all_topics = (
                record.get("all_topics").split(",") if record.get("all_topics") else []
            )
            # don't concern no-topics (e.g. when a domain is designed directly in the model)
            all_topics = [topic for topic in all_topics if topic.count(".") > 0]

            # and include the topic where the class is designed in
            if base_topic and base_topic.count(".") > 0:
                all_topics.append(base_topic)

            # get all the relevant topics
            relevant_topics = (
                record.get("relevant_topics").split(",")
                if record.get("relevant_topics")
                else []
            )

            # don't concern no-topics (e.g. when a domain is designed directly in the model)
            relevant_topics = [
                topic for topic in relevant_topics if topic.count(".") > 0
            ]

            # if no relevant_topic found the relevant is the one where the class is designed in
            if not relevant_topics and base_topic and base_topic.count(".") > 0:
                relevant_topics.append(base_topic)

            alias = record["table_alias"] if "table_alias" in record else None
            if not alias:
                short_name = None
                if is_domain and is_attribute:
                    short_name = ""
                    if "ili_name" in record and record["ili_name"]:
                        short_name = (
                            record["ili_name"].split(".")[-2]
                            + "_"
                            + record["ili_name"].split(".")[-1]
                        )
                else:
                    if (
                        table_appearance_count[record["tablename"]] > 1
                        and "geometry_column" in record
                    ):
                        # table loaded multiple times (because of multiple geometry columns) - append geometry column to name (for PG source layers)
                        fields_info = self.get_fields_info(record["tablename"])
                        for field_info in fields_info:
                            if field_info["column_name"] == record["geometry_column"]:
                                if (
                                    "fully_qualified_name" in field_info
                                    and field_info["fully_qualified_name"]
                                ):
                                    short_name = (
                                        field_info["fully_qualified_name"].split(".")[
                                            -2
                                        ]
                                        + " ("
                                        + field_info["fully_qualified_name"].split(".")[
                                            -1
                                        ]
                                        + ")"
                                    )
                                else:
                                    short_name = record["tablename"]
                    elif "ili_name" in record and record["ili_name"]:
                        match = re.search(r"([^\(]*).*", record["ili_name"])
                        if match.group(0) == match.group(1):
                            short_name = match.group(1).split(".")[-1]
                        else:
                            # table does not fit in match group (on multigeometry in geopackage they are named with "...OriginalName.GeometryColumn (OriginalName)" so we want the GeometryColumn appended in brackets
                            short_name = (
                                match.group(1).split(".")[-2]
                                + " ("
                                + match.group(1).split(".")[-1]
                                + ")"
                            )
                alias = short_name

            display_expression = ""
            if is_basket_table:
                display_expression = "coalesce(attribute(get_feature('{dataset_layer_name}', '{tid}', dataset), 'datasetname') || ' (' || topic || ') ', coalesce( attribute(get_feature('{dataset_layer_name}', '{tid}', dataset), 'datasetname'), {tilitid}))".format(
                    tid=self._db_connector.tid,
                    tilitid=self._db_connector.tilitid,
                    dataset_layer_name=self._db_connector.dataset_table_name,
                )
            elif "ili_name" in record and record["ili_name"]:
                meta_attrs = self.get_meta_attrs(record["ili_name"])
                for attr_record in meta_attrs:
                    if attr_record["attr_name"] in [
                        "dispExpression",
                        "qgis.modelbaker.dispExpression",
                    ]:
                        display_expression = attr_record["attr_value"]

            coord_decimals = (
                record["coord_decimals"] if "coord_decimals" in record else None
            )
            coordinate_precision = None
            if coord_decimals:
                coordinate_precision = 1 / (10**coord_decimals)

            layer = Layer(
                layer_uri.provider,
                layer_uri.get_data_source_uri(record),
                record.get("tablename"),
                record.get("srid"),
                record.get("extent"),
                record.get("geometry_column"),
                QgsWkbTypes.parseType(record["type"]) or QgsWkbTypes.Unknown,
                alias,
                is_domain,
                is_structure,
                is_nmrel,
                display_expression,
                coordinate_precision,
                is_basket_table,
                is_dataset_table,
                record.get("ili_name"),
                is_relevant,
                all_topics,
                relevant_topics,
            )

            # Configure fields for current table
            fields_info = self.get_fields_info(record["tablename"])
            min_max_info = self.get_min_max_info(record["tablename"])
            value_map_info = self.get_value_map_info(record["tablename"])
            re_iliname = re.compile(r".*\.(.*)$")

            for fielddef in fields_info:
                column_name = fielddef["column_name"]
                fully_qualified_name = (
                    fielddef["fully_qualified_name"]
                    if "fully_qualified_name" in fielddef
                    else None
                )
                m = (
                    re_iliname.match(fully_qualified_name)
                    if fully_qualified_name
                    else None
                )

                alias = None
                if "column_alias" in fielddef:
                    alias = fielddef["column_alias"]
                if m and not alias:
                    alias = m.group(1)

                field = Field(column_name)
                field.alias = alias

                # Should we hide the field?
                hide_attribute = False

                if "fully_qualified_name" in fielddef:
                    fully_qualified_name = fielddef["fully_qualified_name"]
                    if fully_qualified_name:
                        meta_attrs_column = self.get_meta_attrs(fully_qualified_name)

                        for attr_record in meta_attrs_column:
                            if attr_record["attr_name"] == "hidden":
                                if attr_record["attr_value"] == "True":
                                    hide_attribute = True
                                    break

                if column_name in IGNORED_FIELDNAMES:
                    hide_attribute = True

                if not self.basket_handling and column_name in BASKET_FIELDNAMES:
                    hide_attribute = True

                field.hidden = hide_attribute

                if column_name in READONLY_FIELDNAMES:
                    field.read_only = True

                if column_name in min_max_info:
                    field.widget = "Range"
                    field.widget_config["Min"] = min_max_info[column_name][0]
                    field.widget_config["Max"] = min_max_info[column_name][1]
                    if "numeric_scale" in fielddef:
                        field.widget_config["Step"] = pow(
                            10, -1 * fielddef["numeric_scale"]
                        )
                    # field.widget_config['Suffix'] = fielddef['unit'] if 'unit' in fielddef else ''
                    if "unit" in fielddef and fielddef["unit"] is not None:
                        field.alias = "{alias} [{unit}]".format(
                            alias=alias or column_name, unit=fielddef["unit"]
                        )

                if column_name in value_map_info:
                    field.widget = "ValueMap"
                    field.widget_config["map"] = [
                        {val: val} for val in value_map_info[column_name]
                    ]

                if "attr_mapping" in fielddef and fielddef["attr_mapping"] == "ARRAY":
                    field.widget = "List"

                if "texttype" in fielddef and fielddef["texttype"] == "MTEXT":
                    field.widget = "TextEdit"
                    field.widget_config["IsMultiline"] = True

                data_type = self._db_connector.map_data_types(fielddef["data_type"])
                if "time" in data_type or "date" in data_type:
                    field.widget = "DateTime"
                    field.widget_config["calendar_popup"] = True

                    dateFormat = QLocale(QgsApplication.instance().locale()).dateFormat(
                        QLocale.ShortFormat
                    )
                    timeFormat = QLocale(QgsApplication.instance().locale()).timeFormat(
                        QLocale.ShortFormat
                    )
                    dateTimeFormat = QLocale(
                        QgsApplication.instance().locale()
                    ).dateTimeFormat(QLocale.ShortFormat)

                    if data_type == self._db_connector.QGIS_TIME_TYPE:
                        field.widget_config["display_format"] = timeFormat
                    elif data_type == self._db_connector.QGIS_DATE_TIME_TYPE:
                        field.widget_config["display_format"] = dateTimeFormat
                    elif data_type == self._db_connector.QGIS_DATE_TYPE:
                        field.widget_config["display_format"] = dateFormat

                db_factory.customize_widget_editor(field, data_type)

                if "enum_domain" in fielddef and fielddef["enum_domain"]:
                    field.enum_domain = fielddef["enum_domain"]

                # default value expressions

                ## we have this to provide e.g. the T_Id expression for GPKG defined in the db_connector
                if "default_value_expression" in fielddef:
                    field.default_value_expression = fielddef[
                        "default_value_expression"
                    ]

                ## oid (t_ili_tid)
                # trying to set reasonable default default-expressions:
                if column_name == self._db_connector.tilitid:
                    field.oid_domain = fielddef.get("oid_domain", None)
                    if field.oid_domain == "INTERLIS.UUIDOID":
                        # clear case
                        field.default_value_expression = "uuid('WithoutBraces')"
                    elif field.oid_domain == "INTERLIS.I32OID":
                        # taking the tid as stable serial
                        field.default_value_expression = self._db_connector.tid
                    elif field.oid_domain == "INTERLIS.STANDARDOID":
                        # taking the example prefix + the tid as stable serial in 8 chars
                        field.default_value_expression = (
                            f"'ch100000' || lpad( {self._db_connector.tid}, 8, 0 )"
                        )
                    else:
                        # ANY, user- or not-defined (mostly OID TEXT, means no leading digits allowed)
                        field.default_value_expression = "'_' || uuid('WithoutBraces')"

                ## basket (t_basket)
                if self.basket_handling and column_name in BASKET_FIELDNAMES:
                    # on NONE strategy those should be all topics the class could be in. On optimized strategies GROUP/HIDE only the relevant topics should be listed.
                    interlis_topics = ",".join(
                        sorted(layer.all_topics)
                        if self.optimize_strategy == OptimizeStrategy.NONE
                        else sorted(layer.relevant_topics)
                    )

                    # and set the default value (to be used from the projet variables)
                    default_basket_topic = slugify(
                        f"default_basket{'_' if interlis_topics else ''}{interlis_topics}"
                    )
                    field.default_value_expression = f"@{default_basket_topic}"

                layer.fields.append(field)

            layers.append(layer)

        # append topic name to ambiguous layers
        self._rename_ambiguous_layers(layers)
        # append model name to still ambiguous layers
        self._rename_ambiguous_layers(layers, second_pass=True)

        self.print_messages()

        return layers

    def _rename_ambiguous_layers(self, layers, second_pass=False):
        # rename ambiguous layers with topic (on not second_pass) or model (on second_pass) prefix
        # on irrelevant layers only if we don't ride OptimizeStrategy.HIDE
        aliases = [
            l.alias
            for l in layers
            if l.is_relevant or self.optimize_strategy != OptimizeStrategy.HIDE
        ]
        ambiguous_aliases = [alias for alias in aliases if aliases.count(alias) > 1]
        for layer in layers:
            if layer.alias in ambiguous_aliases:
                if layer.ili_name:
                    if layer.ili_name.count(".") > 1:
                        layer.alias = (
                            layer.ili_name.split(".")[(0 if second_pass else 1)]
                            + "."
                            + layer.alias
                        )

    def relations(self, layers, filter_layer_list=[]):
        relations_info = self.get_relations_info(filter_layer_list)
        layer_map = dict()
        for layer in layers:
            if layer.name not in layer_map.keys():
                layer_map[layer.name] = list()
            layer_map[layer.name].append(layer)
        relations = list()

        classname_info = [
            record["iliname"] for record in self.get_iliname_dbname_mapping()
        ]

        for record in relations_info:
            if (
                record["referencing_table"] in layer_map.keys()
                and record["referenced_table"] in layer_map.keys()
            ):
                for referencing_layer in layer_map[record["referencing_table"]]:
                    if (
                        not referencing_layer.is_relevant
                        and self.optimize_strategy == OptimizeStrategy.HIDE
                    ):
                        continue
                    for referenced_layer in layer_map[record["referenced_table"]]:
                        if (
                            not referenced_layer.is_relevant
                            and self.optimize_strategy == OptimizeStrategy.HIDE
                        ):
                            continue
                        relation = Relation()
                        relation.referencing_layer = referencing_layer
                        relation.referenced_layer = referenced_layer
                        relation.referencing_field = record["referencing_column"]
                        relation.referenced_field = record["referenced_column"]
                        relation.name = record["constraint_name"]
                        relation.strength = (
                            QgsRelation.Composition
                            if "strength" in record
                            and record["strength"] == "COMPOSITE"
                            or referencing_layer.is_structure
                            else QgsRelation.Association
                        )
                        relation.cardinality_max = record.get("cardinality_max", None)

                        # For domain-class relations, if we have an extended domain, get its child name
                        child_name = None
                        if referenced_layer.is_domain:
                            # Get child name (if domain is extended)
                            fields = [
                                field
                                for field in referencing_layer.fields
                                if field.name == record["referencing_column"]
                            ]
                            if fields:
                                field = fields[0]
                                if (
                                    field.enum_domain
                                    and field.enum_domain not in classname_info
                                ):
                                    child_name = field.enum_domain
                        relation.child_domain_name = child_name

                        relations.append(relation)

        if self._db_connector.ili_version() == 3:
            # Used for ili2db version 3 relation creation
            domain_relations_generator = DomainRelationGenerator(
                self._db_connector, self.inheritance
            )
            (
                domain_relations,
                bags_of_enum,
            ) = domain_relations_generator.get_domain_relations_info(layers)
            relations = relations + domain_relations
        else:
            # Create the bags_of_enum structure
            bags_of_info = self.get_bags_of_info()
            bags_of_enum = {}
            for record in bags_of_info:
                for layer in layers:
                    if record["current_layer_name"] == layer.name:
                        new_item_list = [
                            layer,
                            record["cardinality_min"]
                            + ".."
                            + record["cardinality_max"],
                            layer_map[record["target_layer_name"]][0],
                            self._db_connector.tid,
                            self._db_connector.dispName,
                        ]
                        unique_current_layer_name = "{}_{}".format(
                            record["current_layer_name"], layer.geometry_column
                        )
                        if unique_current_layer_name in bags_of_enum.keys():
                            bags_of_enum[unique_current_layer_name][
                                record["attribute"]
                            ] = new_item_list
                        else:
                            bags_of_enum[unique_current_layer_name] = {
                                record["attribute"]: new_item_list
                            }
        return (relations, bags_of_enum)

    def generate_node(self, layers, node_name, item_properties):
        if item_properties.get("group"):
            node = LegendGroup(
                QCoreApplication.translate("LegendGroup", node_name),
                static_sorting=True,
            )
        else:
            node = Layer(alias=node_name)  # create dummy
            layers.append(node)
        return node

    def full_node(self, layers, item, path_resolver=lambda path: path):
        current_node = None
        if item and isinstance(item, dict):
            current_node_name = next(iter(item))
            # when the node exists, but there is no content we proceed with an empty dict
            item_properties = item.get(current_node_name, None) or {}
            if item_properties.get("group"):
                # get group
                current_node = self.generate_node(
                    layers, current_node_name, item_properties
                )

                # append properties
                current_node.expanded = item_properties.get("expanded", True)
                current_node.checked = item_properties.get("checked", True)
                current_node.mutually_exclusive = item_properties.get(
                    "mutually-exclusive", False
                )
                current_node.mutually_exclusive_child = item_properties.get(
                    "mutually-exclusive-child", -1
                )
                current_node.definitionfile = path_resolver(
                    item_properties.get("definitionfile")
                )

                # append child-nodes
                if "child-nodes" in item_properties:
                    for child_item in item_properties["child-nodes"]:
                        node = self.full_node(layers, child_item, path_resolver)
                        if node:
                            current_node.append(node)
            else:
                # get layer according to the tablename or iliname
                if "tablename" in item_properties or "iliname" in item_properties:
                    for layer in layers:
                        tablename = item_properties.get("tablename")
                        iliname = item_properties.get("iliname")
                        if (
                            layer.name == tablename
                            or iliname
                            and layer.ili_name == iliname
                        ):
                            # if a geometrycolumn is provided, then only consider layer if it's the right one
                            geometry_column = item_properties.get("geometrycolumn")
                            if (
                                geometry_column
                                and layer.geometry_column != geometry_column
                            ):
                                continue
                            # otherwise consider the layer and change the alias
                            layer.alias = current_node_name
                            current_node = layer
                            break

                if not current_node:
                    # get the layer according to the alias
                    for layer in layers:
                        if layer.alias == current_node_name:
                            current_node = layer
                            break

                if not current_node:
                    # get the layer according to the name
                    for layer in layers:
                        if layer.name == current_node_name:
                            current_node = layer
                            break

                if not current_node:
                    current_node = self.generate_node(
                        layers, current_node_name, item_properties
                    )

                # append properties
                current_node.expanded = item_properties.get("expanded", True)
                current_node.checked = item_properties.get("checked", True)
                current_node.featurecount = item_properties.get("featurecount", False)
                if "uri" in item_properties:
                    current_node.uri = item_properties.get("uri")
                if "provider" in item_properties:
                    current_node.provider = item_properties.get("provider")
                current_node.definitionfile = path_resolver(
                    item_properties.get("definitionfile")
                )
                current_node.qmlstylefile = path_resolver(
                    item_properties.get("qmlstylefile")
                )
                styles = {}
                if "styles" in item_properties:
                    for style_name in item_properties["styles"].keys():
                        style_properties = item_properties["styles"][style_name]
                        style_qmlstylefile = path_resolver(
                            style_properties.get("qmlstylefile")
                        )
                        styles[style_name] = {"qmlstylefile": style_qmlstylefile}
                current_node.styles = styles

        return current_node

    def legend(
        self,
        layers,
        ignore_node_names=None,
        layertree_structure=None,
        path_resolver=lambda path: path,
    ):
        legend = LegendGroup(
            QCoreApplication.translate("LegendGroup", "root"),
            ignore_node_names=ignore_node_names,
            static_sorting=layertree_structure is not None,
        )
        if layertree_structure:
            for item in layertree_structure:
                node = self.full_node(layers, item, path_resolver)
                if node:
                    legend.append(node)
        else:
            irrelevant_layers = []
            relevant_layers = []
            if self.optimize_strategy == OptimizeStrategy.NONE:
                relevant_layers = layers
            else:
                for layer in layers:
                    if layer.is_relevant:
                        relevant_layers.append(layer)
                    else:
                        irrelevant_layers.append(layer)

            (
                point_layers,
                line_layers,
                polygon_layers,
                domain_layers,
                table_layers,
                system_layers,
            ) = self._separated_legend_layers(relevant_layers)

            for l in polygon_layers:
                legend.append(l)
            for l in line_layers:
                legend.append(l)
            for l in point_layers:
                legend.append(l)

            # create groups
            if len(table_layers):
                tables = LegendGroup(
                    QCoreApplication.translate("LegendGroup", "tables")
                )
                for layer in table_layers:
                    tables.append(layer)
                legend.append(tables)
            if len(domain_layers):
                domains = LegendGroup(
                    QCoreApplication.translate("LegendGroup", "domains")
                )
                domains.expanded = False
                for layer in domain_layers:
                    domains.append(layer)
                legend.append(domains)
            if len(system_layers):
                system = LegendGroup(
                    QCoreApplication.translate("LegendGroup", "system")
                )
                system.expanded = False
                for layer in system_layers:
                    system.append(layer)
                legend.append(system)

            # when the irrelevant layers should be grouped (but visible), we make the structure for them and append it to a group
            if self.optimize_strategy == OptimizeStrategy.GROUP:
                (
                    point_layers,
                    line_layers,
                    polygon_layers,
                    domain_layers,
                    table_layers,
                    system_layers,
                ) = self._separated_legend_layers(irrelevant_layers)

                # create base group
                base_group = LegendGroup(
                    QCoreApplication.translate("LegendGroup", "base layers")
                )
                base_group.expanded = False
                base_group.checked = False

                for l in polygon_layers:
                    base_group.append(l)
                for l in line_layers:
                    base_group.append(l)
                for l in point_layers:
                    base_group.append(l)

                # create groups
                if len(table_layers):
                    tables = LegendGroup(
                        QCoreApplication.translate("LegendGroup", "base tables")
                    )
                    for layer in table_layers:
                        tables.append(layer)
                    base_group.append(tables)
                if len(domain_layers):
                    domains = LegendGroup(
                        QCoreApplication.translate("LegendGroup", "base domains")
                    )
                    domains.expanded = False
                    for layer in domain_layers:
                        domains.append(layer)
                    base_group.append(domains)

                legend.append(base_group)

        return legend

    def _separated_legend_layers(self, layers):
        domain_layers = []
        table_layers = []
        system_layers = []

        point_layers = []
        line_layers = []
        polygon_layers = []

        for layer in layers:
            if layer.geometry_column:
                geometry_type = QgsWkbTypes.geometryType(layer.wkb_type)
                if geometry_type == QgsWkbTypes.PointGeometry:
                    point_layers.append(layer)
                elif geometry_type == QgsWkbTypes.LineGeometry:
                    line_layers.append(layer)
                elif geometry_type == QgsWkbTypes.PolygonGeometry:
                    polygon_layers.append(layer)
            else:
                if layer.is_domain:
                    domain_layers.append(layer)
                elif layer.name in [
                    self._db_connector.basket_table_name,
                    self._db_connector.dataset_table_name,
                ]:
                    system_layers.append(layer)
                else:
                    table_layers.append(layer)

        return (
            point_layers,
            line_layers,
            polygon_layers,
            domain_layers,
            table_layers,
            system_layers,
        )

    def resolved_layouts(
        self,
        layouts={},
        path_resolver=lambda path: path,
    ):
        resolved_layouts = {}
        for layout_name in layouts.keys():
            resolved_layouts[layout_name] = {}
            resolved_layouts[layout_name]["templatefile"] = path_resolver(
                layouts[layout_name].get("templatefile")
            )
        return resolved_layouts

    def db_or_schema_exists(self):
        return self._db_connector.db_or_schema_exists()

    def metadata_exists(self):
        return self._db_connector.metadata_exists()

    def set_additional_ignored_layers(self, layer_list):
        self._additional_ignored_layers = layer_list

    def get_ignored_layers(self, ignore_basket_tables=True):
        return (
            self._db_connector.get_ignored_layers(ignore_basket_tables)
            + self._additional_ignored_layers
        )

    def get_tables_info(self):
        return self._db_connector.get_tables_info()

    def get_meta_attrs_info(self):
        return self._db_connector.get_meta_attrs_info()

    def get_meta_attrs(self, ili_name):
        return self._db_connector.get_meta_attrs(ili_name)

    def get_fields_info(self, table_name):
        return self._db_connector.get_fields_info(table_name)

    def get_tables_info_without_ignored_tables(self, ignore_basket_tables=True):
        tables_info = self.get_tables_info()
        ignored_layers = self.get_ignored_layers(ignore_basket_tables)
        new_tables_info = []
        for record in tables_info:
            if self.schema:
                if record["schemaname"] != self.schema:
                    continue

            if ignored_layers and record["tablename"] in ignored_layers:
                continue

            new_tables_info.append(record)

        return new_tables_info

    def get_min_max_info(self, table_name):
        return self._db_connector.get_min_max_info(table_name)

    def get_value_map_info(self, table_name):
        return self._db_connector.get_value_map_info(table_name)

    def get_relations_info(self, filter_layer_list=[]):
        return self._db_connector.get_relations_info(filter_layer_list)

    def get_bags_of_info(self):
        return self._db_connector.get_bags_of_info()

    def get_iliname_dbname_mapping(self):
        return self._db_connector.get_iliname_dbname_mapping()

    def get_basket_handling(self):
        return self._db_connector.get_basket_handling()
