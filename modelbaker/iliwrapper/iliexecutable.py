"""
Metadata:
    Creation Date: 2023-09-09
    Copyright: (C) 2020 by Yesid Polania
    Contact: yesidpol.3@gmail.com

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""
import functools
import locale
import re
from abc import abstractmethod
from typing import Optional

from qgis.PyQt.QtCore import QEventLoop, QObject, QProcess, pyqtSignal

from ..utils.qt_utils import AbstractQObjectMeta
from .ili2dbargs import get_ili2db_args
from .ili2dbconfig import Ili2CCommandConfiguration, Ili2DbCommandConfiguration
from .ili2dbutils import JavaNotFoundError, get_ili2c_bin, get_ili2db_bin, get_java_path


class IliExecutable(QObject, metaclass=AbstractQObjectMeta):
    SUCCESS = 0
    ERROR = 1000
    ILI2_NOT_FOUND = 1001

    stdout = pyqtSignal(str)
    stderr = pyqtSignal(str)
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(int, int)
    cancel_process = pyqtSignal()

    # supertolerant done pattern
    _done_pattern = re.compile(r"Info: \.\.\..*done")
    __result = None

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.filename = None
        self.tool = None
        self.configuration = self._create_config()
        _, self.encoding = locale.getlocale()

        # Lets python try to determine the default locale
        if not self.encoding:
            _, self.encoding = locale.getdefaultlocale()

        # This might be unset
        # (https://stackoverflow.com/questions/1629699/locale-getlocale-problems-on-osx)
        if not self.encoding:
            self.encoding = "UTF8"

    @abstractmethod
    def _create_config(self) -> Ili2DbCommandConfiguration | Ili2CCommandConfiguration:
        """Creates the configuration that will be used by *run* method.

        Returns:
            Ili2DbCommandConfiguration or Ili2CCommandConfiguration: ili2db/ili2c configuration
        """

    @abstractmethod
    def _args(self, hide_password: bool) -> list:
        """Gets the list of ili2db/ili2c arguments from configuration.

        Args:
            hide_password (bool): *True* to mask the password, *False* otherwise.

        Returns:
            list: ili2db/ili2c arguments list.
        """

    @abstractmethod
    def _ili2_jar_arg(self):
        """Gets the list of arguments to run ili2db/ili2c jar.

        Returns:
            list: ili2db/ili2c jar arguments list.
        """

    def _escaped_arg(self, argument=str) -> str:
        if '"' in argument:
            argument = argument.replace('"', '"""')
        if " " in argument:
            argument = '"' + argument + '"'
        return argument

    def command(self, hide_password: bool = False) -> str:
        ili2_jar_arg = self._ili2_jar_arg()
        if ili2_jar_arg == self.ILI2_NOT_FOUND:
            return "ili2 tool not found!"

        args = self._args(hide_password)
        java_path = self._escaped_arg(
            get_java_path(self.configuration.base_configuration)
        )
        command_args = ili2_jar_arg + args
        valid_args = []
        for command_arg in command_args:
            valid_args.append(self._escaped_arg(command_arg))

        command = java_path + " " + " ".join(valid_args)

        return command

    def command_with_password(self, edited_command: str) -> str:
        if "--dbpwd ******" in edited_command:
            args = self._args(False)
            i = args.index("--dbpwd")
            edited_command = edited_command.replace(
                "--dbpwd ******", "--dbpwd " + args[i + 1]
            )
        return edited_command

    def command_without_password(self, edited_command: Optional[str] = None) -> str:
        if not edited_command:
            return self.command(True)
        regex = re.compile("--dbpwd [^ ]*")
        match = regex.match(edited_command)
        if match:
            edited_command = edited_command.replace(match.group(1), "--dbpwd ******")
        return edited_command

    def run(self, edited_command: Optional[str] = None) -> int:
        proc = QProcess()
        self.cancel_process.connect(proc.terminate)
        proc.readyReadStandardError.connect(
            functools.partial(self.stderr_ready, proc=proc)
        )
        proc.readyReadStandardOutput.connect(
            functools.partial(self.stdout_ready, proc=proc)
        )

        if not edited_command:
            ili2db_jar_arg = self._ili2_jar_arg()
            if ili2db_jar_arg == self.ILI2_NOT_FOUND:
                return self.ILI2_NOT_FOUND
            args = self._args(False)
            java_path = get_java_path(self.configuration.base_configuration)
            proc.start(java_path, ili2db_jar_arg + args)
        else:
            proc.start(self.command_with_password(edited_command))

        if not proc.waitForStarted():
            proc = None

        if not proc:
            raise JavaNotFoundError()

        self.process_started.emit(self.command_without_password(edited_command))

        self.__result = self.ERROR

        loop = QEventLoop()
        proc.finished.connect(loop.exit)
        loop.exec()

        self.process_finished.emit(proc.exitCode(), self.__result)
        return self.__result

    def stderr_ready(self, proc: QProcess) -> None:
        text = bytes(proc.readAllStandardError()).decode(self.encoding)

        if self._done_pattern.search(text):
            self.__result = self.SUCCESS

        self.stderr.emit(text)

    def stdout_ready(self, proc: QProcess) -> None:
        text = bytes(proc.readAllStandardOutput()).decode(self.encoding)
        self.stdout.emit(text)


class Ili2DbExecutable(IliExecutable):
    """Executes operation on ili2db."""

    _done_pattern = re.compile(r"Info: \.\.\.([a-zA-Z]+ )?done")

    def __init__(self, parent=None):
        super().__init__(parent)

    def _args(self, hide_password):
        """Gets the list of ili2db arguments from configuration.

        Args:
            hide_password (bool): *True* to mask the password, *False* otherwise.

        Returns:
            list: ili2db arguments list.
        """
        self.configuration.tool = self.tool

        return get_ili2db_args(self.configuration, hide_password)

    def _ili2_jar_arg(self):
        """Locates and creates the Java entrypoint arguments array targeting the ili2db jar.

        Returns:
            list or int: Executable jar target arguments list, or a missing constant code.
        """
        ili2db_bin = get_ili2db_bin(
            self.tool, self._get_ili2db_version(), self.stdout, self.stderr
        )
        if not ili2db_bin:
            return self.ILI2_NOT_FOUND
        return ["-jar", ili2db_bin]

    def _get_ili2db_version(self):
        return self.configuration.db_ili_version


class Ili2CExecutable(IliExecutable):
    """Executes operation on ili2c."""

    _done_pattern = re.compile(r"Info: \.\.\.compiler run done.*$")

    def __init__(self, parent=None):
        super().__init__(parent)

    def _args(self, _param):
        """Gets the list of ili2db arguments from configuration.

        Args:
            _param (bool): Unused parameter, kept for interface compatibility.

        Returns:
            list: ili2c arguments list.
        """
        return self.configuration.to_ili2c_args()

    def _ili2_jar_arg(self):
        ili2c_bin = get_ili2c_bin(self.stdout, self.stderr)
        if not ili2c_bin:
            return self.ILI2_NOT_FOUND
        return ["-jar", ili2c_bin]
