"""
/***************************************************************************
    begin                :    01/02/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polanía (BSF-Swissphoto)
    email                :    yesidpol.3@gmail.com
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

import pyodbc
from qgis.core import Qgis

from .db_connector import DBConnector, DBConnectorError

METADATA_TABLE = "t_ili2db_table_prop"
METAATTRS_TABLE = "t_ili2db_meta_attrs"
SETTINGS_TABLE = "t_ili2db_settings"
DATASET_TABLE = "t_ili2db_dataset"
BASKET_TABLE = "t_ili2db_basket"


class MssqlConnector(DBConnector):
    def __init__(self, uri, schema):
        DBConnector.__init__(self, uri, schema)

        try:
            self.conn = pyodbc.connect(uri)
        except (
            pyodbc.ProgrammingError,
            pyodbc.InterfaceError,
            pyodbc.Error,
            pyodbc.OperationalError,
        ) as e:
            raise DBConnectorError(str(e), e)

        self.schema = schema

        self._bMetadataTable = self._metadata_exists()
        self.iliCodeName = "iliCode"
        self.tid = "T_Id"
        self.tilitid = "T_Ili_Tid"
        self.dispName = "dispName"
        self.basket_table_name = BASKET_TABLE
        self.dataset_table_name = DATASET_TABLE

    def map_data_types(self, data_type):
        result = data_type.lower()
        if "timestamp" in data_type:
            result = self.QGIS_DATE_TIME_TYPE
        elif "date" in data_type:
            result = self.QGIS_DATE_TYPE
        elif "time" in data_type:
            result = self.QGIS_TIME_TYPE

        return result

    def db_or_schema_exists(self):
        if self.schema:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT case when count(schema_name)>0 then 1 else 0 end
                FROM information_schema.schemata
                where schema_name = '{}'
            """.format(
                    self.schema
                )
            )

            return bool(cur.fetchone()[0])

        return False

    def metadata_exists(self):
        return self._bMetadataTable

    def _metadata_exists(self):
        return self._table_exists(METADATA_TABLE)

    def _table_exists(self, tablename):
        if self.schema:
            cur = self.conn.cursor()
            cur.execute(
                """
            SELECT count(TABLE_NAME) as 'count'
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA = '{}'
                    AND TABLE_NAME = '{}'
            """.format(
                    self.schema, tablename
                )
            )

            return bool(cur.fetchone()[0])

        return False

    def get_tables_info(self):
        res = []

        if self.schema:
            metadata_exists = self.metadata_exists()

            ln = "\n"
            stmt = ""
            stmt += ln + "SELECT distinct"
            stmt += ln + "     tbls.TABLE_SCHEMA AS schemaname"
            stmt += ln + "    , tbls.TABLE_NAME AS tablename"
            stmt += ln + "    , Col.Column_Name AS primary_key"
            stmt += ln + "    , clm.COLUMN_NAME AS geometry_column"
            if metadata_exists:
                stmt += ln + "    , tsrid.setting AS srid"
                stmt += ln + "    , p.setting AS kind_settings"
                stmt += ln + "    , alias.setting AS table_alias"
                stmt += (
                    ln + "    , left(c.iliname, charindex('.', c.iliname)-1) AS model"
                )
                stmt += ln + "    , c.iliname AS ili_name"
                stmt += ln + "    , STUFF("
                stmt += ln + "       (SELECT ';' + CAST(cp.setting AS VARCHAR(MAX))"
                stmt += ln + "        FROM {schema}.t_ili2db_column_prop cp"
                stmt += ln + "        WHERE tbls.table_name = cp.tablename"
                stmt += ln + "            AND clm.COLUMN_NAME = cp.columnname"
                stmt += ln + "            AND cp.tag IN"
                stmt += (
                    ln
                    + "                ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',"
                )
                stmt += (
                    ln + "                'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')"
                )
                stmt += (
                    ln
                    + "        order by case cp.tag WHEN 'ch.ehi.ili2db.c1Min' THEN 1"
                )
                stmt += ln + "            WHEN 'ch.ehi.ili2db.c2Min' THEN 2"
                stmt += ln + "            WHEN 'ch.ehi.ili2db.c1Max' THEN 3"
                stmt += ln + "            WHEN 'ch.ehi.ili2db.c2Max' THEN 4"
                stmt += ln + "            END"
                stmt += (
                    ln
                    + "        FOR XML PATH(''),TYPE).value('(./text())[1]','VARCHAR(MAX)'),1,1,''"
                )
                stmt += ln + "        ) AS extent"
                stmt += (
                    ln
                    + "    , ( SELECT CASE MAX(CHARINDEX('.',cp.setting)) WHEN 0 THEN 0 ELSE MAX( LEN(cp.setting) -  CHARINDEX('.',cp.setting) ) END"
                )
                stmt += ln + "        FROM {schema}.t_ili2db_column_prop cp"
                stmt += ln + "        WHERE tbls.table_name = cp.tablename"
                stmt += ln + "            AND clm.COLUMN_NAME = cp.columnname"
                stmt += ln + "            AND cp.tag IN"
                stmt += (
                    ln
                    + "                ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',"
                )
                stmt += (
                    ln + "                'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')"
                )
                stmt += ln + "      ) AS coord_decimals"
                stmt += ln + "    , tgeomtype.setting AS simple_type"
                stmt += ln + "    , null AS formatted_type"
                stmt += ln + "    , attrs.sqlname AS attribute_name"
            stmt += ln + "FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS Tab"
            stmt += ln + "INNER JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS Col"
            stmt += ln + "    ON Col.Constraint_Name = Tab.Constraint_Name"
            stmt += ln + "    AND Col.Table_Name = Tab.Table_Name"
            stmt += ln + "    AND Col.CONSTRAINT_SCHEMA = Tab.CONSTRAINT_SCHEMA"
            stmt += ln + "RIGHT JOIN INFORMATION_SCHEMA.TABLES AS tbls"
            stmt += ln + "    ON Tab.TABLE_NAME = tbls.TABLE_NAME"
            stmt += ln + "    AND Tab.CONSTRAINT_SCHEMA = tbls.TABLE_SCHEMA"
            stmt += ln + "    AND Tab.Constraint_Type = 'PRIMARY KEY'"
            if metadata_exists:
                stmt += ln + "LEFT JOIN {schema}.T_ILI2DB_TABLE_PROP AS p"
                stmt += ln + "    ON p.tablename = tbls.TABLE_NAME"
                stmt += ln + "    AND p.tag = 'ch.ehi.ili2db.tableKind'"
                stmt += ln + "LEFT JOIN {schema}.T_ILI2DB_TABLE_PROP AS alias"
                stmt += ln + "    ON alias.tablename = tbls.TABLE_NAME"
                stmt += ln + "    AND alias.tag = 'ch.ehi.ili2db.dispName'"
                stmt += ln + "LEFT JOIN {schema}.t_ili2db_classname AS c"
                stmt += ln + "    ON tbls.TABLE_NAME = c.sqlname"
                stmt += ln + "LEFT JOIN {schema}.t_ili2db_attrname AS attrs"
                stmt += ln + "    ON c.iliname = attrs.iliname"
            stmt += ln + "LEFT JOIN INFORMATION_SCHEMA.COLUMNS AS clm"
            stmt += ln + "    ON clm.TABLE_NAME = tbls.TABLE_NAME"
            stmt += ln + "    AND clm.TABLE_SCHEMA = tbls.TABLE_SCHEMA"
            stmt += ln + "    AND clm.DATA_TYPE = 'geometry'"
            if metadata_exists:
                stmt += ln + "LEFT JOIN {schema}.T_ILI2DB_COLUMN_PROP AS tsrid"
                stmt += ln + "    ON tbls.TABLE_NAME = tsrid.tablename"
                stmt += ln + "    AND clm.COLUMN_NAME = tsrid.columnname"
                stmt += ln + "    AND tsrid.tag='ch.ehi.ili2db.srid'"
                stmt += ln + "LEFT JOIN {schema}.T_ILI2DB_COLUMN_PROP AS tgeomtype"
                stmt += ln + "    ON tbls.TABLE_NAME = tgeomtype.tablename"
                stmt += ln + "    AND clm.COLUMN_NAME = tgeomtype.columnname"
                stmt += ln + "    AND tgeomtype.tag= 'ch.ehi.ili2db.geomType'"
            stmt += (
                ln
                + "WHERE tbls.TABLE_TYPE = 'BASE TABLE' AND tbls.TABLE_SCHEMA = '{schema}'"
            )
            stmt = stmt.format(schema=self.schema)

            if not metadata_exists:
                stmt = self._def_cursor(stmt)

            cur = self.conn.cursor()
            cur.execute(stmt)

            if cur.description:
                columns = [column[0] for column in cur.description]

                for row in cur.fetchall():
                    my_rec = dict(zip(columns, row))
                    my_rec["srid"] = int(my_rec["srid"]) if my_rec["srid"] else None
                    my_rec["type"] = my_rec["simple_type"]
                    res.append(my_rec)

        return res

    def _def_cursor(self, query):
        cursor = """
            DECLARE @schemaname VARCHAR(1000)
            DECLARE @tablename VARCHAR(1000)
            DECLARE @primary_key VARCHAR(1000)
            DECLARE @geometry_column VARCHAR(1000)
            DECLARE @query NVARCHAR(MAX)
            DECLARE @row_counter NVARCHAR(MAX)
            DECLARE @separator NVARCHAR(200)
            declare @full_tabname nvarchar(300)
            declare @count int
            set @query = ''
            set @row_counter = ''
            set @separator = ''

            DECLARE db_cursor CURSOR FOR {query}
            OPEN db_cursor
            FETCH NEXT FROM db_cursor INTO @schemaname, @tablename, @primary_key, @geometry_column
            WHILE @@FETCH_STATUS = 0
            BEGIN
                if @schemaname is null	set @full_tabname = @tablename else set @full_tabname = concat(@schemaname,'.', @tablename)
                if @schemaname is not null set @schemaname = CONCAT('''', @schemaname, '''') else set @schemaname = 'NULL'
                if @primary_key is not null set @primary_key = CONCAT('''', @primary_key, '''') else set @primary_key = 'NULL'
                set @tablename = CONCAT('''', @tablename, '''')

                if @geometry_column is not null begin -- table has geometry
                    select @row_counter = concat('SELECT @C=count(concat(',@geometry_column,'.STSrid,', @geometry_column,'.STGeometryType()))', ' from ', @full_tabname)
                    execute sp_executesql @row_counter, N'@C INT OUTPUT', @C=@count OUTPUT

                    if @count > 0 begin -- table containts geometry data, geometry types are got from data
                        set @query = concat('SELECT distinct '
                        , @schemaname, ' as schemaname,'
                        , @tablename, ' as tablename,'
                        , @primary_key, ' as primary_key,'
                        , '''', @geometry_column, ''' as geometry_column,'
                        , @geometry_column,'.STSrid as srid,'
                        , @geometry_column,'.STGeometryType() as simple_type'
                        , ' from ', @full_tabname, @separator, @query)
                    end else begin -- otherwise, geometry type is set null
                        set @query = concat('SELECT '
                        , @schemaname, ' as schemaname,'
                        , @tablename, ' as tablename,'
                        , @primary_key, ' as primary_key,'
                        , '''', @geometry_column, ''' as geometry_column,'
                        , 'NULL as srid, NULL as simple_type'
                        , @separator, @query)
                    end
                end	else begin -- table does not have geometry
                    set @query = concat('SELECT '
                        , @schemaname, ' as schemaname,'
                        , @tablename, ' as tablename,'
                        , @primary_key, ' as primary_key,'
                        , N'NULL as geometry_column'
                        , N', NULL as srid, NULL as simple_type'
                        , @separator, @query)
                end
                set @separator = ' union '
                FETCH NEXT FROM db_cursor INTO @schemaname, @tablename, @primary_key, @geometry_column
            END
            CLOSE db_cursor
            DEALLOCATE db_cursor
            execute sp_executesql @query """.format(
            query=query
        )

        return cursor

    def get_meta_attrs_info(self):
        if not self._table_exists(METAATTRS_TABLE):
            return []

        result = []

        if self.schema:
            cur = self.conn.cursor()
            cur.execute(
                """
                        SELECT *
                        FROM {schema}.{metaattrs_table};
            """.format(
                    schema=self.schema,
                    metaattrs_table=METAATTRS_TABLE,
                )
            )

            result = self._get_dict_result(cur)

        return result

    def get_meta_attrs(self, ili_name):
        if not self._table_exists(METAATTRS_TABLE):
            return []

        result = []

        if self.schema:
            cur = self.conn.cursor()
            cur.execute(
                """
                        SELECT
                          attr_name,
                          attr_value
                        FROM {schema}.{metaattrs_table}
                        WHERE ilielement='{ili_name}';
            """.format(
                    schema=self.schema,
                    metaattrs_table=METAATTRS_TABLE,
                    ili_name=ili_name,
                )
            )

            result = self._get_dict_result(cur)

        return result

    def get_fields_info(self, table_name):
        res = []
        # Get all fields for this table
        if self.schema:
            metadata_exists = self.metadata_exists()
            metaattrs_exists = self._table_exists(METAATTRS_TABLE)
            ln = "\n"
            stmt = ""

            # TODO description column is missing
            stmt += ln + "SELECT"
            stmt += ln + "     c.column_name"
            stmt += (
                ln
                + "    , case c.data_type when 'decimal' then 'numeric' else c.DATA_TYPE end as data_type"
            )
            stmt += ln + "    , c.numeric_scale"
            if metadata_exists:
                stmt += ln + "    , unit.setting AS unit"
                stmt += ln + "    , txttype.setting AS texttype"
                stmt += ln + "    , alias.setting AS column_alias"
                stmt += ln + "    , full_name.iliname AS fully_qualified_name"
                stmt += ln + "    , enum_domain.setting AS enum_domain"
                stmt += ln + "    , oid_domain.setting AS oid_domain"
                if metaattrs_exists:
                    stmt += (
                        ln
                        + "    , COALESCE(CAST(form_order.attr_value AS int), 999) AS attr_order"
                        + "    , attr_mapping.attr_value AS attr_mapping"
                    )
            stmt += ln + "    , null AS comment"
            stmt += ln + "FROM INFORMATION_SCHEMA.COLUMNS AS c"
            if metadata_exists:
                stmt += ln + "LEFT JOIN {schema}.t_ili2db_column_prop unit"
                stmt += ln + "    ON c.table_name = unit.tablename"
                stmt += ln + "    AND c.column_name = unit.columnname"
                stmt += ln + "    AND unit.tag = 'ch.ehi.ili2db.unit'"
                stmt += ln + "LEFT JOIN {schema}.t_ili2db_column_prop txttype"
                stmt += ln + "    ON c.table_name = txttype.tablename"
                stmt += ln + "    AND c.column_name = txttype.columnname"
                stmt += ln + "    AND txttype.tag = 'ch.ehi.ili2db.textKind'"
                stmt += ln + "LEFT JOIN {schema}.t_ili2db_column_prop alias"
                stmt += ln + "    ON c.table_name = alias.tablename"
                stmt += ln + "    AND c.column_name = alias.columnname"
                stmt += ln + "    AND alias.tag = 'ch.ehi.ili2db.dispName'"
                stmt += ln + "LEFT JOIN {schema}.t_ili2db_attrname full_name"
                stmt += ln + "    ON full_name.{}='{{table}}'".format(
                    "owner" if self.ili_version() == 3 else "colowner"
                )
                stmt += ln + "    AND c.column_name=full_name.sqlname"
                stmt += ln + "LEFT JOIN {schema}.t_ili2db_column_prop enum_domain"
                stmt += ln + "    ON c.table_name = enum_domain.tablename"
                stmt += ln + "    AND c.column_name = enum_domain.columnname"
                stmt += ln + "    AND enum_domain.tag = 'ch.ehi.ili2db.enumDomain'"
                stmt += ln + "LEFT JOIN {schema}.t_ili2db_column_prop oid_domain"
                stmt += ln + "    ON c.table_name = oid_domain.tablename"
                stmt += (
                    ln + "    AND LOWER(c.column_name) = LOWER(oid_domain.columnname)"
                )
                stmt += ln + "    AND oid_domain.tag = 'ch.ehi.ili2db.oidDomain'"
                if metaattrs_exists:
                    stmt += ln + "LEFT JOIN {schema}.t_ili2db_meta_attrs form_order"
                    stmt += ln + "    ON full_name.iliname=form_order.ilielement AND"
                    stmt += ln + "    form_order.attr_name='form_order'"
                    stmt += ln + "LEFT JOIN {schema}.t_ili2db_meta_attrs attr_mapping"
                    stmt += ln + "    ON full_name.iliname=attr_mapping.ilielement AND"
                    stmt += ln + "    attr_mapping.attr_name='ili2db.mapping'"
            stmt += ln + "WHERE TABLE_NAME = '{table}' AND TABLE_SCHEMA = '{schema}'"
            if metadata_exists and metaattrs_exists:
                stmt += ln + "ORDER BY attr_order;"
            stmt = stmt.format(schema=self.schema, table=table_name)

            cur = self.conn.cursor()
            cur.execute(stmt)
            res = self._get_dict_result(cur)
        return res

    def get_min_max_info(self, table_name):
        result = {}
        # Get all 'c'heck constraints for this table
        if self.schema:
            constraints_cur = self.conn.cursor()
            # this query returns the clause check intervals that are similar to:
            #       ([numero_pisos]>=(1) AND [numero_pisos]<=(100))
            query = """
                SELECT CHECK_CLAUSE
                FROM
                    INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc INNER JOIN
                    INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE c
                        ON cc.CONSTRAINT_NAME = c.CONSTRAINT_NAME
                        AND cc.CONSTRAINT_SCHEMA = c.CONSTRAINT_SCHEMA
                WHERE
                    cc.CONSTRAINT_SCHEMA = '{schema}'
                    AND TABLE_NAME = '{table}'
                """.format(
                schema=self.schema, table=table_name
            )

            constraints_cur.execute(query)

            # Create a mapping in the form of
            #
            # fieldname: (min, max)
            constraint_mapping = dict()
            for constraint in constraints_cur:
                # The regex takes the query results (e.g. '([numero_pisos]>=(1) AND [numero_pisos]<=(100))')
                # and gets the field name (regex-group 1), the minimum value (regex-group 2),
                # and the maximum value (regex-group 4) of the field for each register
                m = re.match(
                    r"\(\[(.*)\]>=\(([+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\) AND \[(.*)\]<=\(([+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\)\)",
                    constraint[0],
                )

                if m:
                    constraint_mapping[m.group(1)] = (m.group(2), m.group(4))

            result = constraint_mapping

        return result

    def get_relations_info(self, filter_layer_list=[]):
        result = []

        if self.schema:
            cur = self.conn.cursor()
            schema_where1 = (
                "AND KCU1.CONSTRAINT_SCHEMA = '{}'".format(self.schema)
                if self.schema
                else ""
            )
            schema_where2 = (
                "AND KCU2.CONSTRAINT_SCHEMA = '{}'".format(self.schema)
                if self.schema
                else ""
            )
            filter_layer_where = ""
            if filter_layer_list:
                filter_layer_where = "AND KCU1.TABLE_NAME IN ('{}')".format(
                    "','".join(filter_layer_list)
                )

            strength_field = ""
            strength_join = ""
            cardinality_max_field = ""
            cardinality_max_join = ""
            if self._table_exists(METAATTRS_TABLE):
                strength_field = ",META_ATTRS.attr_value as strength"
                strength_join = """
                LEFT JOIN {schema}.t_ili2db_attrname AS ATTRNAME
                    ON ATTRNAME.sqlname = KCU1.COLUMN_NAME AND ATTRNAME.{colowner} = KCU1.TABLE_NAME AND ATTRNAME.target = KCU2.TABLE_NAME
                LEFT JOIN {schema}.t_ili2db_meta_attrs AS META_ATTRS
                    ON META_ATTRS.ilielement = ATTRNAME.iliname AND META_ATTRS.attr_name = 'ili2db.ili.assocKind'
                    """.format(
                    schema=self.schema,
                    colowner="owner" if self.ili_version() == 3 else "colowner",
                )

                cardinality_max_field = (
                    ",META_ATTRS_CARDINALITY.attr_value as cardinality_max"
                )
                cardinality_max_join = """
                LEFT JOIN {schema}.t_ili2db_attrname AS ATTRNAME_CARDINALITY
                    ON ATTRNAME_CARDINALITY.sqlname = KCU1.COLUMN_NAME AND ATTRNAME_CARDINALITY.{colowner} = KCU1.TABLE_NAME AND ATTRNAME_CARDINALITY.target = KCU2.TABLE_NAME
                LEFT JOIN {schema}.t_ili2db_meta_attrs AS META_ATTRS_CARDINALITY
                    ON META_ATTRS_CARDINALITY.ilielement = ATTRNAME_CARDINALITY.iliname AND META_ATTRS_CARDINALITY.attr_name = 'ili2db.ili.attrCardinalityMax'
                    """.format(
                    schema=self.schema,
                    colowner="owner" if self.ili_version() == 3 else "colowner",
                )

            query = """
                SELECT
                    KCU1.CONSTRAINT_NAME AS constraint_name
                    ,KCU1.TABLE_NAME AS referencing_table
                    ,KCU1.COLUMN_NAME AS referencing_column
                    ,KCU2.CONSTRAINT_SCHEMA AS constraint_schema
                    ,KCU2.TABLE_NAME AS referenced_table
                    ,KCU2.COLUMN_NAME AS referenced_column
                    ,KCU1.ORDINAL_POSITION AS ordinal_position
                    {strength_field}
                    {cardinality_max_field}
                FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS RC

                INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU1
                    ON KCU1.CONSTRAINT_CATALOG = RC.CONSTRAINT_CATALOG
                    AND KCU1.CONSTRAINT_SCHEMA = RC.CONSTRAINT_SCHEMA
                    AND KCU1.CONSTRAINT_NAME = RC.CONSTRAINT_NAME

                INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU2
                    ON KCU2.CONSTRAINT_CATALOG = RC.UNIQUE_CONSTRAINT_CATALOG
                    AND KCU2.CONSTRAINT_SCHEMA = RC.UNIQUE_CONSTRAINT_SCHEMA
                    AND KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME
                    AND KCU2.ORDINAL_POSITION = KCU1.ORDINAL_POSITION
                {strength_join}
                {cardinality_max_join}

                WHERE 1=1 {schema_where1} {schema_where2} {filter_layer_where}
                order by constraint_name, ordinal_position
                """.format(
                schema_where1=schema_where1,
                schema_where2=schema_where2,
                filter_layer_where=filter_layer_where,
                strength_field=strength_field,
                strength_join=strength_join,
                cardinality_max_field=cardinality_max_field,
                cardinality_max_join=cardinality_max_join,
            )
            cur.execute(query)
            result = self._get_dict_result(cur)

        return result

    def get_iliname_dbname_mapping(self, sqlnames=list()):
        """Note: the parameter sqlnames is only used for ili2db version 3 relation creation"""
        result = {}
        # Map domain ili name with its correspondent mssql name
        if self.schema and self.metadata_exists():
            cur = self.conn.cursor()

            where = ""
            if sqlnames:
                names = "'" + "','".join(sqlnames) + "'"
                where = "WHERE sqlname IN ({})".format(names)

            cur.execute(
                """SELECT iliname, sqlname
                           FROM {schema}.t_ili2db_classname
                           {where}
                        """.format(
                    schema=self.schema, where=where
                )
            )

            result = self._get_dict_result(cur)

        return result

    def get_models(self):
        # Get MODELS
        if self.schema:
            cur = self.conn.cursor()

            cur.execute(
                """SELECT distinct split_part(iliname,'.',1) as modelname
                            FROM {schema}.t_ili2db_trafo""".format(
                    schema=self.schema
                )
            )

            models = cur.fetchall()

            cur.execute(
                """SELECT modelname, content
                           FROM {schema}.t_ili2db_model
                        """.format(
                    schema=self.schema
                )
            )

            contents = cur.fetchall()

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

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        result = {}
        if self.schema:
            cur = self.conn.cursor()
            class_names = (
                "'"
                + "','".join(list(models_info.keys()) + list(extended_classes.keys()))
                + "'"
            )
            cur.execute(
                """SELECT iliname, sqlname
                           FROM {schema}.t_ili2db_classname
                           WHERE iliname IN ({class_names})
                        """.format(
                    schema=self.schema, class_names=class_names
                )
            )
            result = self._get_dict_result(cur)
        return result

    def get_attrili_attrdb_mapping(self, attrs_list):
        result = {}
        if self.schema:
            cur = self.conn.cursor()
            attr_names = "'" + "','".join(attrs_list) + "'"

            cur.execute(
                """SELECT iliname, sqlname, owner
                           FROM {schema}.t_ili2db_attrname
                           WHERE iliname IN ({attr_names})
                        """.format(
                    schema=self.schema, attr_names=attr_names
                )
            )
            result = self._get_dict_result(cur)
        return result

    def get_attrili_attrdb_mapping_by_owner(self, owners):
        result = {}
        if self.schema:
            cur = self.conn.cursor()
            owner_names = "'" + "','".join(owners) + "'"
            cur.execute(
                """SELECT iliname, sqlname, owner
                           FROM {schema}.t_ili2db_attrname
                           WHERE owner IN ({owner_names})
                        """.format(
                    schema=self.schema, owner_names=owner_names
                )
            )
            result = self._get_dict_result(cur)
        return result

    def _get_dict_result(self, cur):
        columns = [column[0] for column in cur.description]

        res = []
        for row in cur.fetchall():
            my_rec = dict(zip(columns, row))
            res.append(my_rec)

        return res

    def ili_version(self):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT count(COLUMN_NAME)
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='{schema}'
	AND(TABLE_NAME='t_ili2db_attrname' OR TABLE_NAME='t_ili2db_model')
                       AND(COLUMN_NAME='owner' OR COLUMN_NAME='file')""".format(
                schema=self.schema
            )
        )

        res = cur.fetchone()[0]
        print(res)
        if res > 0:
            self.new_message.emit(
                Qgis.Warning,
                "DB schema created with ili2db version 3. Better use version 4.",
            )
            return 3
        else:
            return 4

    def get_basket_handling(self):
        if self.schema and self._table_exists(SETTINGS_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """SELECT setting
                            FROM {schema}.{table}
                            WHERE tag = ?
                            """.format(
                    schema=self.schema, table=SETTINGS_TABLE
                ),
                ("ch.ehi.ili2db.BasketHandling",),
            )
            content = cur.fetchone()
            if content:
                return content[0] == "readWrite"
        return False

    def get_baskets_info(self):
        result = {}
        if self.schema and self._table_exists(BASKET_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """SELECT b.t_id as basket_t_id,
                            b.t_ili_tid as basket_t_ili_tid,
                            b.topic as topic,
                            d.t_id as dataset_t_id,
                            d.datasetname as datasetname from {schema}.{basket_table} b
                            JOIN {schema}.{dataset_table} d
                            ON b.dataset = d.t_id
                        """.format(
                    schema=self.schema,
                    basket_table=BASKET_TABLE,
                    dataset_table=DATASET_TABLE,
                )
            )
            result = self._get_dict_result(cur)
        return result

    def get_datasets_info(self):
        result = {}
        if self.schema and self._table_exists(DATASET_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """SELECT t_id, datasetname
                           FROM {schema}.{dataset_table}
                        """.format(
                    schema=self.schema, dataset_table=DATASET_TABLE
                )
            )
            result = self._get_dict_result(cur)
        return result

    def create_dataset(self, datasetname):
        if self.schema and self._table_exists(DATASET_TABLE):
            cur = self.conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO {schema}.{dataset_table} VALUES (NEXT VALUE FOR {schema}.{sequence}, ?)
                    """.format(
                        schema=self.schema,
                        sequence="t_ili2db_seq",
                        dataset_table=DATASET_TABLE,
                    ),
                    datasetname,
                )
                self.conn.commit()
                return True, self.tr('Successfully created dataset "{}".').format(
                    datasetname
                )
            except pyodbc.errors.UniqueViolation as e:
                return False, self.tr('Dataset with name "{}" already exists.').format(
                    datasetname
                )
        return False, self.tr('Could not create dataset "{}".').format(datasetname)

    def rename_dataset(self, tid, datasetname):
        if self.schema and self._table_exists(DATASET_TABLE):
            cur = self.conn.cursor()
            try:
                cur.execute(
                    """
                    UPDATE {schema}.{dataset_table} SET datasetname = ? WHERE {tid_name} = {tid}
                    """.format(
                        schema=self.schema,
                        dataset_table=DATASET_TABLE,
                        tid_name=self.tid,
                        tid=tid,
                    ),
                    datasetname,
                )
                self.conn.commit()
                return True, self.tr('Successfully created dataset "{}".').format(
                    datasetname
                )
            except pyodbc.errors.UniqueViolation as e:
                return False, self.tr('Dataset with name "{}" already exists.').format(
                    datasetname
                )
        return False, self.tr('Could not create dataset "{}".').format(datasetname)

    def get_topics_info(self):
        result = {}
        if self.schema and self._table_exists("t_ili2db_classname"):
            cur = self.conn.cursor()
            cur.execute(
                """
                    SELECT DISTINCT PARSENAME(cn.iliname,1) as model,
                    PARSENAME(cn.iliname,2) as topic
                    FROM {schema}.t_ili2db_classname as cn
                    JOIN {schema}.t_ili2db_table_prop as tp
                    ON cn.sqlname = tp.tablename
					WHERE PARSENAME(cn.iliname,3) != '' and tp.setting != 'ENUM'
                """.format(
                    schema=self.schema
                )
            )
            result = self._get_dict_result(cur)
        return result

    def create_basket(self, dataset_tid, topic):
        if self.schema and self._table_exists(BASKET_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """
                    SELECT * FROM {schema}.{basket_table}
                    WHERE dataset = {dataset_tid} and topic = '{topic}'
                """.format(
                    schema=self.schema,
                    basket_table=BASKET_TABLE,
                    dataset_tid=dataset_tid,
                    topic=topic,
                )
            )
            if cur.fetchone():
                return False, self.tr('Basket for topic "{}" already exists.').format(
                    topic
                )
            try:
                cur.execute(
                    """
                    INSERT INTO {schema}.{basket_table} ({tid_name}, dataset, topic, {tilitid_name}, attachmentkey )
                    VALUES (NEXT VALUE FOR {schema}.{sequence}, {dataset_tid}, '{topic}', NEWID(), 'Qgis Model Baker')
                """.format(
                        schema=self.schema,
                        sequence="t_ili2db_seq",
                        tid_name=self.tid,
                        tilitid_name=self.tilitid,
                        basket_table=BASKET_TABLE,
                        dataset_tid=dataset_tid,
                        topic=topic,
                    )
                )
                self.conn.commit()
                return True, self.tr(
                    'Successfully created basket for topic "{}".'
                ).format(topic)
            except pyodbc.errors.Error as e:
                error_message = " ".join(e.args)
                return False, self.tr(
                    'Could not create basket for topic "{}": {}'
                ).format(topic, error_message)
        return False, self.tr('Could not create basket for topic "{}".').format(topic)

    def get_tid_handling(self):
        if self.schema and self._table_exists(SETTINGS_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """SELECT setting
                            FROM {schema}.{table}
                            WHERE tag = ?
                            """.format(
                    schema=self.schema, table=SETTINGS_TABLE
                ),
                ("ch.ehi.ili2db.TidHandling",),
            )
            content = cur.fetchone()
            if content:
                return content[0] == "property"
        return False

    def get_ili2db_settings(self):
        result = {}
        if self._table_exists(SETTINGS_TABLE):
            cur = self.conn.cursor()
            cur.execute(
                """SELECT tag, setting
                            FROM {schema}.{table}
                            """.format(
                    schema=self.schema, table=SETTINGS_TABLE
                )
            )
            result = self._get_dict_result(cur)
        return result
