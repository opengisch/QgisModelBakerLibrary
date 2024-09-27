
    SELECT distinct
     tbls.TABLE_SCHEMA AS schemaname
    , tbls.TABLE_NAME AS tablename
    , Col.Column_Name AS primary_key
    , clm.COLUMN_NAME AS geometry_column
    , tsrid.setting AS srid
    , p.setting AS kind_settings
    , alias.setting AS table_alias
    , left(c.iliname, charindex('.', c.iliname)-1) AS model
    , c.iliname AS ili_name
    , STUFF(
       (SELECT ';' + CAST(cp.setting AS VARCHAR(MAX))
        FROM optimal_polymorph_manuel.t_ili2db_column_prop cp
        WHERE tbls.table_name = cp.tablename
            AND clm.COLUMN_NAME = cp.columnname
            AND cp.tag IN
                ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
        order by case cp.tag WHEN 'ch.ehi.ili2db.c1Min' THEN 1
            WHEN 'ch.ehi.ili2db.c2Min' THEN 2
            WHEN 'ch.ehi.ili2db.c1Max' THEN 3
            WHEN 'ch.ehi.ili2db.c2Max' THEN 4
            END
        FOR XML PATH(''),TYPE).value('(./text())[1]','VARCHAR(MAX)'),1,1,''
        ) AS extent
    , ( SELECT CASE MAX(CHARINDEX('.',cp.setting)) WHEN 0 THEN 0 ELSE MAX( LEN(cp.setting) -  CHARINDEX('.',cp.setting) ) END
        FROM optimal_polymorph_manuel.t_ili2db_column_prop cp
        WHERE tbls.table_name = cp.tablename
            AND clm.COLUMN_NAME = cp.columnname
            AND cp.tag IN
                ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
      ) AS coord_decimals
    , tgeomtype.setting AS simple_type
    , null AS formatted_type
    , attrs.sqlname AS attribute_name
  , CASE WHEN c.iliname IN (
                                        SELECT i.baseClass as base, base_names.class, extend_names.class, base_names.model, extend_names.model
                                        FROM optimal_polymorph_manuel.t_ili2db_inheritance i
                                        LEFT JOIN (
                                            SELECT fullname, model, topicclass, substring(topicclass, charindex('.',topicclass)+1, len(topicclass)) as class
                                            FROM (
                                                SELECT
                                                    thisClass as fullname,
                                                    substring(thisClass, 1, charindex('.', thisClass)-1) as model,
                                                    substring(thisClass, charindex('.', thisClass)+1, len(thisClass)) as topicclass
                                                FROM optimal_polymorph_manuel.t_ili2db_inheritance
                                            ) AS extended
                                        ) AS extend_names
                                        ON thisClass = extend_names.fullname
                                        LEFT JOIN (
                                            SELECT fullname, model, topicclass, substring(topicclass, charindex('.', topicclass)+1, len(topicclass)) as class
                                            FROM (
                                                SELECT
                                                thisClass as fullname,
                                                substring(thisClass, 1, charindex('.',thisClass)-1) as model,
                                                substring(thisClass, charindex('.', thisClass)+1, len(thisClass)) as topicclass
                                                FROM optimal_polymorph_manuel.t_ili2db_inheritance
                                            ) AS topic_level_name
                                        ) AS base_names
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
                                            (SELECT MAX(count) FROM (SELECT COUNT(baseClass) AS count FROM optimal_polymorph_manuel.t_ili2db_inheritance JOIN (
                                            SELECT fullname, model, topicclass, substring(topicclass, charindex('.', topicclass)+1, len(topicclass)) as class
                                            FROM (
                                                SELECT
                                                thisClass as fullname,
                                                substring(thisClass, 0, charindex('.',thisClass)-1) as model,
                                                substring(thisClass, charindex('.', thisClass)+1, len(thisClass)) as topicclass
                                                FROM optimal_polymorph_manuel.t_ili2db_inheritance
                                            ) AS topic_level_name
                                        ) AS extend_names ON thisClass = extend_names.fullname WHERE baseClass = i.baseClass GROUP BY baseClass, extend_names.model) AS counts )>1
                                        )
                                    )
                                    THEN 0 ELSE 1 END AS relevance

FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS Tab
INNER JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS Col
    ON Col.Constraint_Name = Tab.Constraint_Name
    AND Col.Table_Name = Tab.Table_Name
    AND Col.CONSTRAINT_SCHEMA = Tab.CONSTRAINT_SCHEMA
RIGHT JOIN INFORMATION_SCHEMA.TABLES AS tbls
    ON Tab.TABLE_NAME = tbls.TABLE_NAME
    AND Tab.CONSTRAINT_SCHEMA = tbls.TABLE_SCHEMA
    AND Tab.Constraint_Type = 'PRIMARY KEY'
LEFT JOIN optimal_polymorph_manuel.T_ILI2DB_TABLE_PROP AS p
    ON p.tablename = tbls.TABLE_NAME
    AND p.tag = 'ch.ehi.ili2db.tableKind'
LEFT JOIN optimal_polymorph_manuel.T_ILI2DB_TABLE_PROP AS alias
    ON alias.tablename = tbls.TABLE_NAME
    AND alias.tag = 'ch.ehi.ili2db.dispName'
LEFT JOIN optimal_polymorph_manuel.t_ili2db_classname AS c
    ON tbls.TABLE_NAME = c.sqlname
LEFT JOIN optimal_polymorph_manuel.t_ili2db_attrname AS attrs
    ON c.iliname = attrs.iliname
LEFT JOIN INFORMATION_SCHEMA.COLUMNS AS clm
    ON clm.TABLE_NAME = tbls.TABLE_NAME
    AND clm.TABLE_SCHEMA = tbls.TABLE_SCHEMA
    AND clm.DATA_TYPE = 'geometry'
LEFT JOIN optimal_polymorph_manuel.T_ILI2DB_COLUMN_PROP AS tsrid
    ON tbls.TABLE_NAME = tsrid.tablename
    AND clm.COLUMN_NAME = tsrid.columnname
    AND tsrid.tag='ch.ehi.ili2db.srid'
LEFT JOIN optimal_polymorph_manuel.T_ILI2DB_COLUMN_PROP AS tgeomtype
    ON tbls.TABLE_NAME = tgeomtype.tablename
    AND clm.COLUMN_NAME = tgeomtype.columnname
    AND tgeomtype.tag= 'ch.ehi.ili2db.geomType'
WHERE tbls.TABLE_TYPE = 'BASE TABLE' AND tbls.TABLE_SCHEMA = 'optimal_polymorph_manuel'

SELECT distinct
     tbls.TABLE_SCHEMA AS schemaname
    , tbls.TABLE_NAME AS tablename
    , Col.Column_Name AS primary_key
    , clm.COLUMN_NAME AS geometry_column
    , tsrid.setting AS srid
    , p.setting AS kind_settings
    , alias.setting AS table_alias
    , left(c.iliname, charindex('.', c.iliname)-1) AS model
    , c.iliname AS ili_name
    , STUFF(
       (SELECT ';' + CAST(cp.setting AS VARCHAR(MAX))
        FROM optimal_polymorph_manuel.t_ili2db_column_prop cp
        WHERE tbls.table_name = cp.tablename
            AND clm.COLUMN_NAME = cp.columnname
            AND cp.tag IN
                ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
        order by case cp.tag WHEN 'ch.ehi.ili2db.c1Min' THEN 1
            WHEN 'ch.ehi.ili2db.c2Min' THEN 2
            WHEN 'ch.ehi.ili2db.c1Max' THEN 3
            WHEN 'ch.ehi.ili2db.c2Max' THEN 4
            END
        FOR XML PATH(''),TYPE).value('(./text())[1]','VARCHAR(MAX)'),1,1,''
        ) AS extent
    , ( SELECT CASE MAX(CHARINDEX('.',cp.setting)) WHEN 0 THEN 0 ELSE MAX( LEN(cp.setting) -  CHARINDEX('.',cp.setting) ) END
        FROM optimal_polymorph_manuel.t_ili2db_column_prop cp
        WHERE tbls.table_name = cp.tablename
            AND clm.COLUMN_NAME = cp.columnname
            AND cp.tag IN
                ('ch.ehi.ili2db.c1Min', 'ch.ehi.ili2db.c2Min',
                'ch.ehi.ili2db.c1Max', 'ch.ehi.ili2db.c2Max')
      ) AS coord_decimals
    , tgeomtype.setting AS simple_type
    , null AS formatted_type
    , attrs.sqlname AS attribute_name
  , CASE WHEN c.iliname IN (
                                        SELECT i.baseClass as base
                                        FROM optimal_polymorph_manuel.t_ili2db_inheritance i
                                        LEFT JOIN (
                                            SELECT fullname, model, topicclass, substring(topicclass, charindex('.',topicclass)+1, len(topicclass)) as class
                                            FROM (
                                                SELECT
                                                    thisClass as fullname,
                                                    substring(thisClass, 1, charindex('.', thisClass)-1) as model,
                                                    substring(thisClass, charindex('.', thisClass)+1, len(thisClass)) as topicclass
                                                FROM optimal_polymorph_manuel.t_ili2db_inheritance
                                            ) AS extended
                                        ) AS extend_names
                                        ON thisClass = extend_names.fullname
                                        LEFT JOIN (
                                            SELECT fullname, model, topicclass, substring(topicclass, charindex('.', topicclass)+1, len(topicclass)) as class
                                            FROM (
                                                SELECT
                                                thisClass as fullname,
                                                substring(thisClass, 0, charindex('.',thisClass)-1) as model,
                                                substring(thisClass, charindex('.', thisClass)+1, len(thisClass)) as topicclass
                                                FROM optimal_polymorph_manuel.t_ili2db_inheritance
                                            ) AS topic_level_name
                                        ) AS base_names
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
                                            (SELECT MAX(count) FROM (SELECT COUNT(baseClass) AS count FROM optimal_polymorph_manuel.t_ili2db_inheritance JOIN (
                                            SELECT fullname, model, topicclass, substring(topicclass, charindex('.', topicclass)+1, len(topicclass)) as class
                                            FROM (
                                                SELECT
                                                thisClass as fullname,
                                                substring(thisClass, 0, charindex('.',thisClass)-1) as model,
                                                substring(thisClass, charindex('.', thisClass)+1, len(thisClass)) as topicclass
                                                FROM optimal_polymorph_manuel.t_ili2db_inheritance
                                            ) AS topic_level_name
                                        ) AS extend_names ON thisClass = extend_names.fullname WHERE baseClass = i.baseClass GROUP BY baseClass, extend_names.model) AS counts )>1
                                        )
                                    )
                                    THEN 0 ELSE 1 END AS relevance

FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS Tab
INNER JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS Col
    ON Col.Constraint_Name = Tab.Constraint_Name
    AND Col.Table_Name = Tab.Table_Name
    AND Col.CONSTRAINT_SCHEMA = Tab.CONSTRAINT_SCHEMA
RIGHT JOIN INFORMATION_SCHEMA.TABLES AS tbls
    ON Tab.TABLE_NAME = tbls.TABLE_NAME
    AND Tab.CONSTRAINT_SCHEMA = tbls.TABLE_SCHEMA
    AND Tab.Constraint_Type = 'PRIMARY KEY'
LEFT JOIN optimal_polymorph_manuel.T_ILI2DB_TABLE_PROP AS p
    ON p.tablename = tbls.TABLE_NAME
    AND p.tag = 'ch.ehi.ili2db.tableKind'
LEFT JOIN optimal_polymorph_manuel.T_ILI2DB_TABLE_PROP AS alias
    ON alias.tablename = tbls.TABLE_NAME
    AND alias.tag = 'ch.ehi.ili2db.dispName'
LEFT JOIN optimal_polymorph_manuel.t_ili2db_classname AS c
    ON tbls.TABLE_NAME = c.sqlname
LEFT JOIN optimal_polymorph_manuel.t_ili2db_attrname AS attrs
    ON c.iliname = attrs.iliname
LEFT JOIN INFORMATION_SCHEMA.COLUMNS AS clm
    ON clm.TABLE_NAME = tbls.TABLE_NAME
    AND clm.TABLE_SCHEMA = tbls.TABLE_SCHEMA
    AND clm.DATA_TYPE = 'geometry'
LEFT JOIN optimal_polymorph_manuel.T_ILI2DB_COLUMN_PROP AS tsrid
    ON tbls.TABLE_NAME = tsrid.tablename
    AND clm.COLUMN_NAME = tsrid.columnname
    AND tsrid.tag='ch.ehi.ili2db.srid'
LEFT JOIN optimal_polymorph_manuel.T_ILI2DB_COLUMN_PROP AS tgeomtype
    ON tbls.TABLE_NAME = tgeomtype.tablename
    AND clm.COLUMN_NAME = tgeomtype.columnname
    AND tgeomtype.tag= 'ch.ehi.ili2db.geomType'
WHERE tbls.TABLE_TYPE = 'BASE TABLE' AND tbls.TABLE_SCHEMA = 'optimal_polymorph_manuel'
