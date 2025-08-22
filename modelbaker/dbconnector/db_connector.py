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
import fnmatch

from qgis.PyQt.QtCore import QObject, pyqtSignal

from .config import BASKET_TABLES, IGNORED_ILI_ELEMENTS, IGNORED_SCHEMAS, IGNORED_TABLES


class DBConnector(QObject):
    """SuperClass for all DB connectors."""

    stdout = pyqtSignal(str)
    new_message = pyqtSignal(int, str)

    def __init__(self, uri, schema, parent=None):
        QObject.__init__(self, parent)
        self.QGIS_DATE_TYPE = "date"
        self.QGIS_TIME_TYPE = "time"
        self.QGIS_DATE_TIME_TYPE = "datetime"
        self.iliCodeName = ""  # For Domain-Class relations, specific for each DB
        self.tid = ""  # For BAG OF config and basket handling, specific for each DB
        self.tilitid = ""  # For basket handling, specific for each DB
        self.dispName = ""  # For BAG OF config, specific for each DB
        self.basket_table_name = ""  # For basket handling, specific for each DB
        self.dataset_table_name = ""  # For basket handling, specific for each DB
        self._lang = ""  # Preferred tr language for table/column info (2 characters)

    def get_provider_specific_names(self):
        """
        Returns a dictionary of the provider-specific names defined in the initialization of the derived classes.
        """
        return {
            "tid_name": self.tid,
            "tilitid_name": self.tilitid,
            "attachmentkey_name": self.attachmentKey,
            "dispname_name": self.dispName,
            "baskettable_name": self.basket_table_name,
            "datasettable_name": self.dataset_table_name,
        }

    def map_data_types(self, data_type):
        """Map provider date/time types to QGIS date/time types"""
        return None

    def db_or_schema_exists(self):
        """Whether the DB (for GPKG) or schema (for PG) exists or not."""
        raise NotImplementedError

    def create_db_or_schema(self, usr):
        """Create the DB (for GPKG) or schema (for PG)"""
        raise NotImplementedError

    def metadata_exists(self):
        """Whether t_ili2db_table_prop table exists or not.
        In other words... Does the DB/Schema hold an INTERLIS model?
        """
        return False

    def get_tables_info(self):
        """
        Info about tables found in the database (or database schema).

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                schemaname
                tablename
                primary_key
                geometry_column
                srid
                type  (Geometry Type)
                kind_settings
                ili_name
                extent [a string: "xmin;ymin;xmax;ymax"]
                table_alias
                model
                relevance
                base_class
        """
        return []

    def get_meta_attrs_info(self):
        """
        Info about meta attributes

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                ilielement
                attr_name
                attr_value
        """
        raise NotImplementedError

    def get_meta_attr(self, ili_name):
        """
        Info about meta attributes of a given ili element

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                attr_name
                attr_value
        """
        return []

    def get_fields_info(self, table_name):
        """
        Info about fields of a given table in the database.

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                column_name
                data_type
                comment
                unit
                texttype
                column_alias
                enum_domain
                oid_domain
                fully_qualified_name
        """
        return []

    def get_min_max_info(self, table_name):
        """
        Info about range constraints found in a given table.

        Return:
            Dictionary with keys corresponding to column names and values
            corresponding to tuples in the form (min_value, max_value)
        """
        return {}

    def get_value_map_info(self, table_name):
        """
        Info about value map constraints found in a given table.

        Return:
            Dictionary with keys corresponding to column names and values
            with lists of allowed values
        """
        return {}

    def get_t_type_map_info(self, table_name):
        """
        Info about available types of a given smart1-inherited table.

        Return:
            Dictionary with keys corresponding to column names and values
            with lists of allowed values
        """
        return {}

    def get_relations_info(self, filter_layer_list=[]):
        """
        Info about relations found in a database (or database schema).

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                constraint_name
                referencing_table_name
                referencing_column_name
                constraint_schema
                referenced_table_name
                referenced_column_name
                strength
                cardinality_max
                cardinality_min
        """
        return []

    def get_bags_of_info(self):
        """
        Info about bags_of found in a database (or database schema).

        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                current_layer_name
                attribute
                target_layer_name
                cardinality_max
                cardinality_min
        """
        return []

    def get_ignored_layers(self, ignore_basket_tables=True):
        """
        The ignored layers according to the ignored schemas and ignored tables and the ignored ili elements
        listed in the config.py.
        Additionally all the ili elements that have the attribute name ili2db.mapping in the meta attribute
        table.
        """
        tables_info = self.get_tables_info()
        relations_info = self.get_relations_info()
        meta_attrs_info = self.get_meta_attrs_info()
        mapping_ili_elements = []
        static_tables = []
        detected_tables = []
        referencing_detected_tables = []
        for record in meta_attrs_info:
            if record["attr_name"] == "ili2db.mapping":
                mapping_ili_elements.append(record["ilielement"])

        for record in tables_info:
            if "ili_name" in record:
                if (
                    record["ili_name"] in mapping_ili_elements
                    or record["ili_name"] in IGNORED_ILI_ELEMENTS
                ):
                    detected_tables.append(record["tablename"])
                    continue
            if "schemaname" in record and record["schemaname"]:
                ignored = False
                for ignored_schema_pattern in IGNORED_SCHEMAS:
                    if fnmatch.fnmatch(record["schemaname"], ignored_schema_pattern):
                        ignored = True
                        break
                if ignored:
                    static_tables.append(record["tablename"])
                    continue
            if "tablename" in record:
                if self.is_spatial_index_table(record["tablename"]) or (
                    record["tablename"] in IGNORED_TABLES
                    and (
                        ignore_basket_tables or record["tablename"] not in BASKET_TABLES
                    )
                ):
                    static_tables.append(record["tablename"])
                    continue

        for record in relations_info:
            if record["referenced_table"] in detected_tables:
                referencing_detected_tables.append(record["referencing_table"])

        return static_tables + detected_tables + referencing_detected_tables

    def is_spatial_index_table(self, tablename=str) -> bool:
        """Note: Checks if the table is a technical table used for spatial indexing"""
        return False

    def get_iliname_dbname_mapping(self, sqlnames=list()):
        """Note: the parameter sqlnames is only used for ili2db version 3 relation creation"""
        return {}

    def get_classili_classdb_mapping(self, models_info, extended_classes):
        """Used for ili2db version 3"""
        return {}

    def get_attrili_attrdb_mapping(self, attrs_list):
        """Used for ili2db version 3"""
        return {}

    def get_attrili_attrdb_mapping_by_owner(self, owners):
        """Used for ili2db version 3"""
        return {}

    def get_models(self):
        """
        Returns the models in use, the ili-file content and the direct parents of the model.
        """
        return {}

    def ili_version(self):
        """
        Returns the version of the ili2db application that was used to create the schema.
        """
        return None

    def get_basket_handling(self):
        """
        Returns `True` if a basket handling is enabled according to the settings table.
        Means when the database has been created with `--createBasketCol`.
        """
        return False

    def get_baskets_info(self):
        """
        Info about baskets found in the basket table and the related datasetname
        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                basket_t_id
                basket_t_ili_tid
                topic
                attachmentkey
                dataset_t_id
                datasetname
        """
        return {}

    def get_datasets_info(self):
        """
        Info about datasets found in the dataset table
        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                t_id
                datasetname
        """
        return {}

    def create_dataset(self, datasetname):
        """
        Returns the state and the errormessage
        """
        return False, None

    def rename_dataset(self, tid, datasetname):
        """
        Returns the state and the errormessage
        """
        return False, None

    def get_topics_info(self):
        """
        Returns all the topics found in the table t_ili2db_classname as long as they contain tables found in t_ili2db_table_prop and are there not defined as ENUM.
        This avoids to get structures back, containing enumerations and not being in a topic, having the structure <modelname>.<structurename>.<enumerationname>.
        Return:
            Iterable allowing to access rows, each row should allow to access
            specific columns by name (e.g., a list of dicts {column_name:value})
            Expected columns are:
                model
                topic
                bid_domain
                relevance
        """
        return {}

    def get_classes_relevance(self):
        """
        Returns the ili classes and it's sqlname and relevance. Compared to tables_info it returns the classes (and the sqlnames of tables that might not be existing)
        and not the existing tables. This is mainly used, when smart1 has been selected.
            Expected colums are:
                iliname
                sqlname
                relevance
        """
        return []

    def multiple_geometry_tables(self):
        """
        Returns a list of tables having multiple geometry columns.
        It's only usefull on GeoPackage.
        """
        return []

    def create_basket(
        self, dataset_tid, topic, tilitid_value=None, attachment_key="modelbaker"
    ):
        """
        Returns the state and the errormessage
        """
        return False, None

    def edit_basket(self, basket_config: dict) -> tuple[bool, str]:
        """
        Returns the state and the errormessage

        The basket_config must have the following keys:

            dataset_t_id
            datasetname
            topic
            bid_value
            attachmentkey
            basket_t_id
        """
        return False, None

    def get_tid_handling(self):
        """
        Returns `True` if a tid handling is enabled according to the settings table (when the database has been created with `--createTidCol`).
        If t_ili_tids are used only because of a stable id definition in the model (with `OID as` in the topic or the class definition), this parameter is not set and this function will return `{}`.
        """
        return {}

    def get_ili2db_settings(self):
        """
        Returns the settings like they are without any name mapping etc.
        """
        return {}

    def get_ili2db_sequence_value(self):
        """
        Returns the current value of the sequence used for the t_id
        """
        return None

    def get_next_ili2db_sequence_value(self):
        """
        Increases and returns the value of the sequence used for the t_id
        """
        return None

    def set_ili2db_sequence_value(self, value):
        """
        Resets the current value of the sequence used for the t_id
        """
        return False, None

    def set_preferred_translation(self, lang: str) -> bool:
        """
        Returns whether the preferred translation language was successfully set.

        Note: By convention, a value of __ means the preferred language will be
              the original (non-translated) model language.
        """
        if len(lang) == 2 and lang != "__":
            self._lang = lang
            return True

        return False

    def get_translation_handling(self) -> tuple[bool, str]:
        """
        Whether there is translation support for this DB.

        :return: Tuple containing:
            - Whether the t_ili2db_nls is present and the DB connector has a preferred language set.
            - The preferred language set.
        """
        return False, ""

    def get_available_languages(self, irrelevant_models: list[str]) -> list[str]:
        """
        Returns a list of available languages in the t_ili2db_nls table and ignores the values for the irrelevant models
        """
        return []

    def get_domain_dispnames(self, tablename):
        """
        Get the domain display names with consideration of the translation
        """
        return []

    def get_schemas(self, ignore_system_schemas=True):
        result = []
        all_schemas = self.get_all_schemas()

        if not ignore_system_schemas:
            result = all_schemas
        else:
            # filter ignored schemas
            for schema in all_schemas:
                ignored = False
                for ignored_schema_pattern in IGNORED_SCHEMAS:
                    if fnmatch.fnmatch(schema, ignored_schema_pattern):
                        ignored = True
                if ignored:
                    continue
                result.append(schema)
        return result

    def get_all_schemas(self):
        """
        Get the schemas from PostgreSQL. Otherwise empty.
        """
        return []


class DBConnectorError(Exception):
    """This error is raised when DbConnector could not connect to database.

    This exception wraps different database exceptions to unify them in a single exception.
    """

    def __init__(self, message, base_exception=None):
        super().__init__(message)
        self.base_exception = base_exception
