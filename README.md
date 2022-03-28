![modelbaker librar](assets/modelbaker_logo.svg)

The Model Baker Library is a Package containing two main areas:
- Wrapper for ili2db 
- Functionalies to generate a QGIS project from it's database source and interacting with this source

This Library is the backend of the QGIS Plugin [QGIS Model Baker](https://github.com/opengisch/QgisModelBaker).
### Installation

```
pip install modelbaker
```
### Structure

```
.

├── iliwrapper
│   ├── globals.py
│   ├── ili2dbargs.py
│   ├── ili2dbconfig.py
│   ├── ili2dbtools.py
│   ├── ili2dbutils.py
│   ├── ilicache.py
│   ├── iliexecutable.py
│   ├── iliexporter.py
│   ├── iliimporter.py
│   ├── iliupdater.py
│   ├── ilivalidator.py
│   └── __init__.py
├── dataobjects
│   ├── fields.py
│   ├── form.py
│   ├── __init__.py
│   ├── layers.py
│   ├── legend.py
│   ├── project.py
│   └── relations.py
├── dbconnector
│   ├── config.py
│   ├── db_connector.py
│   ├── gpkg_connector.py
│   ├── __init__.py
│   ├── mssql_connector.py
│   └── pg_connector.py
├── db_factory
│   ├── db_command_config_manager.py
│   ├── db_factory.py
│   ├── db_simple_factory.py
│   ├── gpkg_command_config_manager.py
│   ├── gpkg_factory.py
│   ├── gpkg_layer_uri.py
│   ├── __init__.py
│   ├── layer_uri.py
│   ├── mssql_command_config_manager.py
│   ├── mssql_factory.py
│   ├── mssql_layer_uri.py
│   ├── pg_command_config_manager.py
│   ├── pg_factory.py
│   └── pg_layer_uri.py
├── generator
│   ├── config.py
│   ├── domain_relations_generator.py
│   ├── generator.py
│   └── __init__.py
├── __init__.py
└── utils
    ├── db_utils.py
    ├── globals.py
    ├── __init__.py
    ├── qgis_utils.py
    └── qt_utils.py
```