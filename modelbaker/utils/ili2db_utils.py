"""
/***************************************************************************
                              -------------------
        begin                : 27.09.2024
        git sha              : :%H$
        copyright            : (C) 2024 by Germán Carrillo
        email                : german at opengis ch
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
from qgis.PyQt.QtCore import QObject, Qt, pyqtSignal

from ..iliwrapper import ilideleter, ilimetaconfigexporter
from ..iliwrapper.ili2dbconfig import (
    DeleteConfiguration,
    ExportMetaConfigConfiguration,
    Ili2DbCommandConfiguration,
)
from ..iliwrapper.ili2dbutils import JavaNotFoundError
from ..utils.qt_utils import OverrideCursor


class Ili2DbUtils(QObject):
    """
    Execute ili2db operations via Model Baker Library
    """

    stdout = pyqtSignal(str)
    stderr = pyqtSignal(str)
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(int, int)
    log_on_error = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)

        self._log = ""

    def delete_baskets(
        self, baskets: str, configuration: Ili2DbCommandConfiguration = None
    ):
        """
        :param baskets: Semicolon-separated list of baskets to be deleted
        :param configuration: Base Ili2DbCommandConfiguration object
        :return: Tuple with boolean result and optional message
        """
        deleter = ilideleter.Deleter()
        deleter.tool = configuration.tool
        deleter.configuration = DeleteConfiguration(configuration)
        deleter.configuration.baskets = baskets

        with OverrideCursor(Qt.CursorShape.WaitCursor):
            self._connect_ili_executable_signals(deleter)
            self._log = ""

            res = True
            msg = self.tr("Basket(s) '{}' successfully deleted!").format(baskets)
            try:
                if deleter.run() != ilideleter.Deleter.SUCCESS:
                    msg = self.tr(
                        "An error occurred when deleting the basket(s) '{}' from the DB (check the QGIS log panel)."
                    ).format(baskets)
                    res = False
                    self.log_on_error.emit(self._log)
            except JavaNotFoundError as e:
                msg = e.error_string
                res = False

            self._disconnect_ili_executable_signals(deleter)

        return res, msg

    def delete_dataset(
        self, dataset: str, configuration: Ili2DbCommandConfiguration = None
    ):
        """
        :param dataset: Dataset id to be deleted
        :param configuration: Base Ili2DbCommandConfiguration object
        :return: Tuple with boolean result and optional message
        """
        deleter = ilideleter.Deleter()
        deleter.tool = configuration.tool
        deleter.configuration = DeleteConfiguration(configuration)
        deleter.configuration.dataset = dataset

        with OverrideCursor(Qt.CursorShape.WaitCursor):
            self._connect_ili_executable_signals(deleter)
            self._log = ""

            res = True
            msg = self.tr("Dataset '{}' successfully deleted!").format(dataset)
            try:
                if deleter.run() != ilideleter.Deleter.SUCCESS:
                    msg = self.tr(
                        "An error occurred when deleting the dataset '{}' from the DB (check the QGIS log panel)."
                    ).format(dataset)
                    res = False
                    self.log_on_error.emit(self._log)
            except JavaNotFoundError as e:
                msg = e.error_string
                res = False

            self._disconnect_ili_executable_signals(deleter)

        return res, msg

    def export_metaconfig(
        self, ini_file: str, configuration: Ili2DbCommandConfiguration = None
    ):
        """
        :param ini_file: Output file
        :param configuration: Base Ili2DbCommandConfiguration object
        :return: Tuple with boolean result and optional message
        """
        metaconfig_exporter = ilimetaconfigexporter.MetaConfigExporter()
        metaconfig_exporter.tool = configuration.tool
        metaconfig_exporter.configuration = ExportMetaConfigConfiguration(configuration)
        metaconfig_exporter.configuration.metaconfigoutputfile = ini_file

        with OverrideCursor(Qt.CursorShape.WaitCursor):
            self._connect_ili_executable_signals(metaconfig_exporter)
            self._log = ""

            res = True
            msg = self.tr("MetaConfig successfully exported to '{}'!").format(ini_file)
            try:
                if (
                    metaconfig_exporter.run()
                    != ilimetaconfigexporter.MetaConfigExporter.SUCCESS
                ):
                    msg = self.tr(
                        "An error occurred when exporting the metaconfig from the DB to '{}' (check the QGIS log panel)."
                    ).format(ini_file)
                    res = False
                    self.log_on_error.emit(self._log)
            except JavaNotFoundError as e:
                msg = e.error_string
                res = False

            self._disconnect_ili_executable_signals(metaconfig_exporter)

        return res, msg

    def _connect_ili_executable_signals(self, ili_executable):
        ili_executable.process_started.connect(self.process_started)
        ili_executable.stderr.connect(self.stderr)
        ili_executable.stdout.connect(self.stdout)
        ili_executable.process_finished.connect(self.process_finished)

        ili_executable.process_started.connect(self._log_on_process_started)
        ili_executable.stderr.connect(self._log_on_stderr)

    def _disconnect_ili_executable_signals(self, ili_executable):
        ili_executable.process_started.disconnect(self.process_started)
        ili_executable.stderr.disconnect(self.stderr)
        ili_executable.stdout.disconnect(self.stdout)
        ili_executable.process_finished.disconnect(self.process_finished)

        ili_executable.process_started.disconnect(self._log_on_process_started)
        ili_executable.stderr.disconnect(self._log_on_stderr)

    def _log_on_process_started(self, command):
        self._log += command + "\n"

    def _log_on_stderr(self, text):
        self._log += text
