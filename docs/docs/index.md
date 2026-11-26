# Model Baker Library

![Model Baker](assets/long-logo-lib-modelbaker.png)

The modelbaker library is the backend of the QGIS plugin [QGIS Model Baker](https://github.com/opengisch/QgisModelBaker). It contains four main areas:

- a wrapper for ili2db commands (`iliwrapper`)
- a generator to create a QGIS project from its database source with the help of ili2db meta information
- project topping creation tools (`ilitoppingmaker`)
- processing tools (`processing`)

## Installation

```
pip install modelbaker
```

## Packages

| Package | Content |
|---|---|
| [`iliwrapper`](reference/iliwrapper/index.md) | Configurations and executables to run ili2db / ili2c, caches of the INTERLIS repositories |
| [`dbconnector`](reference/dbconnector/index.md) | Connectors to read the physical model from PostgreSQL and GeoPackage |
| [`db_factory`](reference/db_factory/index.md) | Factories providing the database specific objects |
| [`generator`](reference/generator/index.md) | Generator of the QGIS project (layers, relations and legend) |
| [`dataobjects`](reference/dataobjects/index.md) | Objects representing the QGIS project (layers, fields, forms, relations, legend) used for project generation |
| [`ilitoppingmaker`](reference/ilitoppingmaker/index.md) | Creation of project toppings |
| [`ili2pytools`](reference/ili2pytools/index.md) | Interacting with ili2py to parse INTERLIS models |
| [`processing`](reference/processing/index.md) | Model Baker processing algorithms to perform ili2db commands and utilities |
| [`utils`](reference/utils/index.md) | Utilities for databases, QGIS and Qt |
