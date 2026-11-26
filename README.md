<img alt="logo" src="https://raw.githubusercontent.com/opengisch/QgisModelBakerLibrary/main/assets/long-logo-lib-modelbaker.png">

# modelbaker - the library

The modelbaker library is a package containing four main areas:
- a wrapper for ili2db commands (`iliwrapper`)
- a generator to create a QGIS project from its database source with the help of ili2db meta information
- project topping creation tools (`ilitoppingmaker`)
- processing tools (`processing`)

The API documentation you can find [here](https://github.com/opengisch/QgisModelBakerLibrary).

This Library is the backend of the QGIS Plugin [QGIS Model Baker](https://github.com/opengisch/QgisModelBaker).

### Installation

```
pip install modelbaker
```

## Infos for Devs

### Code style

Is enforced with pre-commit. To use, make:
```
pip install pre-commit
pre-commit install
```

And to run it over all the files (with infile changes):

```
pre-commit run --color=always --all-file
```

### Needed packages from PyPI

Needed packages from PyPI are downloaded and packaged on deployment to the plugin's libs folder.

Run the script to download and unpack them or install them to your system.

Script:
```
./scripts/package_pip_packages.sh
```
