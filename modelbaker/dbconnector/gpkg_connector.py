"""
/***************************************************************************
    begin                :    04/10/17
    git sha              :    :%H$
    copyright            :    (C) 2017 by Germán Carrillo (BSF-Swissphoto)
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
import errno
import os
import re
import sqlite3
import uuid

import qgis.utils
from qgis.core import Qgis

from ..generator.config import GPKG_FILTER_TABLES_MATCHING_PREFIX_SUFFIX
from .db_connector import DBConnector, DBConnectorError

GPKG_METADATA_TABLE = "T_ILI2DB_TABLE_PROP"
GPKG_METAATTRS_TABLE = "T_ILI2DB_META_ATTRS"
GPKG_SETTINGS_TABLE = "T_ILI2DB_SETTINGS"
GPKG_DATASET_TABLE = "T_ILI2DB_DATASET"
GPKG_BASKET_TABLE = "T_ILI2DB_BASKET"
GPKG_NLS_TABLE = "T_ILI2DB_NLS"


class GPKGConnector(DBConnector):
    def __init__(self, uri, schema):
        DBConnector.__init__(self, uri, schema)

        if not os.path.isfile(uri):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), uri)

        try:
            self.conn = qgis.utils.spatialite_connect(uri)
        except sqlite3.Error as e:
            raise DBConnectorError(str(e), e)

        self.conn.row_factory = sqlite3.Row
        self.uri = uri
        self._bMetadataTable = self._metadata_exists()
        self._tables_info = []
        self.iliCodeName = "iliCode"
        self.tid = "T_Id"
        self.tilitid = "T_Ili_Tid"
        self.dispName = "dispName"
        self.attachmentKey = "attachmentKey"
        self.basket_table_name = GPKG_BASKET_TABLE
        self.dataset_table_name = GPKG_DATASET_TABLE

    def map_data_types(self, data_type):
        """GPKG date/time types correspond to QGIS date/time types"""
        return data_type.lower()

    def db_or_schema_exists(self):
        return os.path.isfile(self.uri)

    def create_db_or_schema(self, usr):
        """Create the DB (for GPKG)."""
        raise NotImplementedError

    def metadata_exists(self):
        return self._bMetadataTable

    def _metadata_exists(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT count(name)
            FROM sqlite_master
            WHERE name = ?;""",
            (GPKG_METADATA_TABLE,),
        )
        result = cursor.fetchone()[0] == 1
        cursor.close()
        return result

    def _table_exists(self, tablename):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT count(name)
            FROM sqlite_master
            WHERE name = ?;""",
            (tablename,),
        )
        result = cursor.fetchone()[0] == 1
        cursor.close()
        return result

    def get_tables_info(self):
        if not self._tables_info:
            self._tables_info = self._get_tables_info()
        return self._tables_info

    def _get_tables_info(self):
        cursor = self.conn.cursor()
        interlis_fields = ""
        interlis_joins = ""

        if self.metadata_exists():
            tr_enabled, lang = self.get_translation_handling()
            if tr_enabled:
                self.stdout.emit(
                    f"Getting tables info with preferred language '{lang}'."
                )

            interlis_fields = """p.setting AS kind_settings,
                alias.setting AS table_alias,
                c.iliname AS ili_name,
                (
                SELECT GROUP_CONCAT("setting", ';') FROM (
                    SELECT tablename, setting
                    FROM T_ILI2DB_COLUMN_PROP AS cprop
                    LEFT JOIN gpkg_geometry_columns g
                    ON cprop.tablename == g.table_name
                        WHERE cprop."tag" IN ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                         'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
                        AND cprop.tablename = s.name
                    ORDER BY CASE TAG
                        WHEN 'ch.ehi.ili2db.c1Min' THEN 1
                        WHEN 'ch.ehi.ili2db.c2Min' THEN 2
                        WHEN 'ch.ehi.ili2db.c1Max' THEN 3
                        WHEN 'ch.ehi.ili2db.c2Max' THEN 4
                        END ASC
                    ) WHERE g.geometry_type_name IS NOT NULL
                    GROUP BY tablename
                ) AS extent,
                (
                SELECT ( CASE MAX(INSTR("setting",'.')) WHEN 0 THEN 0 ELSE MAX( LENGTH("setting") -  INSTR("setting",'.') ) END)
                    FROM T_ILI2DB_COLUMN_PROP AS cprop
                    LEFT JOIN gpkg_geometry_columns g
                    ON cprop.tablename == g.table_name
                        WHERE cprop."tag" IN ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                         'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
						AND cprop.tablename = s.name
                    GROUP BY tablename
                )  as coord_decimals,
                substr(c.iliname, 0, instr(c.iliname, '.')) AS model,
                attrs.sqlname as attribute_name,
                {relevance_field},
                {topics},
                i.baseclass as base_class,
                {translations}  -- Optional. Trailing comma omitted on purpose.
                """.format(
                relevance_field="""CASE WHEN c.iliname IN (
                            -- used to get the class names from the full names
                            WITH names AS (
                            WITH class_level_name AS(
                                WITH topic_level_name AS (
                                    SELECT
                                    thisClass as fullname,
                                    substr(thisClass, 0, instr(thisClass, '.')) as model,
                                    substr(ltrim(thisClass,substr(thisClass, 0, instr(thisClass, '.'))),2) as topicclass
                                    FROM T_ILI2DB_INHERITANCE
                                )
                                SELECT *, ltrim(topicclass,substr(topicclass, 0, instr(topicclass, '.'))) as class_with_dot
                                FROM topic_level_name
                            )
                            SELECT fullname, model, topicclass, substr(class_with_dot, instr(class_with_dot,'.')+1) as class
                            FROM class_level_name
                            )
                            SELECT i.baseClass as base
                            FROM T_ILI2DB_INHERITANCE i
                            LEFT JOIN names extend_names
                            ON thisClass = extend_names.fullname
                            LEFT JOIN names base_names
                            ON baseClass = base_names.fullname
                            -- it's extended
                            WHERE baseClass IS NOT NULL
                            -- in a different model
                            AND base_names.model != extend_names.model
                            AND (
                                -- with the same name
                                base_names.class = extend_names.class
                                OR
                                -- multiple times in the same extended model
                                (SELECT MAX(count) FROM (SELECT COUNT(baseClass) AS count FROM T_ILI2DB_INHERITANCE JOIN names extend_names ON thisClass = extend_names.fullname WHERE baseClass = i.baseClass GROUP BY baseClass, extend_names.model) AS counts )>1
                            )
                        )
                        THEN FALSE ELSE TRUE END AS relevance""",
                # topics - where this class or an instance of it is located - are emitted by going recursively through the inheritance table.
                # if something of this topic where the current class is located has been extended, it gets the next child topic.
                # the relevant topics for optimization are the ones that are not more extended (or in the very last class).
                topics="""substr( c.iliname, 0, instr(substr( c.iliname, instr(c.iliname, '.')+1), '.')+instr(c.iliname, '.')) as base_topic,
                        (SELECT group_concat(childTopic) FROM {topic_pedigree}) as all_topics,
                        (SELECT group_concat(childTopic) FROM {topic_pedigree} WHERE NOT is_a_base) as relevant_topics""".format(
                    topic_pedigree="""(WITH RECURSIVE children(is_a_base, childTopic, baseTopic) AS (
                        SELECT
                        (CASE
                            WHEN substr( thisClass, 0, instr(substr( thisClass, instr(thisClass, '.')+1), '.')+instr(thisClass, '.')) IN (SELECT substr( i.baseClass, 0, instr(substr( i.baseClass, instr(i.baseClass, '.')+1), '.')+instr(i.baseClass, '.')) FROM T_ILI2DB_INHERITANCE i WHERE substr( i.thisClass, 0, instr(i.thisClass, '.') ) != substr( i.baseClass, 0, instr(i.baseClass, '.')))
                            THEN TRUE
                            ELSE FALSE
                        END) AS is_a_base,
                        substr( thisClass, 0, instr(substr( thisClass, instr(thisClass, '.')+1), '.')+instr(thisClass, '.')) as childTopic,
                        substr( baseClass, 0, instr(substr( baseClass, instr(baseClass, '.')+1), '.')+instr(baseClass, '.')) as baseTopic
                        FROM T_ILI2DB_INHERITANCE
                        WHERE baseTopic = substr( c.iliname, 0, instr(substr( c.iliname, instr(c.iliname, '.')+1), '.')+instr(c.iliname, '.'))
                        UNION
                        SELECT
                        (CASE
                            WHEN substr( thisClass, 0, instr(substr( thisClass, instr(thisClass, '.')+1), '.')+instr(thisClass, '.')) IN (SELECT substr( i.baseClass, 0, instr(substr( i.baseClass, instr(i.baseClass, '.')+1), '.')+instr(i.baseClass, '.')) FROM T_ILI2DB_INHERITANCE i WHERE substr( i.thisClass, 0, instr(i.thisClass, '.')) != substr( i.baseClass, 0,instr(i.baseClass, '.')))
                            THEN TRUE
                            ELSE FALSE
                        END) AS is_a_base,
                        substr( inheritance.thisClass, 0, instr(substr( inheritance.thisClass, instr(inheritance.thisClass, '.')+1), '.')+instr(inheritance.thisClass, '.')) as childTopic ,
                        substr( inheritance.baseClass, 0, instr(substr( inheritance.baseClass, instr(baseClass, '.')+1), '.')+instr(inheritance.baseClass, '.')) as baseTopic FROM children
                        JOIN T_ILI2DB_INHERITANCE as inheritance
                        ON substr( inheritance.baseClass, 0, instr(substr( inheritance.baseClass, instr(inheritance.baseClass, '.')+1), '.')+instr(inheritance.baseClass, '.')) = children.childTopic -- when the childTopic is as well the baseTopic of another childTopic
                        WHERE substr( inheritance.thisClass, 0, instr(substr( inheritance.thisClass, instr(inheritance.thisClass, '.')+1), '.')+instr(inheritance.thisClass, '.')) != children.childTopic --break the recursion when the coming childTopic will be the same
                    )
                    SELECT childTopic, baseTopic, is_a_base FROM children)"""
                ),
                translations="""nls.label AS table_tr,""" if tr_enabled else "",
            )
            interlis_joins = """LEFT JOIN T_ILI2DB_TABLE_PROP p
                   ON p.tablename = s.name
                      AND p.tag = 'ch.ehi.ili2db.tableKind'
                LEFT JOIN T_ILI2DB_TABLE_PROP alias
                   ON alias.tablename = s.name
                      AND alias.tag = 'ch.ehi.ili2db.dispName'
                LEFT JOIN T_ILI2DB_CLASSNAME c
                   ON s.name == c.sqlname
                LEFT JOIN T_ILI2DB_INHERITANCE i
                   ON c.iliname = i.thisclass
                LEFT JOIN T_ILI2DB_ATTRNAME attrs
                   ON c.iliname = attrs.iliname
                {translations}""".format(
                translations=f"""LEFT JOIN T_ILI2DB_NLS nls
                    ON c.iliname = nls.ilielement
                    AND nls.lang = '{lang}'
                """
                if tr_enabled
                else ""
            )
        try:
            cursor.execute(
                """
                SELECT DISTINCT NULL AS schemaname,
                    s.name AS tablename,
                    NULL AS primary_key,
                    g.column_name AS geometry_column,
                    g.srs_id AS srid,
                    {interlis_fields}
                    g.geometry_type_name AS type
                FROM sqlite_master s
                LEFT JOIN gpkg_geometry_columns g
                   ON g.table_name = s.name
                {interlis_joins}
                WHERE s.type='table';
            """.format(
                    interlis_fields=interlis_fields, interlis_joins=interlis_joins
                )
            )
            records = cursor.fetchall()
        except sqlite3.OperationalError as e:
            # If the geopackage is empty, geometry_columns table does not exist
            cursor.close()
            return []

        # Use prefix-suffix pairs defined in config to filter out matching tables
        filtered_records = records[:]
        for prefix_suffix in GPKG_FILTER_TABLES_MATCHING_PREFIX_SUFFIX:
            suffix_regexp = (
                "(" + "|".join(prefix_suffix["suffix"]) + ")$"
                if prefix_suffix["suffix"]
                else ""
            )
            regexp = r"{}[\W\w]+{}".format(prefix_suffix["prefix"], suffix_regexp)

            p = re.compile(
                regexp
            )  # e.g., 'rtree_[\W\w]+_(geometry|geometry_node|geometry_parent|geometry_rowid)$'
            for record in records:
                if p.match(record["tablename"]):
                    if record in filtered_records:
                        filtered_records.remove(record)

        # Get pk info and update each record storing it in a list of dicts
        complete_records = list()
        for record in filtered_records:
            cursor.execute(
                """
                PRAGMA table_info("{}")
                """.format(
                    record["tablename"]
                )
            )
            table_info = cursor.fetchall()

            primary_key_list = list()
            for table_record in table_info:
                if table_record["pk"] > 0:
                    primary_key_list.append(table_record["name"])
            primary_key = ",".join(primary_key_list) or None

            dict_record = dict(zip(record.keys(), tuple(record)))
            dict_record["primary_key"] = primary_key
            complete_records.append(dict_record)

        cursor.close()
        return complete_records

    def get_meta_attrs_info(self):
        if not self._table_exists(GPKG_METAATTRS_TABLE):
            return []

        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT *
            FROM "{}";
            """.format(
                GPKG_METAATTRS_TABLE
            )
        )
        records = cursor.fetchall()
        cursor.close()
        return records

    def get_meta_attrs(self, ili_name):
        if not self._table_exists(GPKG_METAATTRS_TABLE):
            return []

        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT
              attr_name,
              attr_value
            FROM "{}"
            WHERE ilielement=?;
            """.format(
                GPKG_METAATTRS_TABLE
            ),
            (ili_name,),
        )
        records = cursor.fetchall()
        cursor.close()
        return records

    def get_fields_info(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute("""PRAGMA table_info("{}");""".format(table_name))
        columns_info = cursor.fetchall()

        columns_prop = list()
        columns_full_name = list()
        meta_attrs = list()
        columns_tr = list()
        tr_enabled, lang = self.get_translation_handling()

        if self.metadata_exists():
            cursor.execute(
                """
                SELECT *
                FROM T_ILI2DB_COLUMN_PROP
                WHERE tablename = ?;""",
                (table_name,),
            )
            columns_prop = cursor.fetchall()

            if self.ili_version() == 3:
                cursor.execute(
                    """
                    SELECT SqlName, IliName
                    FROM T_ILI2DB_ATTRNAME
                    WHERE owner = ?;""",
                    (table_name,),
                )
            else:
                cursor.execute(
                    """
                    SELECT SqlName, IliName
                    FROM T_ILI2DB_ATTRNAME
                    WHERE colowner = ?;""",
                    (table_name,),
                )
            columns_full_name = cursor.fetchall()

            if self._table_exists(GPKG_METAATTRS_TABLE):
                meta_attrs = self.get_meta_attrs_info()

            if tr_enabled:
                cursor.execute(
                    """
                    SELECT ilielement, label
                    FROM T_ILI2DB_NLS
                    WHERE lang = ?;""",
                    (lang,),
                )
                columns_tr = cursor.fetchall()

        # Build result dict from query results
        complete_records = list()
        for column_info in columns_info:
            record = {}
            record["column_name"] = column_info["name"]
            record["data_type"] = column_info["type"]
            record["comment"] = None
            record["unit"] = None
            record["texttype"] = None
            record["column_alias"] = None
            record["enum_domain"] = None
            record["oid_domain"] = None

            if record["column_name"] == "T_Id" and Qgis.QGIS_VERSION_INT >= 30500:
                # Calculated on client side, since sqlite doesn't provide the means to pre-evaluate serials
                record[
                    "default_value_expression"
                ] = "sqlite_fetch_and_increment(@layer, 'T_KEY_OBJECT', 'T_LastUniqueId', 'T_Key', 'T_Id', map('T_LastChange','date(''now'')','T_CreateDate','date(''now'')','T_User','''' || @user_account_name || ''''))"

            for column_full_name in columns_full_name:
                if column_full_name["sqlname"] == column_info["name"]:
                    record["fully_qualified_name"] = column_full_name["iliname"]

                    for column_tr in columns_tr:
                        if column_full_name["iliname"] == column_tr["ilielement"]:
                            record["column_tr"] = column_tr["label"]
                            break
                    break

            for column_prop in columns_prop:
                if column_prop["columnname"] == column_info["name"]:
                    if column_prop["tag"] == "ch.ehi.ili2db.unit":
                        record["unit"] = column_prop["setting"]
                    elif column_prop["tag"] == "ch.ehi.ili2db.textKind":
                        record["texttype"] = column_prop["setting"]
                    elif column_prop["tag"] == "ch.ehi.ili2db.dispName":
                        record["column_alias"] = column_prop["setting"]
                    elif column_prop["tag"] == "ch.ehi.ili2db.enumDomain":
                        record["enum_domain"] = column_prop["setting"]
                    elif column_prop["tag"] == "ch.ehi.ili2db.oidDomain":
                        record["oid_domain"] = column_prop["setting"]

            record["attr_order"] = "999"
            if (
                "fully_qualified_name" in record
            ):  # e.g., t_id's don't have a fully qualified name
                attr_order_found = False
                attr_mapping_found = False
                for meta_attr in meta_attrs:
                    if record["fully_qualified_name"] != meta_attr["ilielement"]:
                        continue

                    if meta_attr["attr_name"] in [
                        "form_order",  # obsolete
                        "qgis.modelbaker.form_order",  # obsolete
                        "qgis.modelbaker.formOrder",
                    ]:
                        record["attr_order"] = meta_attr["attr_value"]
                        attr_order_found = True

                    if meta_attr["attr_name"] == "ili2db.mapping":
                        record["attr_mapping"] = meta_attr["attr_value"]
                        attr_mapping_found = True

                    if attr_order_found and attr_mapping_found:
                        break

            complete_records.append(record)

        # Finally, let's order the records by attr_order
        complete_records = sorted(complete_records, key=lambda k: int(k["attr_order"]))

        cursor.close()
        return complete_records

    def get_min_max_info(self, table_name):
        constraint_mapping = dict()
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT sql
            FROM sqlite_master
            WHERE name = ? AND type = 'table';""",
            (table_name,),
        )

        # Create a mapping in the form of
        #
        # fieldname: (min, max)
        res1 = re.findall(r"CHECK\((.*)\)", cursor.fetchone()[0])
        for res in res1:
            res2 = re.search(
                r"(\w+) BETWEEN ([-?\d\.E]+) AND ([-?\d\.E]+)", res
            )  # Might contain scientific notation
            if res2:
                constraint_mapping[res2.group(1)] = (res2.group(2), res2.group(3))

        cursor.close()
        return constraint_mapping

    def get_t_type_map_info(self, table_name):
        if self.metadata_exists():
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM T_ILI2DB_COLUMN_PROP
                WHERE tablename = ?
                AND tag = 'ch.ehi.ili2db.types';""",
                (table_name,),
            )
            types_entries = cursor.fetchall()

            types_mapping = dict()
            for types_entry in types_entries:
                values = eval(types_entry["setting"])
                types_mapping[types_entry["columnname"]] = values
            return types_mapping
        return {}

    def get_relations_info(self, filter_layer_list=[]):
        # We need to get the PK for each table, so first get tables_info
        # and then build something more searchable
        tables_info_dict = dict()
        for table_info in self._tables_info:
            tables_info_dict[table_info["tablename"]] = table_info

        cursor = self.conn.cursor()
        complete_records = list()
        tr_enabled, lang = self.get_translation_handling()

        for table_info_name, table_info in tables_info_dict.items():
            cursor.execute("""PRAGMA foreign_key_list("{}");""".format(table_info_name))
            foreign_keys = cursor.fetchall()

            for foreign_key in foreign_keys:
                record = {}
                record["referencing_table"] = table_info["tablename"]
                record["referencing_column"] = foreign_key["from"]
                record["referenced_table"] = foreign_key["table"]
                record["referenced_column"] = tables_info_dict[foreign_key["table"]][
                    "primary_key"
                ]
                record["constraint_name"] = "{}_{}_{}_{}".format(
                    record["referencing_table"],
                    record["referencing_column"],
                    record["referenced_table"],
                    record["referenced_column"],
                )
                if tr_enabled:
                    record["tr_enabled"] = True

                if self._table_exists(GPKG_METAATTRS_TABLE):
                    # Get strength
                    cursor.execute(
                        """SELECT META_ATTRS.attr_value as strength
                        FROM T_ILI2DB_ATTRNAME AS ATTRNAME
                        INNER JOIN T_ILI2DB_META_ATTRS AS META_ATTRS
                        ON META_ATTRS.ilielement = ATTRNAME.iliname AND META_ATTRS.attr_name = 'ili2db.ili.assocKind'
                        WHERE ATTRNAME.sqlname = ? AND ATTRNAME.{colowner} = ? AND ATTRNAME.target = ?;
                        """.format(
                            colowner="owner" if self.ili_version() == 3 else "colowner"
                        ),
                        (
                            foreign_key["from"],
                            table_info["tablename"],
                            foreign_key["table"],
                        ),
                    )
                    strength_record = cursor.fetchone()
                    record["strength"] = (
                        strength_record["strength"] if strength_record else ""
                    )

                    # Get cardinality max
                    cursor.execute(
                        """SELECT META_ATTRS_ATTR_MAX.attr_value as attr_cardinality_max, META_ATTRS_ATTR_MIN.attr_value as attr_cardinality_min, META_ATTRS_ASSOC_MAX.attr_value as assoc_cardinality_max, META_ATTRS_ASSOC_MIN.attr_value as assoc_cardinality_min
                        FROM T_ILI2DB_ATTRNAME AS ATTRNAME
                        LEFT JOIN T_ILI2DB_META_ATTRS AS META_ATTRS_ATTR_MAX
                        ON META_ATTRS_ATTR_MAX.ilielement = ATTRNAME.iliname AND META_ATTRS_ATTR_MAX.attr_name = 'ili2db.ili.attrCardinalityMax'
                        LEFT JOIN T_ILI2DB_META_ATTRS AS META_ATTRS_ATTR_MIN
                        ON META_ATTRS_ATTR_MIN.ilielement = ATTRNAME.iliname AND META_ATTRS_ATTR_MIN.attr_name = 'ili2db.ili.attrCardinalityMin'
                        LEFT JOIN T_ILI2DB_META_ATTRS AS META_ATTRS_ASSOC_MAX
                        ON META_ATTRS_ASSOC_MAX.ilielement = ATTRNAME.iliname AND META_ATTRS_ASSOC_MAX.attr_name = 'ili2db.ili.assocCardinalityMax'
                        LEFT JOIN T_ILI2DB_META_ATTRS AS META_ATTRS_ASSOC_MIN
                        ON META_ATTRS_ASSOC_MIN.ilielement = ATTRNAME.iliname AND META_ATTRS_ASSOC_MIN.attr_name = 'ili2db.ili.assocCardinalityMin'
                        WHERE ATTRNAME.sqlname = ? AND ATTRNAME.{colowner} = ? AND ATTRNAME.target = ?;
                        """.format(
                            colowner="owner" if self.ili_version() == 3 else "colowner"
                        ),
                        (
                            foreign_key["from"],
                            table_info["tablename"],
                            foreign_key["table"],
                        ),
                    )
                    cardinality_record = cursor.fetchone()
                    record["cardinality_max"] = (
                        cardinality_record["attr_cardinality_max"]
                        if cardinality_record
                        else ""
                    )
                    record["cardinality_min"] = (
                        cardinality_record["attr_cardinality_min"]
                        if cardinality_record
                        else ""
                    )
                    record["assoc_cardinality_max"] = (
                        cardinality_record["assoc_cardinality_max"]
                        if cardinality_record
                        else ""
                    )
                    record["assoc_cardinality_min"] = (
                        cardinality_record["assoc_cardinality_min"]
                        if cardinality_record
                        else ""
                    )
                complete_records.append(record)

        cursor.close()
        return complete_records

    def get_bags_of_info(self):
        bags_of_info = {}
        if self.metadata_exists():
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT cprop.tablename as current_layer_name, cprop.columnname as attribute, cprop.setting as target_layer_name,
                            meta_attrs_cardinality_min.attr_value as cardinality_min, meta_attrs_cardinality_max.attr_value as cardinality_max
                            FROM T_ILI2DB_COLUMN_PROP as cprop
                            LEFT JOIN T_ILI2DB_CLASSNAME as cname
                            ON cname.sqlname = cprop.tablename
                            LEFT JOIN T_ILI2DB_META_ATTRS as meta_attrs_array
                            ON LOWER(meta_attrs_array.ilielement) = LOWER(cname.iliname||'.'||cprop.columnname) AND meta_attrs_array.attr_name = 'ili2db.mapping'
                            LEFT JOIN T_ILI2DB_META_ATTRS as meta_attrs_cardinality_min
                            ON LOWER(meta_attrs_cardinality_min.ilielement) = LOWER(cname.iliname||'.'||cprop.columnname) AND meta_attrs_cardinality_min.attr_name = 'ili2db.ili.attrCardinalityMin'
                            LEFT JOIN T_ILI2DB_META_ATTRS as meta_attrs_cardinality_max
                            ON LOWER(meta_attrs_cardinality_max.ilielement) = LOWER(cname.iliname||'.'||cprop.columnname) AND meta_attrs_cardinality_max.attr_name = 'ili2db.ili.attrCardinalityMax'
                            WHERE cprop.tag = 'ch.ehi.ili2db.foreignKey' AND meta_attrs_array.attr_value = 'ARRAY'
                            """
            )
            bags_of_info = cursor.fetchall()
            cursor.close()
        return bags_of_info

    def is_spatial_index_table(self, tablename=str) -> bool:
        """Note: Checks if the table is a technical table used for spatial indexing"""
        if tablename and tablename[0:6] == "rtree_":
            return True
        return False

    def get_iliname_dbname_mapping(self, sqlnames=list()):
        """Note: the parameter sqlnames is only used for ili2db version 3 relation creation"""
        # Map domain ili name with its correspondent sql name
        if self.metadata_exists():
            cursor = self.conn.cursor()

            where = ""
            if sqlnames:
                names = "'" + "','".join(sqlnames) + "'"
                where = "WHERE sqlname IN ({})".format(names)

            cursor.execute(
                """SELECT iliname, sqlname
                FROM T_ILI2DB_CLASSNAME
                {where}
                """.format(
                    where=where
                )
            )
            return cursor

        return {}

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """Used for ili2db version 3 relation creation"""
        cursor = self.conn.cursor()
        class_names = (
            "'"
            + "','".join(list(models_info.keys()) + list(extended_classes.keys()))
            + "'"
        )
        cursor.execute(
            """SELECT *
            FROM T_ILI2DB_CLASSNAME
            WHERE iliname IN ({class_names})
            """.format(
                class_names=class_names
            )
        )
        return cursor

    def get_attrili_attrdb_mapping(self, attrs_list):
        """Used for ili2db version 3 relation creation"""
        cursor = self.conn.cursor()
        attr_names = "'" + "','".join(attrs_list) + "'"
        cursor.execute(
            """SELECT iliname, sqlname, owner
            FROM T_ILI2DB_ATTRNAME
            WHERE iliname IN ({attr_names})
            """.format(
                attr_names=attr_names
            )
        )
        return cursor

    def get_attrili_attrdb_mapping_by_owner(self, owners):
        """Used for ili2db version 3 relation creation"""
        cursor = self.conn.cursor()
        owner_names = "'" + "','".join(owners) + "'"
        cursor.execute(
            """SELECT iliname, sqlname, owner
            FROM T_ILI2DB_ATTRNAME
            WHERE owner IN ({owner_names})
            """.format(
                owner_names=owner_names
            )
        )
        return cursor

    def get_models(self):
        if not self._table_exists("T_ILI2DB_TRAFO"):
            return {}

        # Get MODELS
        cursor = self.conn.cursor()

        cursor.execute(
            """SELECT distinct substr(iliname, 1, pos-1) AS modelname from
            (SELECT *, instr(iliname,'.') AS pos FROM T_ILI2DB_TRAFO)"""
        )

        models = cursor.fetchall()

        cursor.execute(
            """SELECT modelname, content
            FROM T_ILI2DB_MODEL"""
        )

        contents = cursor.fetchall()

        result = dict()
        list_result = []

        for content in contents:
            for model in models:
                if model["modelname"] in re.sub(
                    r"(?:\{[^\}]*\}|\s)", "", content["modelname"]
                ):
                    result["modelname"] = model["modelname"]
                    result["content"] = content["content"]
                    match = re.search(
                        re.escape(model["modelname"]) + r"\{\s([^\}]*)\}",
                        content["modelname"],
                    )
                    result["parents"] = match.group(1).split() if match else []
                    list_result.append(result)
                    result = dict()

        cursor.close()
        return list_result

    def ili_version(self):
        cursor = self.conn.cursor()
        cursor.execute("""PRAGMA table_info(T_ILI2DB_ATTRNAME)""")
        table_info = cursor.fetchall()
        result = 0
        for column_info in table_info:
            if column_info[1] == "Owner":
                result += 1
        cursor.execute("""PRAGMA table_info(T_ILI2DB_MODEL)""")
        table_info = cursor.fetchall()
        for column_info in table_info:
            if column_info[1] == "file":
                result += 1
        cursor.close()
        if result > 1:
            self.new_message.emit(
                Qgis.MessageLevel.Warning,
                "DB schema created with ili2db version 3. Better use version 4.",
            )
            return 3
        else:
            return 4

    def get_basket_handling(self):
        if self._table_exists(GPKG_SETTINGS_TABLE):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT setting
                FROM "{}"
                WHERE tag = ?
                """.format(
                    GPKG_SETTINGS_TABLE
                ),
                ("ch.ehi.ili2db.BasketHandling",),
            )
            content = cursor.fetchone()
            cursor.close()
            if content:
                return content[0] == "readWrite"
        return False

    def get_baskets_info(self):
        if self._table_exists(GPKG_BASKET_TABLE):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT b.t_id as basket_t_id,
                b.t_ili_tid as basket_t_ili_tid,
                b.topic as topic,
                b.attachmentkey as attachmentkey,
                d.t_id as dataset_t_id,
                d.datasetname as datasetname from "{basket_table}" b
                JOIN "{dataset_table}" d
                ON b.dataset = d.t_id;
                """.format(
                    basket_table=GPKG_BASKET_TABLE, dataset_table=GPKG_DATASET_TABLE
                )
            )
            contents = cursor.fetchall()
            cursor.close()
            return contents
        return {}

    def get_datasets_info(self):
        if self._table_exists(GPKG_DATASET_TABLE):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT t_id, datasetname
                FROM "{dataset_table}";
                """.format(
                    dataset_table=GPKG_DATASET_TABLE
                )
            )
            contents = cursor.fetchall()
            cursor.close()
            return contents
        return {}

    def create_dataset(self, datasetname):
        if self._table_exists(GPKG_DATASET_TABLE):
            cursor = self.conn.cursor()
            try:
                (
                    status,
                    next_id,
                    fetch_and_increment_feedback,
                ) = self._fetch_and_increment_key_object(self.tid)
                if not status:
                    cursor.close()
                    return False, self.tr('Could not create dataset "{}": {}').format(
                        datasetname, fetch_and_increment_feedback
                    )

                cursor.execute(
                    """
                    INSERT INTO {dataset_table} ({tid_name},datasetName) VALUES (:next_id, :datasetname)
                    """.format(
                        tid_name=self.tid, dataset_table=GPKG_DATASET_TABLE
                    ),
                    {"datasetname": datasetname, "next_id": next_id},
                )
                self.conn.commit()
                cursor.close()
                return True, self.tr('Successfully created dataset "{}".').format(
                    datasetname
                )
            except sqlite3.Error as e:
                cursor.close()
                error_message = " ".join(e.args)
                return False, self.tr('Could not create dataset "{}": {}').format(
                    datasetname, error_message
                )
        return False, self.tr('Could not create dataset "{}".').format(datasetname)

    def rename_dataset(self, tid, datasetname):
        if self._table_exists(GPKG_DATASET_TABLE):
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE {dataset_table} SET datasetName = :datasetname WHERE {tid_name} = {tid}
                    """.format(
                        dataset_table=GPKG_DATASET_TABLE, tid_name=self.tid, tid=tid
                    ),
                    {"datasetname": datasetname},
                )
                self.conn.commit()
                cursor.close()
                return True, self.tr('Successfully renamed dataset to "{}".').format(
                    datasetname
                )
            except sqlite3.Error as e:
                cursor.close()
                error_message = " ".join(e.args)
                return False, self.tr('Could not rename dataset to "{}": {}').format(
                    datasetname, error_message
                )
        return False, self.tr('Could not rename dataset to "{}".').format(datasetname)

    def get_topics_info(self):
        if self._table_exists("T_ILI2DB_CLASSNAME") and self._table_exists(
            GPKG_METAATTRS_TABLE
        ):
            cursor = self.conn.cursor()
            cursor.execute(
                """
                    SELECT DISTINCT substr(CN.IliName, 0, instr(CN.IliName, '.')) as model,
                    substr(substr(CN.IliName, instr(CN.IliName, '.')+1),0, instr(substr(CN.IliName, instr(CN.IliName, '.')+1),'.')) as topic,
                    MA.attr_value as bid_domain,
                    {relevance}
                    FROM T_ILI2DB_CLASSNAME as CN
                    LEFT JOIN T_ILI2DB_TABLE_PROP as TP
                    ON CN.sqlname = TP.tablename
                    LEFT JOIN T_ILI2DB_META_ATTRS as MA
                    ON substr( CN.IliName, 0, instr(substr( CN.IliName, instr(CN.IliName, '.')+1), '.')+instr(CN.IliName, '.')) = MA.ilielement and MA.attr_name = 'ili2db.ili.bidDomain'
                    WHERE topic != '' and ( TP.setting != 'ENUM' or TP.setting IS NULL )
                """.format(
                    # relevance is emitted by going recursively through the inheritance table. If nothing on this topic is extended, it is relevant. Otherwise it's not (except if it's extended by itself)
                    relevance="""
                        CASE WHEN (WITH RECURSIVE children(childTopic, baseTopic) AS (
                        SELECT substr( thisClass, 0, instr(substr( thisClass, instr(thisClass, '.')+1), '.')+instr(thisClass, '.')) as childTopic , substr( baseClass, 0, instr(substr( baseClass, instr(baseClass, '.')+1), '.')+instr(baseClass, '.')) as baseTopic
                        FROM T_ILI2DB_INHERITANCE
                        WHERE baseTopic = substr( CN.IliName, 0, instr(substr( CN.IliName, instr(CN.IliName, '.')+1), '.')+instr(CN.IliName, '.')) -- model.topic
                        AND baseTopic != childTopic
                        UNION
                        SELECT substr( inheritance.thisClass, 0, instr(substr( inheritance.thisClass, instr(inheritance.thisClass, '.')+1), '.')+instr(inheritance.thisClass, '.')) as childTopic , substr( inheritance.baseClass, 0, instr(substr( inheritance.baseClass, instr(baseClass, '.')+1), '.')+instr(inheritance.baseClass, '.')) as baseTopic FROM children
                        JOIN T_ILI2DB_INHERITANCE as inheritance ON substr( inheritance.baseClass, 0, instr(substr( inheritance.baseClass, instr(baseClass, '.')+1), '.')+instr(inheritance.baseClass, '.')) = children.childTopic
                        )SELECT count(childTopic) FROM children)>0 THEN FALSE ELSE TRUE END AS relevance
                    """
                )
            )
            contents = cursor.fetchall()
            cursor.close()
            return contents
        return {}

    def get_classes_relevance(self):
        if self._table_exists("T_ILI2DB_CLASSNAME"):
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.iliname as iliname,
                    c.SqlName as sqlname,
                    CASE WHEN c.iliname IN (
                            WITH names AS (
                                WITH class_level_name AS(
                                    WITH topic_level_name AS (
                                        SELECT
                                        thisClass as fullname,
                                        substr(thisClass, 0, instr(thisClass, '.')) as model,
                                        substr(ltrim(thisClass,substr(thisClass, 0, instr(thisClass, '.'))),2) as topicclass
                                        FROM T_ILI2DB_INHERITANCE
                                    )
                                    SELECT *, ltrim(topicclass,substr(topicclass, 0, instr(topicclass, '.'))) as class_with_dot
                                    FROM topic_level_name
                                )
                                SELECT fullname, model, topicclass, substr(class_with_dot, instr(class_with_dot,'.')+1) as class
                                FROM class_level_name
                                )
                                SELECT i.baseClass as iliname
                                FROM T_ILI2DB_INHERITANCE i
                                LEFT JOIN names extend_names
                                ON thisClass = extend_names.fullname
                                LEFT JOIN names base_names
                                ON baseClass = base_names.fullname
                                -- it's extended
                                LEFT JOIN T_ILI2DB_CLASSNAME c
                                ON IliName = i.baseClass
                                WHERE baseClass IS NOT NULL
                                -- in a different model
                                AND base_names.model != extend_names.model
                                AND (
                                    -- with the same name
                                    base_names.class = extend_names.class
                                    OR
                                    -- multiple times in the same extended model
                                    (SELECT MAX(count) FROM (SELECT COUNT(baseClass) AS count FROM T_ILI2DB_INHERITANCE JOIN names extend_names ON thisClass = extend_names.fullname WHERE baseClass = i.baseClass GROUP BY baseClass, extend_names.model) AS counts )>1
                                )
                    ) THEN FALSE ELSE TRUE END AS relevance
                FROM T_ILI2DB_CLASSNAME c
                """
            )
            contents = cursor.fetchall()
            cursor.close()
            return contents
        return []

    def multiple_geometry_tables(self):
        tables = []
        if self._table_exists("gpkg_geometry_columns"):
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT table_name
                FROM gpkg_geometry_columns
                GROUP BY table_name
                HAVING COUNT(table_name)>1
            """
            )
            records = cursor.fetchall()
            cursor.close()
            for record in records:
                tables.append(record["table_name"])

        return tables

    def create_basket(
        self, dataset_tid, topic, tilitid_value=None, attachment_key="modelbaker"
    ):
        if self._table_exists(GPKG_BASKET_TABLE):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT * FROM {basket_table}
                WHERE dataset = ? and topic = ?
                """.format(
                    basket_table=GPKG_BASKET_TABLE
                ),
                (dataset_tid, topic),
            )
            if cursor.fetchone():
                cursor.close()
                return False, self.tr('Basket for topic "{}" already exists.').format(
                    topic
                )
            try:
                (
                    status,
                    next_id,
                    fetch_and_increment_feedback,
                ) = self._fetch_and_increment_key_object(self.tid)
                if not status:
                    return False, self.tr(
                        'Could not create basket for topic "{}": {}'
                    ).format(topic, fetch_and_increment_feedback)
                if not tilitid_value:
                    # default value
                    tilitid_value = f"{uuid.uuid4()}"
                cursor.execute(
                    """
                    INSERT INTO "{basket_table}" ("{tid_name}", dataset, topic, "{tilitid_name}", attachmentkey )
                    VALUES (?, ?, ?, ?, ?)
                    """.format(
                        tid_name=self.tid,
                        tilitid_name=self.tilitid,
                        basket_table=GPKG_BASKET_TABLE,
                    ),
                    (
                        next_id,
                        dataset_tid,
                        topic,
                        tilitid_value,
                        attachment_key,
                    ),
                )
                self.conn.commit()
                cursor.close()
                return True, self.tr(
                    'Successfully created basket for topic "{}".'
                ).format(topic)
            except sqlite3.Error as e:
                cursor.close()
                error_message = " ".join(e.args)
                return False, self.tr(
                    'Could not create basket for topic "{}": {}'
                ).format(topic, error_message)
        return False, self.tr('Could not create basket for topic "{}".').format(topic)

    def edit_basket(self, basket_config: dict) -> tuple[bool, str]:
        if self._table_exists(GPKG_BASKET_TABLE):
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE {basket_table}
                    SET dataset = ?,
                        {t_ili_tid} = ?,
                        {attachment_key} = ?
                    WHERE {tid_name} = ?
                    """.format(
                        basket_table=GPKG_BASKET_TABLE,
                        t_ili_tid=self.tilitid,
                        attachment_key=self.attachmentKey,
                        tid_name=self.tid,
                    ),
                    (
                        basket_config["dataset_t_id"],
                        basket_config["bid_value"],
                        basket_config["attachmentkey"],
                        basket_config["basket_t_id"],
                    ),
                )
                self.conn.commit()
                cursor.close()
                return True, self.tr(
                    'Successfully edited basket for topic "{}" and dataset "{}".'
                ).format(basket_config["topic"], basket_config["datasetname"])
            except sqlite3.Error as e:
                cursor.close()
                error_message = " ".join(e.args)
                return False, self.tr(
                    'Could not edit basket for topic "{}" and dataset "{}": {}'
                ).format(
                    basket_config["topic"], basket_config["datasetname"], error_message
                )
        return False, self.tr(
            'Could not edit basket for topic "{}" and dataset "{}"'
        ).format(basket_config["topic"], basket_config["datasetname"])

    def get_tid_handling(self):
        if self._table_exists(GPKG_SETTINGS_TABLE):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT setting
                FROM "{}"
                WHERE tag = ?
                """.format(
                    GPKG_SETTINGS_TABLE
                ),
                ("ch.ehi.ili2db.TidHandling",),
            )
            content = cursor.fetchone()
            cursor.close()
            if content:
                return content[0] == "property"
        return False

    def get_ili2db_settings(self):
        result = {}
        if self._table_exists(GPKG_SETTINGS_TABLE):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT *
                FROM "{}"
                """.format(
                    GPKG_SETTINGS_TABLE
                )
            )
            result = cursor.fetchall()
            cursor.close()
        return result

    def _fetch_and_increment_key_object(self, field_name):
        next_id = 0
        if self._table_exists("T_KEY_OBJECT"):
            # fetch last unique id of field_name
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT T_LastUniqueId, T_CreateDate FROM T_KEY_OBJECT
                WHERE T_Key = ?""",
                (field_name,),
            )

            content = cursor.fetchone()

            create_date = "date('now')"

            # increment
            if content:
                next_id = content[0] + 1
                create_date = content[1]

            # and update
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO T_KEY_OBJECT (T_Key, T_LastUniqueId, T_LastChange, T_CreateDate, T_User )
                    VALUES (:key, :next_id, date('now'), :create_date, 'modelbaker')
                """,
                    {"key": field_name, "next_id": next_id, "create_date": create_date},
                )
                self.conn.commit()
                cursor.close()
                return (
                    True,
                    next_id,
                    self.tr("Successfully set the T_LastUniqueId to {}.").format(
                        next_id
                    ),
                )
            except sqlite3.Error as e:
                cursor.close()
                error_message = " ".join(e.args)
                return (
                    False,
                    next_id,
                    self.tr("Could not set the T_LastUniqueId to {}: {}").format(
                        next_id, error_message
                    ),
                )
        return (
            False,
            next_id,
            self.tr(
                "Could not fetch T_LastUniqueId because T_KEY_OBJECT does not exist."
            ),
        )

    def get_ili2db_sequence_value(self):
        if self._table_exists("T_KEY_OBJECT"):
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT T_LastUniqueId FROM T_KEY_OBJECT
                WHERE T_Key = ?;""",
                (self.tid,),
            )

            content = cursor.fetchone()
            cursor.close()

            if content:
                return content[0]
        return None

    def get_next_ili2db_sequence_value(self):
        (
            status,
            next_id,
            fetch_and_increment_feedback,
        ) = self._fetch_and_increment_key_object(self.tid)
        return next_id

    def set_ili2db_sequence_value(self, value):
        if self._table_exists("T_KEY_OBJECT"):
            try:
                cursor = self.conn.cursor()
                if not self.get_ili2db_sequence_value():
                    # need to create the entry
                    cursor.execute(
                        """
                        INSERT INTO T_KEY_OBJECT (T_Key, T_LastUniqueId, T_LastChange, T_CreateDate, T_User )
                        VALUES (?, ?, date('now'), date('now'), 'modelbaker')
                        """,
                        (self.tid, value),
                    )
                else:
                    # just update it
                    cursor.execute(
                        """UPDATE T_KEY_OBJECT SET
                        T_LastUniqueID = ?,
                        T_LastChange = date('now'),
                        T_User = 'modelbaker'
                        WHERE T_Key = ?;""",
                        (value, self.tid),
                    )
                self.conn.commit()
                cursor.close()
                return True, self.tr("Successfully reset T_LastUniqueId to {}.").format(
                    value
                )
            except sqlite3.Error as e:
                cursor.close()
                error_message = " ".join(e.args)
                return False, self.tr("Could not reset T_LastUniqueId: {}").format(
                    error_message
                )

        return False, self.tr("Could not reset T_LastUniqueId")

    def get_translation_handling(self) -> tuple[bool, str]:
        return self._table_exists(GPKG_NLS_TABLE) and self._lang != "", self._lang

    def get_available_languages(self, irrelevant_models=[]):
        if not self._table_exists(GPKG_NLS_TABLE):
            return []

        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT DISTINCT
            lang
            FROM "{t_ili2db_nls}"
            WHERE
            lang IS NOT NULL
            AND
            substr(iliElement, 0, instr(iliElement, '.')) NOT IN ({model_list})
            ;
            """.format(
                t_ili2db_nls=GPKG_NLS_TABLE,
                model_list=",".join(
                    [f"'{modelname}'" for modelname in irrelevant_models]
                ),
            )
        )
        records = cursor.fetchall()
        cursor.close()
        return [record["lang"] for record in records]

    def get_domain_dispnames(self, tablename):
        if (
            not self._table_exists
            or not self._table_exists(GPKG_NLS_TABLE)
            or self._lang == ""
        ):
            return []

        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT t.iliCode as code, nls.label as label
            FROM "{tablename}" t
            LEFT JOIN "{t_ili2db_nls}" nls
            ON nls.ilielement = (t.thisClass||'.'||t.iliCode) and lang = '{lang}'
            ;
            """.format(
                tablename=tablename, t_ili2db_nls=GPKG_NLS_TABLE, lang=self._lang
            )
        )
        records = cursor.fetchall()
        cursor.close()

        return records
