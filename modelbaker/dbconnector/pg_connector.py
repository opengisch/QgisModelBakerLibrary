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
import logging
import re

import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError, sql
from qgis.core import Qgis

from .db_connector import DBConnector, DBConnectorError

PG_METADATA_TABLE = "t_ili2db_table_prop"
PG_METAATTRS_TABLE = "t_ili2db_meta_attrs"
PG_SETTINGS_TABLE = "t_ili2db_settings"
PG_DATASET_TABLE = "t_ili2db_dataset"
PG_BASKET_TABLE = "t_ili2db_basket"
PG_NLS_TABLE = "t_ili2db_nls"


class PGConnector(DBConnector):
    _geom_parse_regexp = None

    def __init__(self, uri, schema):
        DBConnector.__init__(self, uri, schema)

        try:
            self.conn = psycopg2.connect(uri)
        except OperationalError as e:
            raise DBConnectorError(str(e), e)

        self.schema = schema
        self._bMetadataTable = self._metadata_exists()
        self.iliCodeName = "ilicode"
        self.tid = "t_id"
        self.tilitid = "t_ili_tid"
        self.attachmentKey = "attachmentkey"
        self.dispName = "dispname"
        self.basket_table_name = PG_BASKET_TABLE
        self.dataset_table_name = PG_DATASET_TABLE

    def map_data_types(self, data_type):
        if not data_type:
            data_type = ""
        data_type = data_type.lower()
        if "timestamp" in data_type:
            data_type = self.QGIS_DATE_TIME_TYPE
        elif "date" in data_type:
            data_type = self.QGIS_DATE_TYPE
        elif "time" in data_type:
            data_type = self.QGIS_TIME_TYPE

        return data_type

    def _postgis_exists(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """
            SELECT
                count(extversion)
            FROM pg_catalog.pg_extension
            WHERE extname='postgis'
            """
        )

        return bool(cur.fetchone()[0])

    def db_or_schema_exists(self):
        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                """
                SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = %s);
                """,
                (self.schema,),
            )

            return bool(cur.fetchone()[0])

        return False

    def create_db_or_schema(self, usr):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if usr:
            authorization_string = sql.SQL("AUTHORIZATION") + sql.Identifier(usr)
        else:
            authorization_string = sql.SQL(";")

        parts = (
            sql.SQL("CREATE SCHEMA")
            + sql.Identifier(self.schema)
            + authorization_string
        )
        cur.execute(parts.join(" "))
        self.conn.commit()

    def metadata_exists(self):
        return self._bMetadataTable

    def _metadata_exists(self):
        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                """
                SELECT
                    count(tablename)
                FROM pg_catalog.pg_tables
                WHERE schemaname = %s and tablename = %s
                """,
                (self.schema, PG_METADATA_TABLE),
            )

            return bool(cur.fetchone()[0])

        return False

    def _table_exists(self, tablename):
        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                """
                SELECT
                    count(tablename)
                FROM pg_catalog.pg_tables
                WHERE schemaname = %s and tablename = %s
                """,
                (self.schema, tablename),
            )

            return bool(cur.fetchone()[0])

        return False

    def get_tables_info(self):
        if self.schema:
            kind_settings_field = ""
            domain_left_join = ""
            schema_where = ""
            table_alias = ""
            ili_name = ""
            extent = ""
            coord_decimals = ""
            alias_left_join = ""
            model_name = ""
            base_class = ""
            model_where = ""
            base_class_left_join = ""
            attribute_name = ""
            attribute_left_join = ""
            translations_left_join = ""
            relevance = ""
            topics = ""
            translations = ""

            if self.metadata_exists():
                tr_enabled, lang = self.get_translation_handling()
                if tr_enabled:
                    self.stdout.emit(
                        f"Getting tables info with preferred language '{lang}'."
                    )

                kind_settings_field = "p.setting AS kind_settings,"
                table_alias = "alias.setting AS table_alias,"
                ili_name = "c.iliname AS ili_name,"
                extent = """(
                    SELECT string_agg(setting, ';' ORDER BY CASE
                        WHEN cprop."tag"='ch.ehi.ili2db.c1Min' THEN 1
                        WHEN cprop."tag"='ch.ehi.ili2db.c2Min' THEN 2
                        WHEN cprop."tag"='ch.ehi.ili2db.c1Max' THEN 3
                        WHEN cprop."tag"='ch.ehi.ili2db.c2Max' THEN 4
                        END)
                    FROM {}."t_ili2db_column_prop" AS cprop
                    WHERE tbls.tablename = cprop.tablename
                    AND cprop.columnname = g.f_geometry_column
                    AND cprop."tag" IN ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                     'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
                ) AS extent,""".format(
                    self.schema
                )
                coord_decimals = """(
                    SELECT CASE MAX(position('.' in cprop.setting)) WHEN 0 THEN 0 ELSE MAX( char_length(cprop.setting) -  position('.' in cprop.setting) ) END
                    FROM {}."t_ili2db_column_prop" AS cprop
                    WHERE tbls.tablename = cprop.tablename
                    AND cprop.columnname = g.f_geometry_column
                    AND cprop."tag" IN ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                     'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
                ) AS coord_decimals,""".format(
                    self.schema
                )
                model_name = "left(c.iliname, strpos(c.iliname, '.')-1) AS model,"
                base_class = "inh.baseclass as base_class,"
                relevance = """
                        CASE WHEN c.iliname IN (
                            WITH names AS (
                                WITH topic_level_name AS (
                                    SELECT
                                    thisClass as fullname,
                                    substring(thisClass from 1 for position('.' in thisClass)-1) as model,
                                    substring(thisClass from position('.' in thisClass)+1) as topicclass
                                    FROM {schema}.t_ili2db_inheritance
                                )
                                SELECT fullname, model, topicclass, substring(topicclass from position('.' in topicclass)+1) as class
                                FROM topic_level_name
                            )
                            SELECT i.baseClass as base
                            FROM {schema}.t_ili2db_inheritance i
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
                                -- multiple times in a same extended model
                                (SELECT MAX(count) FROM (SELECT COUNT(baseClass) AS count FROM {schema}.t_ili2db_inheritance JOIN names extend_names ON thisClass = extend_names.fullname WHERE baseClass = i.baseClass GROUP BY baseClass, extend_names.model) AS counts )>1
                            )
                        )
                        THEN FALSE ELSE TRUE END AS relevance,
                    """.format(
                    schema=self.schema
                )

                # topics - where this class or an instance of it is located - are emitted by going recursively through the inheritance table.
                # if something of this topic where the current class is located has been extended, it gets the next child topic.
                # the relevant topics for optimization are the ones that are not more extended (or in the very last class).
                topics = """substring( c.iliname from 1 for position('.' in substring( c.iliname from position('.' in c.iliname)+1))+position('.' in c.iliname)-1) as base_topic,
                        (SELECT STRING_AGG(childTopic,',') FROM {topic_pedigree}) as all_topics,
                        (SELECT STRING_AGG(childTopic,',') FROM {topic_pedigree} WHERE NOT is_a_base) as relevant_topics,""".format(
                    topic_pedigree="""(WITH RECURSIVE children(is_a_base, childTopic, baseTopic) AS (
                        SELECT
                        (CASE
                            WHEN substring( thisClass from 1 for position('.' in substring( thisClass from position('.' in thisClass)+1))+position('.' in thisClass)-1) IN (SELECT substring( i.baseClass from 1 for position('.' in substring( i.baseClass from position('.' in i.baseClass)+1))+position('.' in i.baseClass)-1) FROM {schema}.T_ILI2DB_INHERITANCE i WHERE substring( i.thisClass from 1 for  position('.' in i.thisClass) ) != substring( i.baseClass from 1 for  position('.' in i.baseClass)))
                            THEN TRUE
                            ELSE FALSE
                        END) AS is_a_base,
                        substring( thisClass from 1 for position('.' in substring( thisClass, position('.' in thisClass)+1))+position('.' in thisClass)-1) as childTopic,
                        substring( baseClass from 1 for position('.' in substring( baseClass, position('.' in baseClass)+1))+position('.' in baseClass)-1) as baseTopic
                        FROM {schema}.T_ILI2DB_INHERITANCE
                        WHERE substring( baseClass from 1 for position('.' in substring( baseClass, position('.' in baseClass)+1))+position('.' in baseClass)-1) = substring( c.iliname from 1 for position('.' in substring( c.iliname from position('.' in c.iliname)+1))+position('.' in c.iliname)-1)
                        UNION
                        SELECT
                        (CASE
                            WHEN substring( thisClass from 1 for position('.' in substring( thisClass from position('.' in thisClass)+1))+position('.' in thisClass)-1) IN (SELECT substring( i.baseClass from 1 for position('.' in substring( i.baseClass from position('.' in i.baseClass)+1))+position('.' in i.baseClass)-1) FROM {schema}.T_ILI2DB_INHERITANCE i WHERE substring( i.thisClass from 1 for  position('.' in i.thisClass)) != substring( i.baseClass from 1 for position('.' in i.baseClass)))
                            THEN TRUE
                            ELSE FALSE
                        END) AS is_a_base,
                        substring( inheritance.thisClass from 1 for position('.' in substring( inheritance.thisClass from position('.' in inheritance.thisClass)+1))+position('.' in inheritance.thisClass)-1) as childTopic ,
                        substring( inheritance.baseClass from 1 for position('.' in substring( inheritance.baseClass from position('.' in baseClass)+1))+position('.' in inheritance.baseClass)-1) as baseTopic
                        FROM children
                        JOIN {schema}.T_ILI2DB_INHERITANCE as inheritance
                        ON substring( inheritance.baseClass from 1 for position('.' in substring( inheritance.baseClass from position('.' in inheritance.baseClass)+1))+position('.' in inheritance.baseClass)-1) = children.childTopic -- when the childTopic is as well the baseTopic of another childTopic
                        WHERE substring( inheritance.thisClass from 1 for position('.' in substring( inheritance.thisClass from position('.' in inheritance.thisClass)+1))+position('.' in inheritance.thisClass)-1) != children.childTopic --break the recursion when the coming childTopic will be the same
                    )
                    SELECT childTopic, baseTopic, is_a_base FROM children) AS kiddies""".format(
                        schema=self.schema
                    )
                )

                translations = """nls.label AS table_tr,""" if tr_enabled else ""

                domain_left_join = """LEFT JOIN {}.t_ili2db_table_prop p
                              ON p.tablename = tbls.tablename
                              AND p.tag = 'ch.ehi.ili2db.tableKind'""".format(
                    self.schema
                )
                alias_left_join = """LEFT JOIN {}.t_ili2db_table_prop alias
                              ON alias.tablename = tbls.tablename
                              AND alias.tag = 'ch.ehi.ili2db.dispName'""".format(
                    self.schema
                )
                model_where = """LEFT JOIN {}.t_ili2db_classname c
                      ON tbls.tablename = c.sqlname""".format(
                    self.schema
                )
                base_class_left_join = """LEFT JOIN {}.t_ili2db_inheritance inh
                      ON c.iliname = inh.thisclass""".format(
                    self.schema
                )
                attribute_name = "attrs.sqlname as attribute_name,"
                attribute_left_join = """LEFT JOIN {}.t_ili2db_attrname attrs
                      ON c.iliname = attrs.iliname""".format(
                    self.schema
                )
                translations_left_join = (
                    """LEFT JOIN {}.t_ili2db_nls nls
                      ON c.iliname = nls.ilielement
                      AND nls.lang = '{}'
                """.format(
                        self.schema, lang
                    )
                    if tr_enabled
                    else ""
                )

            schema_where = "AND schemaname = '{}'".format(self.schema)

            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cur.execute(
                """
                SELECT DISTINCT
                  tbls.schemaname AS schemaname,
                  tbls.tablename AS tablename,
                  a.attname AS primary_key,
                  g.f_geometry_column AS geometry_column,
                  g.srid AS srid,
                  {kind_settings_field}
                  {table_alias}
                  {model_name}
                  {base_class}
                  {ili_name}
                  {extent}
                  {attribute_name}
                  {coord_decimals}
                  {relevance}
                  {topics}
                  {translations}
                  g.type AS simple_type,
                  format_type(ga.atttypid, ga.atttypmod) as formatted_type
                FROM pg_catalog.pg_tables tbls
                LEFT JOIN pg_index i
                  ON i.indrelid = CONCAT(tbls.schemaname, '."', tbls.tablename, '"')::regclass
                LEFT JOIN pg_attribute a
                  ON a.attrelid = i.indrelid
                  AND a.attnum = ANY(i.indkey)
                {domain_left_join}
                {alias_left_join}
                {model_where}
                {base_class_left_join}
                {attribute_left_join}
                {translations_left_join}
                LEFT JOIN public.geometry_columns g
                  ON g.f_table_schema = tbls.schemaname
                  AND g.f_table_name = tbls.tablename
                LEFT JOIN pg_attribute ga
                  ON ga.attrelid = i.indrelid
                  AND ga.attname = g.f_geometry_column
                WHERE i.indisprimary {schema_where}
            """.format(
                    kind_settings_field=kind_settings_field,
                    table_alias=table_alias,
                    model_name=model_name,
                    base_class=base_class,
                    ili_name=ili_name,
                    extent=extent,
                    coord_decimals=coord_decimals,
                    relevance=relevance,
                    topics=topics,
                    translations=translations,
                    domain_left_join=domain_left_join,
                    alias_left_join=alias_left_join,
                    translations_left_join=translations_left_join,
                    model_where=model_where,
                    base_class_left_join=base_class_left_join,
                    attribute_name=attribute_name,
                    attribute_left_join=attribute_left_join,
                    schema_where=schema_where,
                )
            )

            return self._preprocess_table(cur)

        return []

    def get_meta_attrs_info(self):
        if not self._table_exists(PG_METAATTRS_TABLE):
            return []

        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT *
                    FROM {}.{};
                    """
                ).format(
                    sql.Identifier(self.schema), sql.Identifier(PG_METAATTRS_TABLE)
                )
            )

            return cur

        return []

    def get_meta_attrs(self, ili_name):
        if not self._table_exists(PG_METAATTRS_TABLE):
            return []

        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT
                        attr_name,
                        attr_value
                    FROM {}.{}
                    WHERE ilielement = %s;
                    """
                ).format(
                    sql.Identifier(self.schema), sql.Identifier(PG_METAATTRS_TABLE)
                ),
                (ili_name,),
            )

            return cur

        return []

    def _preprocess_table(self, records):
        for record in records:
            my_rec = {key: value for key, value in record.items()}
            geom_type = self._parse_pg_type(record["formatted_type"])
            if not geom_type:
                geom_type = record["simple_type"]
            my_rec["type"] = geom_type
            yield my_rec

    def _parse_pg_type(self, formatted_attr_type):
        if not self._geom_parse_regexp:
            self._geom_parse_regexp = re.compile(r"geometry\((\w+?),\d+\)")

        typedef = None

        if formatted_attr_type:
            match = self._geom_parse_regexp.search(formatted_attr_type)

            if match:
                typedef = match.group(1)
            else:
                typedef = None

        return typedef

    def get_fields_info(self, table_name):
        # Get all fields for this table
        if self.schema:
            fields_cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            unit_field = ""
            text_kind_field = ""
            full_name_field = ""
            enum_domain_field = ""
            oid_domain_field = ""
            attr_order_field = ""
            attr_mapping_field = ""
            translations = ""
            column_alias = ""
            unit_join = ""
            text_kind_join = ""
            disp_name_join = ""
            full_name_join = ""
            enum_domain_join = ""
            oid_domain_join = ""
            attr_order_join = ""
            attr_mapping_join = ""
            translations_left_join = ""
            order_by_attr_order = ""

            if self.metadata_exists():
                tr_enabled, lang = self.get_translation_handling()

                unit_field = "unit.setting AS unit,"
                text_kind_field = "txttype.setting AS texttype,"
                column_alias = "alias.setting AS column_alias,"
                full_name_field = "full_name.iliname as fully_qualified_name,"
                enum_domain_field = "enum_domain.setting as enum_domain,"
                oid_domain_field = "oid_domain.setting as oid_domain,"
                translations = """nls.label AS column_tr,""" if tr_enabled else ""
                unit_join = """LEFT JOIN {}.t_ili2db_column_prop unit
                                                    ON c.table_name=unit.tablename AND
                                                    c.column_name=unit.columnname AND
                                                    unit.tag = 'ch.ehi.ili2db.unit'""".format(
                    self.schema
                )
                text_kind_join = """LEFT JOIN {}.t_ili2db_column_prop txttype
                                                        ON c.table_name=txttype.tablename AND
                                                        c.column_name=txttype.columnname AND
                                                        txttype.tag = 'ch.ehi.ili2db.textKind'""".format(
                    self.schema
                )
                disp_name_join = """LEFT JOIN {}.t_ili2db_column_prop alias
                                                        ON c.table_name=alias.tablename AND
                                                        c.column_name=alias.columnname AND
                                                        alias.tag = 'ch.ehi.ili2db.dispName'""".format(
                    self.schema
                )
                full_name_join = """LEFT JOIN {}.t_ili2db_attrname full_name
                                                            ON full_name.{}='{}' AND
                                                            c.column_name=full_name.sqlname
                                                            """.format(
                    self.schema,
                    "owner" if self.ili_version() == 3 else "colowner",
                    table_name,
                )
                enum_domain_join = """LEFT JOIN {}.t_ili2db_column_prop enum_domain
                                                    ON c.table_name=enum_domain.tablename AND
                                                    c.column_name=enum_domain.columnname AND
                                                    enum_domain.tag = 'ch.ehi.ili2db.enumDomain'""".format(
                    self.schema
                )
                oid_domain_join = """LEFT JOIN {}.t_ili2db_column_prop oid_domain
                                                    ON c.table_name=oid_domain.tablename AND
                                                    lower(c.column_name)=lower(oid_domain.columnname) AND
                                                    oid_domain.tag = 'ch.ehi.ili2db.oidDomain'""".format(
                    self.schema
                )

                if self._table_exists(PG_METAATTRS_TABLE):
                    attr_order_field = "COALESCE(to_number(form_order.attr_value, '999'), 999) as attr_order,"
                    attr_order_join = """LEFT JOIN {schema}.{t_ili2db_meta_attrs} form_order
                                                            ON full_name.iliname=form_order.ilielement AND
                                                            form_order.attr_name IN (
                                                                'form_order', --obsolete
                                                                'qgis.modelbaker.form_order', --obsolete
                                                                'qgis.modelbaker.formOrder')
                                                            """.format(
                        schema=self.schema, t_ili2db_meta_attrs=PG_METAATTRS_TABLE
                    )
                    order_by_attr_order = """ORDER BY attr_order"""

                    attr_mapping_field = (
                        "meta_attr_mapping_value.attr_value as attr_mapping,"
                    )
                    attr_mapping_join = """LEFT JOIN {schema}.{t_ili2db_meta_attrs} meta_attr_mapping_value
                                                            ON full_name.iliname=meta_attr_mapping_value.ilielement AND
                                                            meta_attr_mapping_value.attr_name='ili2db.mapping'
                                                            """.format(
                        schema=self.schema, t_ili2db_meta_attrs=PG_METAATTRS_TABLE
                    )

                    translations_left_join = (
                        """LEFT JOIN {}.t_ili2db_nls nls
                                          ON full_name.iliname = nls.ilielement
                                          AND nls.lang = '{}'
                                    """.format(
                            self.schema, lang
                        )
                        if tr_enabled
                        else ""
                    )

                fields_cur.execute(
                    """
                    SELECT
                      c.column_name,
                      c.data_type,
                      c.numeric_scale,
                      {unit_field}
                      {text_kind_field}
                      {column_alias}
                      {full_name_field}
                      {enum_domain_field}
                      {oid_domain_field}
                      {attr_order_field}
                      {attr_mapping_field}
                      {translations}
                      pgd.description AS comment
                    FROM pg_catalog.pg_statio_all_tables st
                    LEFT JOIN information_schema.columns c ON c.table_schema=st.schemaname AND c.table_name=st.relname
                    LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid=st.relid AND pgd.objsubid=c.ordinal_position
                    {unit_join}
                    {text_kind_join}
                    {disp_name_join}
                    {full_name_join}
                    {enum_domain_join}
                    {oid_domain_join}
                    {attr_order_join}
                    {attr_mapping_join}
                    {translations_left_join}
                    WHERE st.relid = '{schema}."{table}"'::regclass
                    {order_by_attr_order};
                    """.format(
                        schema=self.schema,
                        table=table_name,
                        unit_field=unit_field,
                        text_kind_field=text_kind_field,
                        column_alias=column_alias,
                        full_name_field=full_name_field,
                        enum_domain_field=enum_domain_field,
                        oid_domain_field=oid_domain_field,
                        attr_order_field=attr_order_field,
                        attr_mapping_field=attr_mapping_field,
                        translations=translations,
                        unit_join=unit_join,
                        text_kind_join=text_kind_join,
                        disp_name_join=disp_name_join,
                        full_name_join=full_name_join,
                        enum_domain_join=enum_domain_join,
                        oid_domain_join=oid_domain_join,
                        attr_order_join=attr_order_join,
                        attr_mapping_join=attr_mapping_join,
                        translations_left_join=translations_left_join,
                        order_by_attr_order=order_by_attr_order,
                    )
                )

                return fields_cur

        return []

    def get_min_max_info(self, table_name):
        # Get all 'c'heck constraints for this table
        if self.schema:
            constraints_cur = self.conn.cursor(
                cursor_factory=psycopg2.extras.DictCursor
            )
            constraints_cur.execute(
                r"""
                SELECT
                  pg_get_constraintdef(oid),
                  regexp_matches(pg_get_constraintdef(oid), 'CHECK \(\(\((.*) >= [\'']?([-]?[\d\.]+)[\''::integer|numeric]*\) AND \((.*) <= [\'']?([-]?[\d\.]+)[\''::integer|numeric]*\)\)\)') AS check_details
                FROM pg_constraint
                WHERE conrelid = %s::regclass
                AND contype = 'c'
                """,
                ('{}."{}"'.format(self.schema, table_name),),
            )

            # Create a mapping in the form of
            #
            # fieldname: (min, max)
            constraint_mapping = dict()
            for constraint in constraints_cur:
                constraint_mapping[constraint["check_details"][0]] = (
                    constraint["check_details"][1],
                    constraint["check_details"][3],
                )

            return constraint_mapping

        return {}

    _ValueMapRegExp = re.compile(".*'(.*)'::.*")

    def get_value_map_info(self, table_name):
        if self.schema:
            constraints_cur = self.conn.cursor(
                cursor_factory=psycopg2.extras.DictCursor
            )
            constraints_cur.execute(
                r"""
                SELECT
                  regexp_matches(pg_get_constraintdef(oid), 'CHECK \(\(\((.*)\)::text = ANY \(\(ARRAY\[(.*)\]\)::text\[\]\)\)\)') AS check_details
                FROM pg_constraint
                WHERE conrelid = %s::regclass
                AND contype = 'c'
                """,
                ('{}."{}"'.format(self.schema, table_name),),
            )
            # Returns value in the form of
            #    {t_type,"'gl_ntznng_v1_4geobasisdaten_grundnutzung_zonenflaeche'::character varying, 'grundnutzung_zonenflaeche'::character varying"}

            constraint_mapping = dict()
            for constraint in constraints_cur:
                values = list()
                for value in constraint["check_details"][1].split(","):
                    match = re.match(PGConnector._ValueMapRegExp, value)
                    values.append(match.group(1))

                constraint_mapping[constraint["check_details"][0]] = values

            return constraint_mapping

        return {}

    def get_t_type_map_info(self, table_name):
        if self.schema and self.metadata_exists():
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT *
                    FROM {}.t_ili2db_column_prop
                    WHERE tablename = %s
                    AND tag = 'ch.ehi.ili2db.types'
                    """
                ).format(sql.Identifier(self.schema)),
                (table_name,),
            )
            types_entries = cur.fetchall()

            types_mapping = dict()
            for types_entry in types_entries:
                values = eval(types_entry["setting"])
                types_mapping[types_entry["columnname"].lower()] = values
            return types_mapping
        return {}

    def get_relations_info(self, filter_layer_list=[]):
        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            schema_where1 = "AND KCU1.CONSTRAINT_SCHEMA = '{}'".format(self.schema)
            schema_where2 = "AND KCU2.CONSTRAINT_SCHEMA = '{}'".format(self.schema)
            filter_layer_where = ""
            if filter_layer_list:
                filter_layer_where = "AND KCU1.TABLE_NAME IN ('{}')".format(
                    "','".join(filter_layer_list)
                )

            strength_field = ""
            strength_join = ""
            strength_group_by = ""
            cardinality_fields = ""
            cardinality_join = ""
            cardinality_group_bys = ""
            translate = ""

            if self._table_exists(PG_METAATTRS_TABLE):
                strength_field = ", META_ATTRS.attr_value as strength"
                strength_join = """
                            LEFT JOIN {schema}.t_ili2db_attrname AS ATTRNAME
                             ON ATTRNAME.sqlname = KCU1.COLUMN_NAME AND ATTRNAME.{colowner} = KCU1.TABLE_NAME AND ATTRNAME.target = KCU2.TABLE_NAME
                            LEFT JOIN {schema}.{t_ili2db_meta_attrs} AS META_ATTRS
                             ON META_ATTRS.ilielement = ATTRNAME.iliname AND META_ATTRS.attr_name = 'ili2db.ili.assocKind'""".format(
                    schema=self.schema,
                    t_ili2db_meta_attrs=PG_METAATTRS_TABLE,
                    colowner="owner" if self.ili_version() == 3 else "colowner",
                )
                strength_group_by = ", META_ATTRS.attr_value"

                cardinality_fields = """
                            , META_ATTRS_ATTR_CARDINALITY_MAX.attr_value as cardinality_max, META_ATTRS_ATTR_CARDINALITY_MIN.attr_value as cardinality_min
                            , META_ATTRS_ASSOC_CARDINALITY_MAX.attr_value as assoc_cardinality_max, META_ATTRS_ASSOC_CARDINALITY_MIN.attr_value as assoc_cardinality_min
                            """
                cardinality_join = """
                            LEFT JOIN {schema}.t_ili2db_attrname AS ATTRNAME_CARDINALITY
                             ON ATTRNAME_CARDINALITY.sqlname = KCU1.COLUMN_NAME AND ATTRNAME_CARDINALITY.{colowner} = KCU1.TABLE_NAME AND ATTRNAME_CARDINALITY.target = KCU2.TABLE_NAME
                            LEFT JOIN {schema}.{t_ili2db_meta_attrs} AS META_ATTRS_ATTR_CARDINALITY_MAX
                             ON META_ATTRS_ATTR_CARDINALITY_MAX.ilielement = ATTRNAME_CARDINALITY.iliname AND META_ATTRS_ATTR_CARDINALITY_MAX.attr_name = 'ili2db.ili.attrCardinalityMax'
                            LEFT JOIN {schema}.{t_ili2db_meta_attrs} AS META_ATTRS_ATTR_CARDINALITY_MIN
                             ON META_ATTRS_ATTR_CARDINALITY_MIN.ilielement = ATTRNAME_CARDINALITY.iliname AND META_ATTRS_ATTR_CARDINALITY_MIN.attr_name = 'ili2db.ili.attrCardinalityMin'
                            LEFT JOIN {schema}.{t_ili2db_meta_attrs} AS META_ATTRS_ASSOC_CARDINALITY_MAX
                             ON META_ATTRS_ASSOC_CARDINALITY_MAX.ilielement = ATTRNAME_CARDINALITY.iliname AND META_ATTRS_ASSOC_CARDINALITY_MAX.attr_name = 'ili2db.ili.assocCardinalityMax'
                            LEFT JOIN {schema}.{t_ili2db_meta_attrs} AS META_ATTRS_ASSOC_CARDINALITY_MIN
                             ON META_ATTRS_ASSOC_CARDINALITY_MIN.ilielement = ATTRNAME_CARDINALITY.iliname AND META_ATTRS_ASSOC_CARDINALITY_MIN.attr_name = 'ili2db.ili.assocCardinalityMin'""".format(
                    schema=self.schema,
                    t_ili2db_meta_attrs=PG_METAATTRS_TABLE,
                    colowner="owner" if self.ili_version() == 3 else "colowner",
                )
                cardinality_group_bys = """
                            , META_ATTRS_ATTR_CARDINALITY_MAX.attr_value, META_ATTRS_ATTR_CARDINALITY_MIN.attr_value
                            , META_ATTRS_ASSOC_CARDINALITY_MAX.attr_value, META_ATTRS_ASSOC_CARDINALITY_MIN.attr_value
                            """

                translate = (
                    ", true AS tr_enabled" if self.get_translation_handling()[0] else ""
                )

            cur.execute(
                """SELECT RC.CONSTRAINT_NAME, KCU1.TABLE_NAME AS referencing_table, KCU1.COLUMN_NAME AS referencing_column, KCU2.CONSTRAINT_SCHEMA, KCU2.TABLE_NAME AS referenced_table, KCU2.COLUMN_NAME AS referenced_column, KCU1.ORDINAL_POSITION{strength_field}{cardinality_fields}{translate}
                            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS RC
                            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU1
                             ON KCU1.CONSTRAINT_CATALOG = RC.CONSTRAINT_CATALOG AND KCU1.CONSTRAINT_SCHEMA = RC.CONSTRAINT_SCHEMA AND KCU1.CONSTRAINT_NAME = RC.CONSTRAINT_NAME {schema_where1} {filter_layer_where}
                            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU2
                             ON KCU2.CONSTRAINT_CATALOG = RC.UNIQUE_CONSTRAINT_CATALOG AND KCU2.CONSTRAINT_SCHEMA = RC.UNIQUE_CONSTRAINT_SCHEMA AND KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME
                             AND KCU2.ORDINAL_POSITION = KCU1.ORDINAL_POSITION {schema_where2}
                            {strength_join}
                            {cardinality_join}
                            GROUP BY RC.CONSTRAINT_NAME, KCU1.TABLE_NAME, KCU1.COLUMN_NAME, KCU2.CONSTRAINT_SCHEMA, KCU2.TABLE_NAME, KCU2.COLUMN_NAME, KCU1.ORDINAL_POSITION{strength_group_by}{cardinality_group_bys}
                            ORDER BY KCU1.ORDINAL_POSITION
                            """.format(
                    schema_where1=schema_where1,
                    schema_where2=schema_where2,
                    filter_layer_where=filter_layer_where,
                    strength_field=strength_field,
                    strength_join=strength_join,
                    strength_group_by=strength_group_by,
                    cardinality_fields=cardinality_fields,
                    cardinality_join=cardinality_join,
                    cardinality_group_bys=cardinality_group_bys,
                    translate=translate,
                )
            )
            return cur

        return []

    def get_bags_of_info(self):
        if self.schema and self.metadata_exists():
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """SELECT cprop.tablename as current_layer_name, cprop.columnname as attribute, cprop.setting as target_layer_name,
                        meta_attrs_cardinality_min.attr_value as cardinality_min, meta_attrs_cardinality_max.attr_value as cardinality_max
                    FROM {schema}.t_ili2db_column_prop as cprop
                    LEFT JOIN {schema}.t_ili2db_classname as cname
                    ON cname.sqlname = cprop.tablename
                    LEFT JOIN {schema}.{t_ili2db_meta_attrs} as meta_attrs_array
                    ON meta_attrs_array.ilielement ILIKE cname.iliname||'.'||cprop.columnname AND meta_attrs_array.attr_name = 'ili2db.mapping'
                    LEFT JOIN {schema}.{t_ili2db_meta_attrs} as meta_attrs_cardinality_min
                    ON meta_attrs_cardinality_min.ilielement ILIKE cname.iliname||'.'||cprop.columnname AND meta_attrs_cardinality_min.attr_name = 'ili2db.ili.attrCardinalityMin'
                    LEFT JOIN {schema}.{t_ili2db_meta_attrs} as meta_attrs_cardinality_max
                    ON meta_attrs_cardinality_max.ilielement ILIKE cname.iliname||'.'||cprop.columnname AND meta_attrs_cardinality_max.attr_name = 'ili2db.ili.attrCardinalityMax'
                    WHERE cprop.tag = 'ch.ehi.ili2db.foreignKey' AND meta_attrs_array.attr_value = 'ARRAY'
                    """
                ).format(
                    schema=sql.Identifier(self.schema),
                    t_ili2db_meta_attrs=sql.Identifier(PG_METAATTRS_TABLE),
                )
            )
            return cur
        return []

    def get_iliname_dbname_mapping(self, sqlnames=list()):
        """Note: the parameter sqlnames is only used for ili2db version 3 relation creation"""
        # Map domain ili name with its correspondent pg name
        if self.schema and self.metadata_exists():
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            where = sql.SQL(";")
            if sqlnames:
                where = sql.SQL("WHERE sqlname IN ({})").format(
                    sql.SQL(", ").join(sql.Placeholder() * len(sqlnames))
                )

            parts = (
                sql.SQL("SELECT iliname, sqlname FROM ")
                + sql.Identifier(self.schema)
                + sql.SQL(".t_ili2db_classname ")
                + where
            )

            cur.execute(parts.join(""), tuple(sqlnames))

            return cur

        return {}

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """Used for ili2db version 3 relation creation"""
        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            where = sql.SQL(" WHERE iliname IN ({})").format(
                sql.SQL(", ").join(
                    sql.Placeholder() * (len(models_info) + len(extended_classes))
                )
            )
            parts = (
                sql.SQL("SELECT * FROM ")
                + sql.Identifier(self.schema)
                + sql.SQL(".t_ili2db_classname")
                + where
            )

            cur.execute(
                parts.join(""),
                tuple(models_info.keys()) + tuple(extended_classes.keys()),
            )
            return cur

        return {}

    def get_attrili_attrdb_mapping(self, attrs_list):
        """Used for ili2db version 3 relation creation"""
        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            where = sql.SQL("WHERE iliname IN ({})").format(
                sql.SQL(", ").join(sql.Placeholder() * len(attrs_list))
                if attrs_list
                else sql.SQL("''")
            )
            parts = (
                sql.SQL("SELECT iliname, sqlname, owner FROM ")
                + sql.Identifier(self.schema)
                + sql.SQL(".t_ili2db_attrname ")
                + where
            )

            cur.execute(parts.join(""), tuple(attrs_list))
            return cur

        return {}

    def get_attrili_attrdb_mapping_by_owner(self, owners):
        """Used for ili2db version 3 relation creation"""
        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            where = sql.SQL("WHERE owner IN ({});").format(
                sql.SQL(", ").join(sql.Placeholder() * len(owners))
                if owners
                else sql.SQL("''")
            )
            parts = (
                sql.SQL("SELECT iliname, sqlname, owner FROM ")
                + sql.Identifier(self.schema)
                + sql.SQL(".t_ili2db_attrname ")
                + where
            )

            cur.execute(parts.join(""), tuple(owners))
            return cur

        return {}

    def get_models(self):
        if not self._table_exists("t_ili2db_trafo"):
            return {}

        # Get MODELS
        if self.schema:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cursor.execute(
                sql.SQL(
                    """
                    SELECT distinct split_part(iliname,'.',1) as modelname
                    FROM {}.t_ili2db_trafo
                    """
                ).format(sql.Identifier(self.schema))
            )

            models = cursor.fetchall()

            cursor.execute(
                sql.SQL(
                    """
                    SELECT modelname, content
                    FROM {}.t_ili2db_model
                    """
                ).format(sql.Identifier(self.schema))
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

            return list_result
        return {}

    def ili_version(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM information_schema.columns
            WHERE table_schema = %s
            AND(table_name='t_ili2db_attrname' OR table_name = 't_ili2db_model')
            AND(column_name='owner' OR column_name = 'file')
            """,
            (self.schema,),
        )
        if cur.rowcount > 1:
            self.new_message.emit(
                Qgis.MessageLevel.Warning,
                "DB schema created with ili2db version 3. Better use version 4.",
            )
            return 3
        else:
            return 4

    def get_basket_handling(self):
        if self.schema and self._table_exists(PG_SETTINGS_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                sql.SQL(
                    """
                    SELECT setting
                    FROM {}.{}
                    WHERE tag = %s
                    """
                ).format(
                    sql.Identifier(self.schema), sql.Identifier(PG_SETTINGS_TABLE)
                ),
                ("ch.ehi.ili2db.BasketHandling",),
            )
            content = cur.fetchone()
            if content:
                return content[0] == "readWrite"
        return False

    def get_baskets_info(self):
        if self.schema and self._table_exists(PG_BASKET_TABLE):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """SELECT b.t_id as basket_t_id,
                    b.t_ili_tid as basket_t_ili_tid,
                    b.topic as topic,
                    b.attachmentkey as attachmentkey,
                    d.t_id as dataset_t_id,
                    d.datasetname as datasetname from {schema}.{basket_table} b
                    JOIN {schema}.{dataset_table} d
                    ON b.dataset = d.t_id
                    """
                ).format(
                    schema=sql.Identifier(self.schema),
                    basket_table=sql.Identifier(PG_BASKET_TABLE),
                    dataset_table=sql.Identifier(PG_DATASET_TABLE),
                )
            )
            return cur.fetchall()
        return {}

    def get_datasets_info(self):
        if self.schema and self._table_exists(PG_DATASET_TABLE):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT t_id, datasetname
                    FROM {}.{}
                    """
                ).format(sql.Identifier(self.schema), sql.Identifier(PG_DATASET_TABLE))
            )
            return cur.fetchall()
        return {}

    def create_dataset(self, datasetname):
        if self.schema and self._table_exists(PG_DATASET_TABLE):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.{} VALUES (nextval(%s), %s)
                        """
                    ).format(
                        sql.Identifier(self.schema), sql.Identifier(PG_DATASET_TABLE)
                    ),
                    ("{}.{}".format(self.schema, "t_ili2db_seq"), datasetname),
                )
                self.conn.commit()
                return True, self.tr('Successfully created dataset "{}".').format(
                    datasetname
                )
            except psycopg2.errors.UniqueViolation as e:
                return False, self.tr('Dataset with name "{}" already exists.').format(
                    datasetname
                )
        return False, self.tr('Could not create dataset "{}".').format(datasetname)

    def rename_dataset(self, tid, datasetname):
        if self.schema and self._table_exists(PG_DATASET_TABLE):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cur.execute(
                    """
                    UPDATE {schema}.{dataset_table} SET datasetname = %(datasetname)s WHERE {tid_name} = {tid}
                    """.format(
                        schema=self.schema,
                        dataset_table=PG_DATASET_TABLE,
                        tid_name=self.tid,
                        tid=tid,
                    ),
                    {"datasetname": datasetname},
                )
                self.conn.commit()
                return True, self.tr('Successfully renamed dataset "{}".').format(
                    datasetname
                )
            except psycopg2.errors.UniqueViolation as e:
                return False, self.tr('Dataset with name "{}" already exists.').format(
                    datasetname
                )
        return False, self.tr('Could not rename dataset "{}".').format(datasetname)

    def get_topics_info(self):
        if (
            self.schema
            and self._table_exists("t_ili2db_classname")
            and self._table_exists(PG_METAATTRS_TABLE)
        ):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT DISTINCT (string_to_array(cn.iliname, '.'))[1] as model,
                    (string_to_array(cn.iliname, '.'))[2] as topic,
                    ma.attr_value as bid_domain,

                    -- relevance is emitted by going recursively through the inheritance table.
                    -- If nothing on this topic is extended, it is relevant. Otherwise it's not (except if it's extended by itself)
                    CASE WHEN (WITH RECURSIVE children(childTopic, baseTopic) AS (
                    SELECT substring( thisClass from 1 for position('.' in substring( thisClass from position('.' in thisClass)+1))+position('.' in thisClass)-1) as childTopic , substring( baseClass from 1 for position('.' in substring( baseClass from position('.' in baseClass)+1))+position('.' in baseClass)-1) as baseTopic
                    FROM {schema}.T_ILI2DB_INHERITANCE
                    WHERE substring( baseClass from 1 for position('.' in substring( baseClass from position('.' in baseClass)+1))+position('.' in baseClass)-1) = substring( CN.IliName from 1 for position('.' in substring( CN.IliName from position('.' in CN.IliName)+1))+position('.' in CN.IliName)-1) -- model.topic
                    AND substring( thisClass from 1 for position('.' in substring( thisClass from position('.' in thisClass)+1))+position('.' in thisClass)-1) != substring( CN.IliName from 1 for position('.' in substring( CN.IliName from position('.' in CN.IliName)+1))+position('.' in CN.IliName)-1) -- model.topic
                    UNION
                    SELECT substring( inheritance.thisClass from 1 for position('.' in substring( inheritance.thisClass from position('.' in inheritance.thisClass)+1))+position('.' in inheritance.thisClass)-1) as childTopic , substring( inheritance.baseClass from 1 for position('.' in substring( inheritance.baseClass from position('.' in baseClass)+1))+position('.' in inheritance.baseClass)-1) as baseTopic FROM children
                    JOIN {schema}.T_ILI2DB_INHERITANCE as inheritance ON substring( inheritance.baseClass from 1 for position('.' in substring( inheritance.baseClass from position('.' in baseClass)+1))+position('.' in inheritance.baseClass)-1) = children.childTopic
                    )SELECT count(childTopic) FROM children)>0 THEN FALSE ELSE TRUE END AS relevance

                    FROM {schema}.t_ili2db_classname as cn
                    LEFT JOIN {schema}.t_ili2db_table_prop as tp
                    ON cn.sqlname = tp.tablename
                    LEFT JOIN {schema}.t_ili2db_meta_attrs as ma
                    ON CONCAT((string_to_array(cn.iliname, '.'))[1],'.',(string_to_array(cn.iliname, '.'))[2]) = ma.ilielement and ma.attr_name = 'ili2db.ili.bidDomain'
                    WHERE array_length(string_to_array(cn.iliname, '.'),1) > 2 and ( tp.setting != 'ENUM' or  tp.setting IS NULL )
                    """
                ).format(schema=sql.Identifier(self.schema))
            )
            return cur.fetchall()

        return {}

    def get_classes_relevance(self):
        if self.schema and self._table_exists("t_ili2db_classname"):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT
                        c.iliname as iliname,
                        c.SqlName as sqlname,
                        CASE WHEN c.iliname IN (
                                WITH names AS (
                                    WITH topic_level_name AS (
                                        SELECT
                                        thisClass as fullname,
                                        substring(thisClass from 1 for position('.' in thisClass)-1) as model,
                                        substring(thisClass from position('.' in thisClass)+1) as topicclass
                                        FROM {schema}.t_ili2db_inheritance
                                    )
                                    SELECT fullname, model, topicclass, substring(topicclass from position('.' in topicclass)+1) as class
                                    FROM topic_level_name
                                )
                                SELECT i.baseClass as base
                                FROM {schema}.t_ili2db_inheritance i
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
                                    -- multiple times in a same extended model
                                    (SELECT MAX(count) FROM (SELECT COUNT(baseClass) AS count FROM {schema}.t_ili2db_inheritance JOIN names extend_names ON thisClass = extend_names.fullname WHERE baseClass = i.baseClass GROUP BY baseClass, extend_names.model) AS counts )>1
                                )
                            )
                            THEN FALSE ELSE TRUE END AS relevance
                    FROM {schema}.t_ili2db_classname c
                    """
                ).format(schema=sql.Identifier(self.schema))
            )
            return cur.fetchall()
        return []

    def create_basket(
        self, dataset_tid, topic, tilitid_value=None, attachment_key="modelbaker"
    ):
        if self.schema and self._table_exists(PG_BASKET_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                sql.SQL(
                    """
                    SELECT * FROM {}.{}
                    WHERE dataset = %s and topic = %s;
                    """
                ).format(
                    sql.Identifier(self.schema),
                    sql.Identifier(PG_BASKET_TABLE),
                ),
                (dataset_tid, topic),
            )
            if cur.fetchone():
                return False, self.tr('Basket for topic "{}" already exists.').format(
                    topic
                )
            try:
                if not tilitid_value:
                    # default value
                    tilitid_value = "uuid_generate_v4()"

                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {schema}.{basket_table} ({tid_name}, dataset, topic, {tilitid_name}, attachmentkey)
                        VALUES (nextval(%s), %s, %s, %s, %s)
                        """
                    ).format(
                        schema=sql.Identifier(self.schema),
                        basket_table=sql.Identifier(PG_BASKET_TABLE),
                        tid_name=sql.Identifier(self.tid),
                        tilitid_name=sql.Identifier(self.tilitid),
                    ),
                    (
                        "{}.{}".format(self.schema, "t_ili2db_seq"),
                        dataset_tid,
                        topic,
                        tilitid_value,
                        attachment_key,
                    ),
                )
                self.conn.commit()
                return True, self.tr(
                    'Successfully created basket for topic "{}".'
                ).format(topic)
            except psycopg2.errors.Error as e:
                error_message = " ".join(e.args)
                return False, self.tr(
                    'Could not create basket for topic "{}": {}'
                ).format(topic, error_message)
        return False, self.tr('Could not create basket for topic "{}".').format(topic)

    def edit_basket(self, basket_config: dict) -> tuple[bool, str]:
        if self.schema and self._table_exists(PG_BASKET_TABLE):
            cur = self.conn.cursor()
            try:
                cur.execute(
                    sql.SQL(
                        """
                        UPDATE {schema}.{basket_table}
                        SET dataset = %s,
                            {t_ili_tid} = %s,
                            {attachment_key} = %s
                        WHERE {tid_name} = %s
                        """
                    ).format(
                        schema=sql.Identifier(self.schema),
                        basket_table=sql.Identifier(PG_BASKET_TABLE),
                        t_ili_tid=sql.Identifier(self.tilitid),
                        attachment_key=sql.Identifier(self.attachmentKey),
                        tid_name=sql.Identifier(self.tid),
                    ),
                    (
                        basket_config["dataset_t_id"],
                        basket_config["bid_value"],
                        basket_config["attachmentkey"],
                        basket_config["basket_t_id"],
                    ),
                )
                self.conn.commit()
                return True, self.tr(
                    'Successfully edited basket for topic "{}" and dataset "{}".'
                ).format(basket_config["topic"], basket_config["datasetname"])
            except psycopg2.errors.Error as e:
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
        if self.schema and self._table_exists(PG_SETTINGS_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                sql.SQL(
                    """
                    SELECT setting
                    FROM {}.{}
                    WHERE tag = %s
                    """
                ).format(
                    sql.Identifier(self.schema), sql.Identifier(PG_SETTINGS_TABLE)
                ),
                ("ch.ehi.ili2db.TidHandling",),
            )
            content = cur.fetchone()
            if content:
                return content[0] == "property"
        return False

    def get_ili2db_settings(self):
        result = {}
        if self._table_exists(PG_SETTINGS_TABLE):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT tag, setting
                    FROM {}.{}
                    """
                ).format(sql.Identifier(self.schema), sql.Identifier(PG_SETTINGS_TABLE))
            )
            result = cur.fetchall()
        return result

    def get_ili2db_sequence_value(self):
        if self.schema:
            cur = self.conn.cursor()
            cur.execute(
                sql.SQL(
                    """
                    SELECT last_value FROM {}.{};
                    """
                ).format(sql.Identifier(self.schema), sql.Identifier("t_ili2db_seq"))
            )
            content = cur.fetchone()
            if content:
                return content[0]
        return None

    def get_next_ili2db_sequence_value(self):

        if self.schema:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT nextval(%s)
                    """
                ),
                ("{}.{}".format(self.schema, "t_ili2db_seq"),),
            )
            content = cur.fetchone()
            if content:
                return content[0]
        return None

    def set_ili2db_sequence_value(self, value):
        if self.schema:
            cur = self.conn.cursor()
            try:
                cur.execute(
                    sql.SQL(
                        """
                        ALTER SEQUENCE {}.{} RESTART WITH %s;
                        """
                    ).format(
                        sql.Identifier(self.schema), sql.Identifier("t_ili2db_seq")
                    ),
                    (value,),
                )
                self.conn.commit()
                return True, self.tr(
                    'Successfully reset sequence value to "{}".'
                ).format(value)
            except psycopg2.errors.Error as e:
                error_message = " ".join(e.args)
                return False, self.tr("Could not reset sequence: {}").format(
                    error_message
                )

        return False, self.tr("Could not reset sequence")

    def get_all_schemas(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                """
            )
        except psycopg2.errors.Error as e:
            error_message = " ".join(e.args)
            logging.error(f"Could not get the list of schemas: {error_message}")
            return []

        schemas = cursor.fetchall()

        # Transform list of tuples into list
        return list(sum(schemas, ()))

    def get_translation_handling(self) -> tuple[bool, str]:
        return self._table_exists(PG_NLS_TABLE) and self._lang != "", self._lang

    def get_available_languages(self, irrelevant_models=[]):
        if self.schema and self._table_exists(PG_NLS_TABLE):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """
                    SELECT DISTINCT
                    lang
                    FROM {schema}.t_ili2db_nls
                    WHERE
                    lang IS NOT NULL
                    AND
                    split_part(iliElement,'.',1) NOT IN ({model_list})
                    """
                ).format(
                    schema=sql.Identifier(self.schema),
                    model_list=sql.SQL(", ").join(
                        sql.Placeholder() * len(irrelevant_models)
                    ),
                ),
                irrelevant_models,
            )
            return [row["lang"] for row in cur.fetchall()]
        return []

    def get_domain_dispnames(self, tablename):
        if (
            self.schema
            and self._table_exists
            and self._table_exists(PG_NLS_TABLE)
            and self._lang != ""
        ):
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                sql.SQL(
                    """SELECT t.iliCode as code, nls.label as label
                FROM {schema}.{tablename} t
                LEFT JOIN {schema}.{t_ili2db_nls} nls
                ON nls.ilielement = (t.thisClass||'.'||t.iliCode) and lang = %s
                ;
                """
                ).format(
                    schema=sql.Identifier(self.schema),
                    tablename=sql.Identifier(tablename),
                    t_ili2db_nls=sql.Identifier(PG_NLS_TABLE),
                ),
                (self._lang,),
            )
            records = cur.fetchall()

            return records
        return []
