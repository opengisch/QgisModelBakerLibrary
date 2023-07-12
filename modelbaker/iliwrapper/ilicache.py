"""
/***************************************************************************
                              -------------------
        begin                : 15/06/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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
import glob
import logging
import os
import re
import shutil
import urllib.parse
import xml.etree.ElementTree as ET
from enum import Enum

from PyQt5.QtCore import QDir, QObject, QSortFilterProxyModel, Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QRegion, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QGridLayout, QItemDelegate, QLabel, QStyle, QWidget
from qgis.core import Qgis, QgsMessageLog

from ..utils.qt_utils import download_file
from .ili2dbutils import get_all_modeldir_in_path


class IliCache(QObject):
    ns = {"ili23": "http://www.interlis.ch/INTERLIS2.3"}

    new_message = pyqtSignal(int, str)

    CACHE_PATH = os.path.expanduser("~/.ilicache")

    def __init__(self, configuration, single_ili_file=None):
        QObject.__init__(self)
        self.information_file = "ilimodels.xml"
        self.repositories = dict()
        self.base_configuration = configuration
        self.single_ili_file = single_ili_file
        self.model = IliModelItemModel()
        self.sorted_model = QSortFilterProxyModel()
        self.sorted_model.setSourceModel(self.model)
        self.sorted_model.sort(0, Qt.AscendingOrder)
        self.directories = None
        if self.base_configuration:
            self.directories = self.base_configuration.model_directories

    def refresh(self):
        if not self.directories is None:
            for directory in self.directories:
                self.process_model_directory(directory)

        if not self.single_ili_file is None:
            if os.path.exists(self.single_ili_file):
                self.process_single_ili_file()

    def process_model_directory(self, path):
        if path[0] == "%":
            pass
        else:
            # download remote and local repositories
            self.download_repository(path)

            if os.path.isdir(path):
                # additional recursive search of paths containing ili files (without ilimodel.xml)
                get_all_modeldir_in_path(path, self.process_local_ili_folder)

    def process_single_ili_file(self):
        models = self.process_ili_file(self.single_ili_file)
        self.repositories["no_repo"] = sorted(
            models, key=lambda m: m["version"], reverse=True
        )
        self.model.set_repositories(self.repositories)

    def file_url(self, url, file):
        if url is None:
            return file
        elif os.path.isdir(url):
            return os.path.join(url, file)
        else:
            return urllib.parse.urljoin(url + "/", file)

    def file_path(self, netloc, url, file):
        if url is None:
            return file
        elif os.path.isdir(url):
            return os.path.join(url, file)
        else:
            netloc = "" if netloc is None else netloc
            return os.path.join(self.CACHE_PATH, netloc, file)

    def download_repository(self, url):
        """
        Downloads the informationfile (default: ilimodels.xml) and ilisite.xml files from the provided url
        and updates the local cache.
        """
        netloc = urllib.parse.urlsplit(url)[1] if not os.path.isdir(url) else url

        information_file_url = self.file_url(url, self.information_file)
        ilisite_url = self.file_url(url, "ilisite.xml")
        logger = logging.getLogger(__name__)

        if os.path.isdir(url):
            # continue with the local file
            if os.path.exists(information_file_url):
                self._process_informationfile(information_file_url, netloc, url)
            else:
                logger.warning(
                    self.tr("Could not find local file {}").format(information_file_url)
                )
            if os.path.exists(ilisite_url):
                self._process_ilisite(ilisite_url)
            else:
                logger.warning(
                    self.tr("Could not find local file  {}").format(ilisite_url)
                )
        else:
            netloc_dir = os.path.join(self.CACHE_PATH, netloc)
            os.makedirs(netloc_dir, exist_ok=True)
            information_file_path = os.path.join(netloc_dir, self.information_file)
            ilisite_path = os.path.join(self.CACHE_PATH, netloc, "ilisite.xml")

            # download ilimodels.xml
            download_file(
                information_file_url,
                information_file_path,
                on_success=lambda: self._process_informationfile(
                    information_file_path, netloc, url
                ),
                on_error=lambda error, error_string: logger.warning(
                    self.tr("Could not download {url} ({message})").format(
                        url=information_file_url, message=error_string
                    )
                ),
            )

            # download ilisite.xml
            download_file(
                ilisite_url,
                ilisite_path,
                on_success=lambda: self._process_ilisite(ilisite_path),
                on_error=lambda error, error_string: logger.warning(
                    self.tr("Could not download {url} ({message})").format(
                        url=ilisite_url, message=error_string
                    )
                ),
            )

    @classmethod
    def clear_cache(cls):
        if not QDir().exists(cls.CACHE_PATH):
            return

        shutil.rmtree(cls.CACHE_PATH, ignore_errors=False, onerror=None)

    def _process_ilisite(self, file):
        """
        Parses the ilisite.xml provided in ``file`` and recursively downloads any subidiary sites.
        """
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as e:
            QgsMessageLog.logMessage(
                self.tr(
                    "Could not parse ilisite file `{file}` ({exception})".format(
                        file=file, exception=str(e)
                    )
                ),
                self.tr("QGIS Model Baker"),
            )
            return

        for site in root.iter(
            "{http://www.interlis.ch/INTERLIS2.3}IliSite09.SiteMetadata.Site"
        ):
            subsite = site.find("ili23:subsidiarySite", self.ns)
            if subsite is not None:
                for location in subsite.findall(
                    "ili23:IliSite09.RepositoryLocation_", self.ns
                ):
                    value = self.get_element_text(location.find("ili23:value", self.ns))
                    if value:
                        self.download_repository(value)

    def _process_informationfile(self, file, netloc, url):
        """
        Parses ilimodels.xml provided in ``file`` and updates the local repositories cache.
        """

        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as e:
            QgsMessageLog.logMessage(
                self.tr(
                    "Could not parse ilimodels file `{file}` ({exception})".format(
                        file=file, exception=str(e)
                    )
                ),
                self.tr("QGIS Model Baker"),
            )
            return

        self.repositories[netloc] = list()
        repo_models = list()
        for repo in root.iter(
            "{http://www.interlis.ch/INTERLIS2.3}IliRepository09.RepositoryIndex"
        ):
            for model_metadata in repo.findall(
                "ili23:IliRepository09.RepositoryIndex.ModelMetadata", self.ns
            ):
                model = dict()
                model["name"] = self.get_element_text(
                    element=model_metadata.find("ili23:Name", self.ns)
                )
                if model["name"]:
                    model["version"] = self.get_element_text(
                        model_metadata.find("ili23:Version", self.ns)
                    )
                    model["repository"] = netloc
                    repo_models.append(model)

        for repo in root.iter(
            "{http://www.interlis.ch/INTERLIS2.3}IliRepository20.RepositoryIndex"
        ):
            for model_metadata in repo.findall(
                "ili23:IliRepository20.RepositoryIndex.ModelMetadata", self.ns
            ):
                model = dict()
                model["name"] = self.get_element_text(
                    model_metadata.find("ili23:Name", self.ns)
                )
                if model["name"]:
                    model["version"] = self.get_element_text(
                        model_metadata.find("ili23:Version", self.ns)
                    )
                    model["repository"] = netloc
                    repo_models.append(model)

        self.repositories[netloc] = sorted(
            repo_models,
            key=lambda m: m["version"] if m["version"] else "0",
            reverse=True,
        )

        self.model.set_repositories(self.repositories)

    def process_local_ili_folder(self, path):
        """
        Parses all .ili files in the given ``path`` (non-recursively)
        """
        models = list()
        fileModels = list()
        for ilifile in glob.iglob(os.path.join(path, "*.ili")):
            fileModels = self.process_ili_file(ilifile)
            models.extend(fileModels)

        self.repositories[path] = sorted(
            models, key=lambda m: m["version"], reverse=True
        )

        self.model.set_repositories(self.repositories)

    def process_ili_file(self, ilifile):
        fileModels = list()
        try:
            fileModels = self.parse_ili_file(ilifile, "utf-8")
        except UnicodeDecodeError:
            try:
                fileModels = self.parse_ili_file(ilifile, "latin1")
                self.new_message.emit(
                    Qgis.Warning,
                    self.tr(
                        "Even though the ili file `{}` could be read, it is not in UTF-8. Please encode your ili models in UTF-8.".format(
                            os.path.basename(ilifile)
                        )
                    ),
                )
            except UnicodeDecodeError as e:
                self.new_message.emit(
                    Qgis.Critical,
                    self.tr(
                        "Could not parse ili file `{}` with UTF-8 nor Latin-1 encodings. Please encode your ili models in UTF-8.".format(
                            os.path.basename(ilifile)
                        )
                    ),
                )
                QgsMessageLog.logMessage(
                    self.tr(
                        "Could not parse ili file `{ilifile}`. We suggest you to encode it in UTF-8. ({exception})".format(
                            ilifile=ilifile, exception=str(e)
                        )
                    ),
                    self.tr("QGIS Model Baker"),
                )
                fileModels = list()

        return fileModels

    def parse_ili_file(self, ilipath, encoding):
        """
        Parses an ili file returning models and version data
        """
        models = list()
        re_model = re.compile(r"\s*MODEL\s*([\w\d_-]+).*")
        re_model_version = re.compile(r'VERSION "([ \w\d\._-]+)".*')
        with open(ilipath, encoding=encoding) as file:
            model = None
            for lineno, line in enumerate(file):
                line = line.split("!!")[0]
                result = re_model.search(line)
                if result:
                    model = dict()
                    model["name"] = result.group(1)
                    model["version"] = ""
                    model["repository"] = ilipath
                    models += [model]

                result = re_model_version.search(line)
                if result:
                    if not model:
                        raise RuntimeError(
                            "VERSION tag found in file {}:{} without previous MODEL definition.".format(
                                ilipath, lineno
                            )
                        )
                    model["version"] = result.group(1)
                    model = None

        return models

    @property
    def model_names(self):
        names = list()
        for repo in self.repositories.values():
            for model in repo:
                names.append(model["name"])
        return names

    def get_element_text(self, element):
        if element is not None:
            return element.text
        return None


class IliModelItemModel(QStandardItemModel):
    class Roles(Enum):
        ILIREPO = Qt.UserRole + 1
        VERSION = Qt.UserRole + 2

        def __int__(self):
            return self.value

    def __init__(self, parent=None):
        super().__init__(0, 1, parent)

    def set_repositories(self, repositories):
        self.clear()
        row = 0
        names = list()

        for repository in repositories.values():

            for model in repository:
                # in case there is more than one version of the model with the same name, it shouldn't load it twice
                if any(model["name"] == s for s in names):
                    continue

                item = QStandardItem()
                item.setData(model["name"], int(Qt.DisplayRole))
                item.setData(model["name"], int(Qt.EditRole))  # considered in completer
                item.setData(model["repository"], int(IliModelItemModel.Roles.ILIREPO))
                item.setData(model["version"], int(IliModelItemModel.Roles.VERSION))

                names.append(model["name"])
                self.appendRow(item)
                row += 1


class ModelCompleterDelegate(QItemDelegate):
    """
    A item delegate for the autocompleter of model dialogs.
    It shows the source repository next to the model name.
    """

    def __init__(self):
        super().__init__()
        self.widget = QWidget()
        self.widget.setLayout(QGridLayout())
        self.widget.layout().setContentsMargins(2, 0, 0, 0)
        self.model_label = QLabel()
        self.model_label.setAttribute(Qt.WA_TranslucentBackground)
        self.repository_label = QLabel()
        self.repository_label.setAlignment(Qt.AlignRight)
        self.widget.layout().addWidget(self.model_label, 0, 0)
        self.widget.layout().addWidget(self.repository_label, 0, 1)

    def paint(self, painter, option, index):
        option.index = index
        super().paint(painter, option, index)

    def drawDisplay(self, painter, option, rect, text):
        repository = option.index.data(int(IliModelItemModel.Roles.ILIREPO))
        option.index.data(int(IliModelItemModel.Roles.VERSION))
        self.repository_label.setText(
            '<font color="#666666"><i>{repository}</i></font>'.format(
                repository=repository
            )
        )
        self.model_label.setText("{model}".format(model=text))
        self.widget.setMinimumSize(rect.size())

        model_palette = option.palette
        if option.state & QStyle.State_Selected:
            model_palette.setColor(
                QPalette.WindowText,
                model_palette.color(QPalette.Active, QPalette.HighlightedText),
            )

        self.widget.render(painter, rect.topLeft(), QRegion(), QWidget.DrawChildren)


class IliDataCache(IliCache):

    file_download_succeeded = pyqtSignal(str, str)
    file_download_failed = pyqtSignal(str, str)
    model_refreshed = pyqtSignal(int)

    CACHE_PATH = os.path.expanduser("~/.ilimetaconfigcache")

    def __init__(self, configuration, type="metaconfig", models=None):
        IliCache.__init__(self, configuration)
        self.information_file = "ilidata.xml"

        self.model = IliDataItemModel()
        self.model.modelReset.connect(
            lambda: self.model_refreshed.emit(self.model.rowCount())
        )
        self.sorted_model.setSourceModel(self.model)
        self.sorted_model.sort(0, Qt.AscendingOrder)
        self.filter_models = models.split(";") if models else []
        self.type = type
        self.directories = (
            self.base_configuration.metaconfig_directories
            if self.base_configuration
            else []
        )

    def process_model_directory(self, path):
        # download remote and local repositories
        self.download_repository(path)

    def _process_informationfile(self, file, netloc, url):
        """
        Parses ilidata.xml provided in ``file`` and updates the local repositories cache.
        """
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as e:
            QgsMessageLog.logMessage(
                self.tr(
                    "Could not parse ilidata file `{file}` ({exception})".format(
                        file=file, exception=str(e)
                    )
                ),
                self.tr("QGIS Model Baker"),
            )
            return

        model_code_regex = re.compile("http://codes.interlis.ch/model/(.*)")
        type_code_regex = re.compile("http://codes.interlis.ch/type/(.*)")
        tool_code_regex = re.compile("http://codes.opengis.ch/(.*)")

        self.repositories[netloc] = list()
        repo_metaconfigs = list()
        for repo in root.iter(
            "{http://www.interlis.ch/INTERLIS2.3}DatasetIdx16.DataIndex"
        ):
            for metaconfig_metadata in repo.findall(
                "ili23:DatasetIdx16.DataIndex.DatasetMetadata", self.ns
            ):
                categories_element = metaconfig_metadata.find(
                    "ili23:categories", self.ns
                )
                if categories_element is not None:
                    models = []
                    type = ""
                    for category in categories_element.findall(
                        "ili23:DatasetIdx16.Code_", self.ns
                    ):
                        category_value = self.get_element_text(
                            category.find("ili23:value", self.ns)
                        )
                        if category_value:
                            if model_code_regex.search(category_value):
                                models.append(
                                    model_code_regex.search(category_value).group(1)
                                )
                            if type_code_regex.search(category_value):
                                type = type_code_regex.search(category_value).group(1)
                            if tool_code_regex.search(category_value):
                                tool_code_regex.search(category_value).group(1)
                    if (
                        not any(model in models for model in self.filter_models)
                        or type != self.type
                    ):
                        continue
                    title = list()
                    for title_element in metaconfig_metadata.findall(
                        "ili23:title", self.ns
                    ):
                        for multilingual_text_element in title_element.findall(
                            "ili23:DatasetIdx16.MultilingualText", self.ns
                        ):
                            for (
                                localised_text_element
                            ) in multilingual_text_element.findall(
                                "ili23:LocalisedText", self.ns
                            ):
                                for (
                                    localised_text_element
                                ) in localised_text_element.findall(
                                    "ili23:DatasetIdx16.LocalisedText", self.ns
                                ):
                                    title_information = {
                                        "language": self.get_element_text(
                                            localised_text_element.find(
                                                "ili23:Language", self.ns
                                            )
                                        ),
                                        "text": self.get_element_text(
                                            localised_text_element.find(
                                                "ili23:Text", self.ns
                                            )
                                        ),
                                    }
                                    title.append(title_information)

                    short_description = list()

                    for short_description_element in metaconfig_metadata.findall(
                        "ili23:shortDescription", self.ns
                    ):
                        for (
                            multilingual_text_element
                        ) in short_description_element.findall(
                            "ili23:DatasetIdx16.MultilingualMText", self.ns
                        ):
                            for (
                                localised_text_element
                            ) in multilingual_text_element.findall(
                                "ili23:LocalisedText", self.ns
                            ):
                                for (
                                    localised_text_element
                                ) in localised_text_element.findall(
                                    "ili23:DatasetIdx16.LocalisedMText", self.ns
                                ):
                                    short_description_information = {
                                        "language": self.get_element_text(
                                            localised_text_element.find(
                                                "ili23:Language", self.ns
                                            )
                                        ),
                                        "text": self.get_element_text(
                                            localised_text_element.find(
                                                "ili23:Text", self.ns
                                            )
                                        ),
                                    }
                                    short_description.append(
                                        short_description_information
                                    )

                    model_link_names = []
                    for basket_element in metaconfig_metadata.findall(
                        "ili23:baskets", self.ns
                    ):
                        for basket_metadata in basket_element.findall(
                            "ili23:DatasetIdx16.DataIndex.BasketMetadata", self.ns
                        ):
                            for model_element in basket_metadata.findall(
                                "ili23:model", self.ns
                            ):
                                for model_link in model_element.findall(
                                    "ili23:DatasetIdx16.ModelLink", self.ns
                                ):
                                    model_link_names.append(
                                        self.get_element_text(
                                            model_link.find("ili23:name", self.ns)
                                        )
                                    )

                    for files_element in metaconfig_metadata.findall(
                        "ili23:files", self.ns
                    ):
                        for data_file in files_element.findall(
                            "ili23:DatasetIdx16.DataFile", self.ns
                        ):
                            for file_element in data_file.findall(
                                "ili23:file", self.ns
                            ):
                                for file in file_element.findall(
                                    "ili23:DatasetIdx16.File", self.ns
                                ):
                                    path = self.get_element_text(
                                        file.find("ili23:path", self.ns)
                                    )

                                    metaconfig = dict()
                                    metaconfig["id"] = self.get_element_text(
                                        metaconfig_metadata.find("ili23:id", self.ns)
                                    )

                                    metaconfig["version"] = self.get_element_text(
                                        metaconfig_metadata.find(
                                            "ili23:version", self.ns
                                        )
                                    )
                                    metaconfig["owner"] = self.get_element_text(
                                        metaconfig_metadata.find("ili23:owner", self.ns)
                                    )

                                    metaconfig["repository"] = netloc
                                    metaconfig["url"] = url
                                    metaconfig["models"] = models
                                    metaconfig["relative_file_path"] = path
                                    if title is not None:
                                        metaconfig["title"] = title
                                    else:
                                        metaconfig["title"] = None
                                    if short_description is not None:
                                        metaconfig[
                                            "short_description"
                                        ] = short_description
                                    else:
                                        metaconfig["short_description"] = None

                                    metaconfig["model_link_names"] = model_link_names
                                    repo_metaconfigs.append(metaconfig)

        self.repositories[netloc] = sorted(
            repo_metaconfigs,
            key=lambda m: m["version"] if m["version"] else "0",
            reverse=True,
        )

        self.model.set_repositories(self.repositories)

    def download_file(self, netloc, url, file, dataset_id=None):
        """
        Downloads the given file from the given url to the local cache.
        passes the local file path or the id (for information) to signals.
        Returns the file path immediately (might not be downloaded yet)
        """
        file_url = self.file_url(url, file)

        if url is None or os.path.isdir(url):
            file_path = file_url
            # continue with the local file
            if os.path.exists(file_url):
                self.file_download_succeeded.emit(dataset_id, file_url)
            else:
                self.file_download_failed.emit(
                    dataset_id,
                    self.tr("Could not find local file  {}").format(file_url),
                )
        else:
            file_path = os.path.join(self.CACHE_PATH, netloc, file)
            file_dir = os.path.dirname(file_path)
            os.makedirs(file_dir, exist_ok=True)

            download_file(
                file_url,
                file_path,
                on_success=lambda: self.file_download_succeeded.emit(
                    dataset_id, file_path
                ),
                on_error=lambda error, error_string: self.file_download_failed.emit(
                    dataset_id,
                    self.tr("Could not download file {url} ({message})").format(
                        url=file_url, message=error_string
                    ),
                ),
            )
        return file_path


class IliDataItemModel(QStandardItemModel):
    class Roles(Enum):
        ILIREPO = Qt.UserRole + 1
        VERSION = Qt.UserRole + 2
        MODELS = Qt.UserRole + 3
        RELATIVEFILEPATH = Qt.UserRole + 4
        OWNER = Qt.UserRole + 5
        TITLE = Qt.UserRole + 6
        ID = Qt.UserRole + 7
        URL = Qt.UserRole + 8
        MODEL_LINKS = Qt.UserRole + 9
        SHORT_DESCRIPTION = Qt.UserRole + 10

        def __int__(self):
            return self.value

    def __init__(self, parent=None):
        super().__init__(0, 1, parent)

    def set_repositories(self, repositories):
        self.beginResetModel()
        self.clear()
        row = 0
        ids = list()

        for repository in repositories.values():

            for dataitem in repository:
                if any(dataitem["id"] == s for s in ids):
                    continue

                item = QStandardItem()
                display_value = dataitem["id"]
                if dataitem["title"] and "text" in dataitem["title"][0]:
                    # since there is no multilanguage handling we take the first entry
                    display_value = dataitem["title"][0]["text"]

                short_description = None
                if (
                    dataitem["short_description"]
                    and "text" in dataitem["short_description"][0]
                ):
                    short_description = dataitem["short_description"][0]["text"]

                item.setData(display_value, int(Qt.DisplayRole))
                item.setData(display_value, int(Qt.EditRole))
                item.setData(short_description, int(Qt.ToolTipRole))
                item.setData(dataitem["id"], int(IliDataItemModel.Roles.ID))
                item.setData(
                    dataitem["repository"], int(IliDataItemModel.Roles.ILIREPO)
                )
                item.setData(dataitem["version"], int(IliDataItemModel.Roles.VERSION))
                item.setData(dataitem["models"], int(IliDataItemModel.Roles.MODELS))
                item.setData(
                    dataitem["relative_file_path"],
                    int(IliDataItemModel.Roles.RELATIVEFILEPATH),
                )
                item.setData(dataitem["owner"], int(IliDataItemModel.Roles.OWNER))
                item.setData(dataitem["title"], int(IliDataItemModel.Roles.TITLE))
                item.setData(dataitem["url"], int(IliDataItemModel.Roles.URL))
                item.setData(
                    short_description, int(IliDataItemModel.Roles.SHORT_DESCRIPTION)
                )

                item.setData(
                    dataitem["model_link_names"],
                    int(IliDataItemModel.Roles.MODEL_LINKS),
                )

                ids.append(dataitem["id"])
                self.appendRow(item)
                row += 1
        self.endResetModel()


class MetaConfigCompleterDelegate(QItemDelegate):
    """
    A item delegate for the autocompleter of metaconfig / topping dialogs.
    It shows the source repository (including model) next to the metaconfig id and the owner.
    """

    def __init__(self):
        super().__init__()
        self.widget = QWidget()
        self.widget.setLayout(QGridLayout())
        self.widget.layout().setContentsMargins(2, 0, 0, 0)
        self.metaconfig_label = QLabel()
        self.metaconfig_label.setAttribute(Qt.WA_TranslucentBackground)
        self.repository_label = QLabel()
        self.repository_label.setAlignment(Qt.AlignRight)
        self.widget.layout().addWidget(self.metaconfig_label, 0, 0)
        self.widget.layout().addWidget(self.repository_label, 0, 1)

    def paint(self, painter, option, index):
        option.index = index
        super().paint(painter, option, index)

    def drawDisplay(self, painter, option, rect, text):
        repository = option.index.data(int(IliDataItemModel.Roles.ILIREPO))
        display_text = option.index.data(int(Qt.DisplayRole))

        self.repository_label.setText(
            '<font color="#666666"><i>{repository}</i></font>'.format(
                repository=repository
            )
        )
        self.metaconfig_label.setText(
            "{display_text}".format(display_text=display_text)
        )
        self.widget.setMinimumSize(rect.size())

        model_palette = option.palette
        if option.state & QStyle.State_Selected:
            model_palette.setColor(
                QPalette.WindowText,
                model_palette.color(QPalette.Active, QPalette.HighlightedText),
            )

        self.widget.render(painter, rect.topLeft(), QRegion(), QWidget.DrawChildren)


class IliToppingFileCache(IliDataCache):

    download_finished = pyqtSignal()
    """
    meta_netloc is the repository (netloc) of the metaconfiguration file used for file paths in the file_ids
    file_ids can contain ilidata: or file: information
    """

    CACHE_PATH = os.path.expanduser("~/.ilitoppingfilescache")

    def __init__(self, configuration, file_ids=None, tool_dir=None):
        IliDataCache.__init__(self, configuration)
        self.model = IliToppingFileItemModel()
        self.sorted_model.setSourceModel(self.model)
        self.sorted_model.sort(0, Qt.AscendingOrder)
        self.file_ids = file_ids
        self.tool_dir = (
            tool_dir
            if tool_dir
            else os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        )
        self.downloaded_files = list()
        self.file_download_succeeded.connect(
            lambda dataset_id, path: self.on_download_status(dataset_id)
        )
        self.file_download_failed.connect(
            lambda dataset_id, path: self.on_download_status(dataset_id)
        )
        self.model.rowsInserted.connect(lambda: self.on_download_status(None))

    def refresh(self):
        if not self.directories is None:
            for directory in self.directories:
                self.process_model_directory(directory)

        # collect local files
        netloc = "local_files"
        repo_files = list()
        for file_path_id in [
            file_id for file_id in self.file_ids if file_id[0:5] == "file:"
        ]:
            toppingfile = dict()
            toppingfile["id"] = file_path_id
            toppingfile["version"] = None
            toppingfile["owner"] = None
            toppingfile["repository"] = netloc
            toppingfile["url"] = None
            toppingfile["relative_file_path"] = file_path_id[5:]
            toppingfile["local_file_path"] = (
                file_path_id[5:]
                if os.path.isabs(file_path_id[5:])
                else os.path.join(self.tool_dir, file_path_id[5:])
            )
            if os.path.exists(toppingfile["local_file_path"]):
                self.file_download_succeeded.emit(
                    file_path_id, toppingfile["local_file_path"]
                )
            else:
                self.file_download_failed.emit(
                    file_path_id,
                    self.tr("Could not find local file  {}").format(file_path_id[5:]),
                )
            repo_files.append(toppingfile)

        self.repositories[netloc] = repo_files
        self.model.set_repositories(self.repositories)

    def on_download_status(self, dataset_id):
        # here we could add some more logic
        if dataset_id is not None:
            self.downloaded_files.append(dataset_id)
        if len(self.downloaded_files) == len(self.file_ids) == self.model.rowCount():
            self.download_finished.emit()

    def _process_informationfile(self, file, netloc, url):
        """
        Parses ilidata.xml provided in ``file`` and updates the local repositories cache.
        """
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as e:
            QgsMessageLog.logMessage(
                self.tr(
                    "Could not parse ilidata file `{file}` ({exception})".format(
                        file=file, exception=str(e)
                    )
                ),
                self.tr("QGIS Model Baker"),
            )
            return

        self.repositories[netloc] = list()
        repo_files = list()
        for repo in root.iter(
            "{http://www.interlis.ch/INTERLIS2.3}DatasetIdx16.DataIndex"
        ):
            for topping_metadata in repo.findall(
                "ili23:DatasetIdx16.DataIndex.DatasetMetadata", self.ns
            ):
                dataset_id = "ilidata:{}".format(
                    self.get_element_text(topping_metadata.find("ili23:id", self.ns))
                )
                if dataset_id in self.file_ids:
                    for files_element in topping_metadata.findall(
                        "ili23:files", self.ns
                    ):
                        for data_file in files_element.findall(
                            "ili23:DatasetIdx16.DataFile", self.ns
                        ):
                            for file_element in data_file.findall(
                                "ili23:file", self.ns
                            ):
                                for file in file_element.findall(
                                    "ili23:DatasetIdx16.File", self.ns
                                ):
                                    path = self.get_element_text(
                                        file.find("ili23:path", self.ns)
                                    )

                                    toppingfile = dict()
                                    toppingfile["id"] = dataset_id

                                    toppingfile["version"] = self.get_element_text(
                                        topping_metadata.find("ili23:version", self.ns)
                                    )
                                    toppingfile["owner"] = self.get_element_text(
                                        topping_metadata.find("ili23:owner", self.ns)
                                    )

                                    toppingfile["repository"] = netloc
                                    # relative_file_path like layerstyle/something.qml
                                    toppingfile["relative_file_path"] = path
                                    # url like http://models.opengis.ch or /home/nyuki/folder
                                    toppingfile["url"] = url
                                    toppingfile["local_file_path"] = self.download_file(
                                        netloc, url, path, dataset_id
                                    )
                                    repo_files.append(toppingfile)

        self.repositories[netloc] = sorted(
            repo_files,
            key=lambda m: m["version"] if m["version"] else "0",
            reverse=True,
        )

        self.model.set_repositories(self.repositories)


class IliToppingFileItemModel(QStandardItemModel):
    class Roles(Enum):
        ILIREPO = Qt.UserRole + 1
        VERSION = Qt.UserRole + 2
        RELATIVEFILEPATH = Qt.UserRole + 3
        LOCALFILEPATH = Qt.UserRole + 4
        OWNER = Qt.UserRole + 5
        URL = Qt.UserRole + 6

        def __int__(self):
            return self.value

    def __init__(self, parent=None):
        super().__init__(0, 1, parent)

    def set_repositories(self, repositories):
        self.clear()
        row = 0
        ids = list()

        for repository in repositories.values():

            for toppingfile in repository:
                if any(toppingfile["id"] == s for s in ids):
                    continue
                item = QStandardItem()
                item.setData(toppingfile["id"], int(Qt.DisplayRole))
                item.setData(toppingfile["id"], int(Qt.EditRole))
                item.setData(
                    toppingfile["repository"],
                    int(IliToppingFileItemModel.Roles.ILIREPO),
                )
                item.setData(
                    toppingfile["version"], int(IliToppingFileItemModel.Roles.VERSION)
                )
                item.setData(toppingfile["url"], int(IliToppingFileItemModel.Roles.URL))
                item.setData(
                    toppingfile["relative_file_path"],
                    int(IliToppingFileItemModel.Roles.RELATIVEFILEPATH),
                )
                item.setData(
                    toppingfile["local_file_path"],
                    int(IliToppingFileItemModel.Roles.LOCALFILEPATH),
                )
                item.setData(
                    toppingfile["owner"], int(IliToppingFileItemModel.Roles.OWNER)
                )

                ids.append(toppingfile["id"])
                self.appendRow(item)
                row += 1
