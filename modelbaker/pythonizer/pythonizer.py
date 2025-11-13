import datetime
import os

from qgis.core import Qgis
from qgis.PyQt.QtCore import QFile, QObject, QStandardPaths

from ..iliwrapper import iliexecutable
from ..iliwrapper.ili2dbconfig import Ili2CCommandConfiguration
from ..iliwrapper.ili2dbutils import JavaNotFoundError
from ..libs.ili2py.mappers.helpers import Index
from ..libs.ili2py.readers.interlis_24.ilismeta16.xsdata import Imd16Reader
from ..libs.ili2py.writers.py.python_structure import Library
from ..utils import db_utils
from ..utils.globals import default_log_function
from ..utils.qt_utils import NetworkError, download_file


class Pythonizer(QObject):
    """
    This is pure Tinkerlis. pythonizer function does the ili2py stuff. The rest is kind of a utils api.
    """

    def __init__(self, log_function=None) -> None:
        QObject.__init__(self)

        self.log_function = log_function if log_function else default_log_function

        if not log_function:
            self.log_function = default_log_function

    def pythonize(self, imd_file):
        reader = Imd16Reader()
        metamodel = reader.read(imd_file)
        index = Index(metamodel.datasection)
        library_name = index.types_bucket["Model"][-1].name
        library = Library.from_imd(metamodel.datasection.ModelData, index, library_name)
        return index, library

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

    def model_files_generated_from_db(self, configuration, model_list=[]):
        model_files = []
        # this could be improved i guess, we already have the models read from the same function. but yes. poc etc.
        db_connector = db_utils.get_db_connector(configuration)
        db_connector.get_models()
        model_records = db_connector.get_models()
        for record in model_records:
            name = record["modelname"].split("{")[0]
            # on an empty model_list we create a file for every found model
            if len(model_list) == 0 or name in model_list:
                modelfilepath = self._temp_ilifile(name)
                file = QFile(modelfilepath)
                if file.open(QFile.OpenModeFlag.WriteOnly):
                    file.write(record["content"].encode("utf-8"))
                    file.close()
                model_files.append(modelfilepath)
                print(modelfilepath)
        return model_files

    def download_file(self, modelname, url):
        modelfilepath = self._temp_ilifile(modelname)
        try:
            download_file(
                url,
                modelfilepath,
                on_progress=lambda received, total: self.on_ili_stdout("."),
            )
        except NetworkError:
            self.on_ili_stderr(f"Could not download model {modelname} from {url}")
            return None
        return modelfilepath

    def _temp_ilifile(self, name):
        return os.path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.TempLocation
            ),
            "temp_{}_{:%Y%m%d%H%M%S%f}.ili".format(name, datetime.datetime.now()),
        )

    def on_ili_stdout(self, message):
        lines = message.strip().split("\n")
        for line in lines:
            text = f"pythonizer: {line}"
            self.log_function(text, Qgis.MessageLevel.Info)

    def on_ili_stderr(self, message):
        lines = message.strip().split("\n")
        for line in lines:
            text = f"pythonizer: {line}"
            self.log_function(text, Qgis.MessageLevel.Critical)

    def on_ili_process_started(self, command):
        text = f"pythonizer: {command}"
        self.log_function(text, Qgis.MessageLevel.Info)

    def on_ili_process_finished(self, exit_code, result):
        if exit_code == 0:
            text = f"pythonizer: Successfully performed command."
            self.log_function(text, Qgis.MessageLevel.Info)
        else:
            text = f"pythonizer: Finished with errors: {result}"
            self.log_function(text, Qgis.MessageLevel.Critical)
