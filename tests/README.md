# Running the tests

To run the tests inside the same environment as they are executed on gh workflow,
you need a [Docker](https://www.docker.com/) installation. This will also launch an extra container
with a database, so your own postgres installation is not affected at all.

To run the tests, go to the main directory of the project and do

```sh
export QGIS_TEST_VERSION=latest # See https://hub.docker.com/r/qgis/qgis/tags/
export GITHUB_WORKSPACE=$PWD # only for local execution
docker-compose -f .docker/docker-compose.gh.yml run qgis /usr/src/.docker/run-docker-tests.sh
```

In one line, removing all containers.
```sh
QGIS_TEST_VERSION=latest GITHUB_WORKSPACE=$PWD docker-compose -f .docker/docker-compose.gh.yml run qgis /usr/src/.docker/run-docker-tests.sh; GITHUB_WORKSPACE=$PWD docker-compose -f .docker/docker-compose.gh.yml rm -s -f
```

Run all test starting with ``test_array_`
```sh
[...] run-tests.sh -k test_array_ [...]
```

## Testing with MSSQL

These are dirty notes for the quickest way to test mssql queries manually in the way the tests work.

1. Create a new dir. E.g. `.local_docker_test`
2. Copy the original docker-compose file from directory `.docker` and remove everything except the qgis and the mssql container (remove the postgis dependency in qgis as well).
3. Copy the original `run-docker-tests.sh` and remove everything except:
    ```bash
    set -e

    /usr/src/tests/testdata/mssql/setup-mssql.sh
    ```
4. Do the following:
    Go to the local folder
    ```bash
    export QGIS_TEST_VERSION=latest
    export GITHUB_WORKSPACE=$PWD
    docker-compose -f .local_docker_test/docker-compose.gh.yml up -d
    docker exec -it local_docker_test_qgis_1 bash
    ```
    And then in the qgis docker:
    ```bash
    /usr/src/.local_docker_test/run-docker-tests.sh
    java -jar /usr/src/modelbaker/iliwrapper/bin/ili2mssql-5.0.0/ili2mssql-5.0.0.jar --schemaimport --dbhost mssql --dbusr sa --dbpwd '<YourStrong!Passw0rd>' --dbdatabase gis --dbschema optimal_polymorph_manuel --coalesceCatalogueRef --createEnumTabs --createNumChecks --createUnique --createFk --createFkIdx --coalesceMultiSurface --coalesceMultiLine --coalesceMultiPoint --coalesceArray --beautifyEnumDispName --createGeomIdx --createMetaInfo --expandMultilingual --createTypeConstraint --createEnumTabsWithId --createTidCol --importTid --smart2Inheritance --strokeArcs --createBasketCol --defaultSrsAuth EPSG --defaultSrsCode 2056 --preScript NULL --postScript NULL --models Polymorphic_Ortsplanung_V1_1 --iliMetaAttrs NULL /usr/src/tests/testdata/ilimodels/Polymorphic_Ortsplanung_V1_1.ili
    ```
    (Surely this could be done without this qgis container, but there you have everything for the set up already...)
5. Now connect (with eg. the VS Code extension) with these params:
    ```
    localhost
    1433
    sa
    '<YourStrong!Passw0rd>'
    ```

### Testing in python console

Another dirty script as helper.

To test in python console in QGIS you need
- to get the modelbaker library from the plugin
- copy paste the test utils functions and apply local db settings
- use your local paths for model dir and target gpkg etc.

```
import datetime
import logging
import os
import shutil
import tempfile

import pytest
from qgis.core import Qgis, QgsProject
from qgis.testing import start_app, unittest

from QgisModelBaker.libs.modelbaker.dataobjects.project import Project
from QgisModelBaker.libs.modelbaker.db_factory.gpkg_command_config_manager import GpkgCommandConfigManager
from QgisModelBaker.libs.modelbaker.generator.generator import Generator
from QgisModelBaker.libs.modelbaker.iliwrapper import iliimporter
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode

import os
from subprocess import call

import pytest

from modelbaker.iliwrapper import ili2dbconfig
from modelbaker.iliwrapper.globals import DbIliMode
from modelbaker.iliwrapper.ili2dbconfig import (
    BaseConfiguration,
    DeleteConfiguration,
    ExportConfiguration,
    ExportMetaConfigConfiguration,
    ImportDataConfiguration,
    SchemaImportConfiguration,
    UpdateDataConfiguration,
    ValidateConfiguration,
)


def iliimporter_config(tool=DbIliMode.ili2pg, modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = SchemaImportConfiguration()
    configuration.tool = tool
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = "localhost"
        configuration.dbport = 54322
        configuration.dbusr = "docker"
        configuration.dbpwd = "docker"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = "mssql"
        configuration.dbusr = "sa"
        configuration.dbpwd = "<YourStrong!Passw0rd>"
        configuration.database = "gis"
    configuration.base_configuration = base_config

    return configuration


def iliexporter_config(
    tool=DbIliMode.ili2pg, modeldir=None, gpkg_path="geopackage/test_export.gpkg"
):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = ExportConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = "localhost"
        configuration.dbport = 54322
        configuration.dbusr = "docker"
        configuration.dbpwd = "docker"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = "mssql"
        configuration.dbusr = "sa"
        configuration.dbpwd = "<YourStrong!Passw0rd>"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2gpkg:
        configuration.dbfile = testdata_path(gpkg_path)
    configuration.base_configuration = base_config

    return configuration


def ilidataimporter_config(tool=DbIliMode.ili2pg, modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = ImportDataConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = "localhost"
        configuration.dbport = 54322
        configuration.dbusr = "docker"
        configuration.dbpwd = "docker"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = "mssql"
        configuration.dbusr = "sa"
        configuration.dbpwd = "<YourStrong!Passw0rd>"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2gpkg:
        configuration.dbfile = testdata_path("geopackage/test_export.gpkg")
    configuration.base_configuration = base_config

    return configuration


def iliupdater_config(tool=DbIliMode.ili2pg, modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = UpdateDataConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = "localhost"
        configuration.dbport = 54322
        configuration.dbusr = "docker"
        configuration.dbpwd = "docker"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = "mssql"
        configuration.dbusr = "sa"
        configuration.dbpwd = "<YourStrong!Passw0rd>"
        configuration.database = "gis"

    configuration.base_configuration = base_config

    return configuration


def ilivalidator_config(
    tool=DbIliMode.ili2pg, modeldir=None, gpkg_path="geopackage/test_validate.gpkg"
):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = ValidateConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = "localhost"
        configuration.dbport = 54322
        configuration.dbusr = "docker"
        configuration.dbpwd = "docker"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = "mssql"
        configuration.dbusr = "sa"
        configuration.dbpwd = "<YourStrong!Passw0rd>"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2gpkg:
        configuration.dbfile = testdata_path(gpkg_path)
    configuration.base_configuration = base_config

    return configuration


def ilideleter_config(tool=DbIliMode.ili2pg, modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = DeleteConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = "localhost"
        configuration.dbport = 54322
        configuration.dbusr = "docker"
        configuration.dbpwd = "docker"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = "mssql"
        configuration.dbusr = "sa"
        configuration.dbpwd = "<YourStrong!Passw0rd>"
        configuration.database = "gis"

    configuration.base_configuration = base_config

    return configuration


def ilimetaconfigexporter_config(tool=DbIliMode.ili2pg, modeldir=None):
    base_config = BaseConfiguration()
    if modeldir is None:
        base_config.custom_model_directories_enabled = False
    else:
        base_config.custom_model_directories = testdata_path(modeldir)
        base_config.custom_model_directories_enabled = True

    configuration = ExportMetaConfigConfiguration()
    if tool == DbIliMode.ili2pg:
        configuration.dbhost = "localhost"
        configuration.dbport = 54322
        configuration.dbusr = "docker"
        configuration.dbpwd = "docker"
        configuration.database = "gis"
    elif tool == DbIliMode.ili2mssql:
        configuration.dbhost = "mssql"
        configuration.dbusr = "sa"
        configuration.dbpwd = "<YourStrong!Passw0rd>"
        configuration.database = "gis"

    configuration.base_configuration = base_config

    return configuration


@pytest.mark.skip("This is a utility function, not a test function")
def testdata_path(path):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, "testdata", path)


def get_pg_conn(schema):
    myenv = os.environ.copy()
    myenv["PGPASSWORD"] = "docker"

    call(
        [
            "pg_restore",
            "-Fc",
            "-h" + "localhost"
            "-p54322"
            "-Udocker",
            "-dgis",
            testdata_path("dumps/{}_dump".format(schema)),
        ],
        env=myenv,
    )
    db_factory = DbSimpleFactory().create_factory(DbIliMode.pg)
    configuration = ili2dbconfig.ExportConfiguration()

    configuration.database = "gis"
    configuration.dbhost = "localhost"
    configuration.dbport = 54322
    configuration.dbusr = "docker"
    configuration.dbpwd = "docker"
    configuration.dbport = "5432"

    config_manager = db_factory.get_db_command_config_manager(configuration)
    db_connector = db_factory.get_db_connector(config_manager.get_uri(), schema)
    return db_connector


def get_gpkg_conn(gpkg):
    db_factory = DbSimpleFactory().create_factory(DbIliMode.gpkg)
    db_connector = db_factory.get_db_connector(
        testdata_path("geopackage/{}.gpkg".format(gpkg)), None
    )
    return db_connector


def get_pg_connection_string():
    pg_host = "localhost"
    dbport = 54322
    return "dbname=gis user=docker password=docker host=localhost port=54322"


# Schema Import
importer = iliimporter.Importer()
importer.tool = DbIliMode.ili2gpkg
importer.configuration = iliimporter_config(importer.tool, "/home/dave/dev/opengisch/QgisModelBakerLibrary/tests/testdata/ilimodels")
importer.configuration.ilimodels = "Colors_V2"
importer.configuration.dbfile = f"/home/dave/qgis-projects/test_{datetime.datetime.now()}.gpkg"
importer.configuration.inheritance = "smart2"
importer.configuration.create_basket_col = False
# createEnumTabs
importer.configuration.enum_tabs = "tabs"
print(importer.run())

config_manager = GpkgCommandConfigManager(importer.configuration)
uri = config_manager.get_uri()

generator = Generator(
    DbIliMode.ili2gpkg, uri, importer.configuration.inheritance
)

available_layers = generator.layers()
relations, bagof = generator.relations(available_layers)

legend = generator.legend(available_layers)

project = Project()
project.layers = available_layers
project.relations = relations
print(bagof)
print(available_layers)
project.legend = legend
project.post_generate()

qgis_project = QgsProject.instance()
project.create(None, qgis_project)
```
