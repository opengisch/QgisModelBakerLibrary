![logo](assets/Long-Logo_Green_Modelbaker_RGB.png)
# modelbaker - the library

The modelbaker library is a package containing two main areas:
- Wrapper for ili2db `iliwrapper`
- Modules to generate a QGIS project from it's database source and interacting with this source

This Library is the backend of the QGIS Plugin [QGIS Model Baker](https://github.com/opengisch/QgisModelBaker).
### Installation

```
pip install modelbaker
```
### Structure

```
.
├── __init__.py
├── iliwrapper
│   ├── __init__.py
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
│   └── ilivalidator.py
├── dataobjects
│   ├── __init__.py
│   ├── fields.py
│   ├── form.py
│   ├── layers.py
│   ├── legend.py
│   ├── project.py
│   └── relations.py
├── dbconnector
│   ├── __init__.py
│   ├── config.py
│   ├── db_connector.py
│   ├── gpkg_connector.py
│   ├── mssql_connector.py
│   └── pg_connector.py
├── db_factory
│   ├── __init__.py
│   ├── db_command_config_manager.py
│   ├── db_factory.py
│   ├── db_simple_factory.py
│   ├── gpkg_command_config_manager.py
│   ├── gpkg_factory.py
│   ├── gpkg_layer_uri.py
│   ├── layer_uri.py
│   ├── mssql_command_config_manager.py
│   ├── mssql_factory.py
│   ├── mssql_layer_uri.py
│   ├── pg_command_config_manager.py
│   ├── pg_factory.py
│   └── pg_layer_uri.py
├── generator
│   ├── __init__.py
│   ├── config.py
│   ├── domain_relations_generator.py
│   └── generator.py
└── utils
│   ├── __init__.py
    ├── db_utils.py
    ├── globals.py
    ├── qgis_utils.py
    └── qt_utils.py
```