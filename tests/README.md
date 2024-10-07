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
2. Copy the original docker-compose file from directory `.docker` and remove everything except the qgis and the mssql container.
3. Copy the original Dockerfile as well. Leave it like it is...
4. Copy the original `run-docker-tests.sh` and remove everything except:
    ```bash
    set -e

    /usr/src/tests/testdata/mssql/setup-mssql.sh
    ```
5. Do the following:
    ```bash
    docker-compose up -d
    docker exec -it local_docker_tests_qgis_1 bash
    ```
    And then in the qgis docker:
    ```bash
    /usr/src/.local_docker_tests/run-docker-tests.sh;
    java -jar /usr/src/modelbaker/iliwrapper/bin/ili2mssql-5.0.0/ili2mssql-5.0.0.jar --schemaimport --dbhost mssql --dbusr sa --dbpwd '<YourStrong!Passw0rd>' --dbdatabase gis --dbschema optimal_polymorph_manuel --coalesceCatalogueRef --createEnumTabs --createNumChecks --createUnique --createFk --createFkIdx --coalesceMultiSurface --coalesceMultiLine --coalesceMultiPoint --coalesceArray --beautifyEnumDispName --createGeomIdx --createMetaInfo --expandMultilingual --createTypeConstraint --createEnumTabsWithId --createTidCol --importTid --smart2Inheritance --strokeArcs --createBasketCol --defaultSrsAuth EPSG --defaultSrsCode 2056 --preScript NULL --postScript NULL --models Polymorphic_Ortsplanung_V1_1 --iliMetaAttrs NULL /usr/src/tests/testdata/ilimodels/Polymorphic_Ortsplanung_V1_1.ili
    ```
    (Surely this could be done without this qgis container, but there you have everything for the set up already...)
6. Now connect (with eg. the VS Code extension) with these params:
    ```
    localhost
    1433
    sa
    '<YourStrong!Passw0rd>'
    ```
