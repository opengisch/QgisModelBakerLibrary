import datetime
import os

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from qgis.core import Qgis
from qgis.PyQt.QtCore import QEventLoop, QFile, QObject, QStandardPaths, QTimer
from QgisModelBaker.libs.modelbaker.iliwrapper import iliexecutable
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2CCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbutils import JavaNotFoundError
from QgisModelBaker.libs.modelbaker.iliwrapper.ilicache import IliModelFileCache
from QgisModelBaker.libs.modelbaker.libs.ili2py.mappers.helpers import Index
from QgisModelBaker.libs.modelbaker.libs.ili2py.readers.interlis_24.ilismeta16.xsdata import (
    Imd16Reader,
)
from QgisModelBaker.libs.modelbaker.libs.ili2py.writers.py import Library

from ..utils.globals import default_log_function


class Pythonizer(QObject):
    def __init__(self, log_function=None) -> None:
        QObject.__init__(self)

        self.log_function = log_function if log_function else default_log_function

        if not log_function:
            self.log_function = default_log_function

    def compile(self, base_configuration, ili_file):
        compiler = iliexecutable.IliCompiler()

        configuration = Ili2CCommandConfiguration()
        configuration.base_configuration = base_configuration
        configuration.ilifile = ili_file
        configuration.imdfile = os.path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.TempLocation
            ),
            "temp_imd_{:%Y%m%d%H%M%S%f}.imd".format(datetime.datetime.now()),
        )

        compiler.configuration = configuration

        compiler.stdout.connect(self.on_ili_stdout)
        compiler.stderr.connect(self.on_ili_stderr)
        compiler.process_started.connect(self.on_ili_process_started)
        compiler.process_finished.connect(self.on_ili_process_finished)
        result = True

        try:
            compiler_result = compiler.run()
            if compiler_result != compiler.SUCCESS:
                result = False
        except JavaNotFoundError as e:
            self.log_function(
                self.tr("Java not found error: {}").format(e.error_string),
                Qgis.MessageLevel.Warning,
            )
            result = False

        return result, compiler.configuration.imdfile

    def pythonize(self, imd_file):
        reader = Imd16Reader()
        metamodel = reader.read(imd_file)
        index = Index(metamodel.datasection)
        library_name = index.types_bucket["Model"][-1].name
        library = Library.from_imd(metamodel.datasection.ModelData, index, library_name)
        return index, library

    def model_files_generated_from_db(self, configuration, model_list):
        model_files = []
        # this could be improved i guess, we already have the models read from the same function. but yes. poc etc.
        db_connector = db_utils.get_db_connector(configuration)
        db_connector.get_models()
        model_records = db_connector.get_models()
        for record in model_records:
            name = record["modelname"].split("{")[0]
            if name in model_list:
                modelfilepath = os.path.join(
                    QStandardPaths.writableLocation(
                        QStandardPaths.StandardLocation.TempLocation
                    ),
                    "temp_{}_{:%Y%m%d%H%M%S%f}.ili".format(
                        name, datetime.datetime.now()
                    ),
                )
                file = QFile(modelfilepath)
                if file.open(QFile.OpenModeFlag.WriteOnly):
                    file.write(record["content"].encode("utf-8"))
                    file.close()
                model_files.append(modelfilepath)
                print(modelfilepath)
        return model_files

    def model_files_from_repo(self, base_configuration, model_list):
        model_file_cache = IliModelFileCache(base_configuration, model_list)
        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        model_file_cache.download_finished_and_model_fresh.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(10000)

        model_file_cache.refresh()
        self.log_function(self.tr("- - Downloading…"))

        # we wait for the download_finished_and_model_fresh signal, because even when the files are local, it should only continue when both is ready
        loop.exec()

        if len(model_file_cache.downloaded_files) == len(model_list):
            self.log_function(self.tr("- - All model files"))
        else:
            missing_file_ids = model_list
            for downloaded_file_id in model_file_cache.downloaded_files:
                if downloaded_file_id in missing_file_ids:
                    missing_file_ids.remove(downloaded_file_id)
            try:
                self.log_function(
                    self.tr(
                        "- - Some model files where not successfully downloaded: {}"
                    ).format(" ".join(missing_file_ids))
                )
            except Exception:
                pass

        return model_file_cache.ilifilelist

    def on_ili_stdout(self, message):
        lines = message.strip().split("\n")
        for line in lines:
            text = f"ili2c: {line}"
            self.log_function(text, Qgis.MessageLevel.Info)

    def on_ili_stderr(self, message):
        lines = message.strip().split("\n")
        for line in lines:
            text = f"ili2c: {line}"
            self.log_function(text, Qgis.MessageLevel.Critical)

    def on_ili_process_started(self, command):
        text = f"ili2c: {command}"
        self.log_function(text, Qgis.MessageLevel.Info)

    def on_ili_process_finished(self, exit_code, result):
        if exit_code == 0:
            text = f"ili2c: Successfully performed command."
            self.log_function(text, Qgis.MessageLevel.Info)
        else:
            text = f"ili2c: Finished with errors: {result}"
            self.log_function(text, Qgis.MessageLevel.Critical)
