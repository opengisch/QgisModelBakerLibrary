"""
/***************************************************************************
                              -------------------
        begin                : 2022-07-17
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
        email                : david at opengis ch
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


from qgis.core import Qgis, QgsProject

from ..libs.toppingmaker import ExportSettings, ProjectTopping
from .ilidata import IliData
from .ilitarget import IliTarget
from .metaconfig import MetaConfig


class IliProjectTopping(ProjectTopping):
    """
    Class keeping a projet configuration resulting in a YAML file optimized for INTERLIS projects.
    - layertree
    - layerorder
    - project variables (future)
    - print layout (future)
    - map themes (future)
    QML style files, QLR layer definition files and the source of a layer can be linked in the YAML file and are exported to the specific folders.

    And artefacts for INTERLIS use like ilidata, metaconfigfile (ini) and a target of IliTarget as well as the needed methods to generate them.
    """

    def __init__(
        self,
        target=IliTarget(),
        export_settings: ExportSettings = ExportSettings(),
        metaconfig=MetaConfig(),
    ):
        # While ProjectTopping does not hold objects like target and export_settings (and those are passed by the function) the IliProjectTopping keeps it to set up the whole IliProjectTopping before create anything.
        super().__init__()
        self.target = target
        self.export_settings = export_settings
        self.metaconfig = metaconfig

    @property
    def models(self):
        return self.metaconfig.ili2db_settings.models

    @property
    def referencedata_paths(self):
        return self.metaconfig.referencedata_paths

    @models.setter
    def models(self, models: list):
        self.metaconfig.ili2db_settings.models = models

    @referencedata_paths.setter
    def referencedata_paths(self, paths: list):
        self.metaconfig.referencedata_paths = paths

    def makeit(self, project: QgsProject = None):
        """
        Creates everything - generates all the files.
        Returns the path to the ilidata.xml file.
        """
        self.stdout.emit(self.tr("Generate everything."), Qgis.Info)
        ilidata_path = None
        if not project:
            self.stdout.emit(
                self.tr("Cannot generate anything without having a QGIS project."),
                Qgis.Warning,
            )
            return False
        # Creates and sets the project_topping considering the passed QgsProject and the existing ExportSettings.
        self.parse_project(project, self.export_settings)
        # Generate topping files (layertree and depending files like style etc) considering existing ProjectTopping and Target.
        projecttopping_id = self.generate_files(self.target)

        # update metaconfig object
        self.metaconfig.update_projecttopping_path(projecttopping_id)

        # generate metaconfig (topping) file
        if self.metaconfig.generate_files(self.target):
            self.stdout.emit(self.tr("MetaConfig written to INI file."), Qgis.Info)

        # generate ilidata
        ilidata = IliData()
        ilidata_path = ilidata.generate_file(self.target, self.models)
        if ilidata_path:
            self.stdout.emit(
                self.tr("IliData written to XML file: {}").format(ilidata_path),
                Qgis.Info,
            )

        return ilidata_path
