"""
/***************************************************************************
                              -------------------
        begin                : 14.9.17
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
import os
import platform
import re
import subprocess
import tempfile
import zipfile

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QColor

from ..utils.qt_utils import NetworkError, download_file
from .globals import DbIliMode
from .ili2dbtools import get_tool_url, get_tool_version


def get_ili2db_bin(tool, db_ili_version, stdout, stderr):
    if tool not in DbIliMode or tool == DbIliMode.ili:
        raise RuntimeError("Tool {} not found".format(tool))

    tool |= (
        DbIliMode.ili
    )  # Regardless of the incoming form (i.e., pg or ili2pg), we need its corresponding ili tool
    tool_name = tool.name  # in fact, we need the name of the ili tool

    ili_tool_version = get_tool_version(tool, db_ili_version)
    ili_tool_url = get_tool_url(tool, db_ili_version)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    ili2db_dir = "{}-{}".format(tool_name, ili_tool_version)

    # the structure changed since 3.12.2
    if is_version_valid(
        ili_tool_version,
        "3.12.2",
        exact_required_version=False,
        module_tested=tool_name,
    ):
        ili2db_file = os.path.join(
            dir_path,
            "bin",
            ili2db_dir,
            "{tool}-{version}.jar".format(tool=tool_name, version=ili_tool_version),
        )
    else:
        ili2db_file = os.path.join(
            dir_path,
            "bin",
            ili2db_dir,
            "{tool}-{version}/{tool}.jar".format(
                tool=tool_name, version=ili_tool_version
            ),
        )

    if not os.path.isfile(ili2db_file):
        try:
            os.makedirs(os.path.join(dir_path, "bin", ili2db_dir), exist_ok=True)
        except FileExistsError:
            pass

        tmpfile = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)

        stdout.emit(
            QCoreApplication.translate(
                "ili2dbutils",
                "Downloading {} version {}…".format(tool_name, ili_tool_version),
            )
        )

        try:
            download_file(
                ili_tool_url,
                tmpfile.name,
                on_progress=lambda received, total: stdout.emit("."),
            )
        except NetworkError as e:
            stderr.emit(
                QCoreApplication.translate(
                    "ili2dbutils",
                    'Could not download {tool_name}\n\n  Error: {error}\n\nFile "{file}" not found. Please download and extract <a href="{ili2db_url}">{tool_name}</a>'.format(
                        tool_name=tool_name,
                        ili2db_url=ili_tool_url,
                        error=e.msg,
                        file=ili2db_file,
                    ),
                )
            )
            return None

        try:
            with zipfile.ZipFile(tmpfile.name, "r") as z:
                z.extractall(os.path.join(dir_path, "bin", ili2db_dir))
        except zipfile.BadZipFile:
            # We will realize soon enough that the files were not extracted
            pass

        if not os.path.isfile(ili2db_file):
            stderr.emit(
                QCoreApplication.translate(
                    "ili2dbutils",
                    'File "{file}" not found. Please download and extract <a href="{ili2db_url}">{tool_name}</a>.'.format(
                        tool_name=tool_name, file=ili2db_file, ili2db_url=ili_tool_url
                    ),
                )
            )
            return None

    return ili2db_file


def get_all_modeldir_in_path(path, lambdafunction=None):
    all_subdirs = [path[0] for path in os.walk(path)]  # include path
    # Make sure path is included, it can be a special string like `%XTF_DIR`
    modeldirs = [path]
    for subdir in all_subdirs:
        if os.path.isdir(subdir) and len(glob.glob(subdir + "/*.ili")) > 0:
            if lambdafunction is not None:
                lambdafunction(subdir)
            modeldirs += [subdir]

    # Remove duplicates
    modeldirs = list(dict.fromkeys(modeldirs))
    return ";".join(modeldirs)


def color_log_text(text, txt_edit):
    textlines = text.splitlines()
    for textline in textlines:
        if textline.startswith("Warning:"):
            txt_edit.setTextColor(QColor("#FFBF00"))
            txt_edit.append(textline)
        elif "error" in textline.lower() or "failed" in textline.lower():
            txt_edit.setTextColor(QColor("#aa2222"))
            txt_edit.append(textline)
        else:
            txt_edit.setTextColor(QColor("#2a2a2a"))
            txt_edit.append(textline)


def get_java_path(base_configuration):
    """
    Delivers the path to a Java 8 installation or raises a JavaNotFoundError

    1. If the java path is set by the user, this one will be taken. No other paths are returned.
    2. Finds additional java paths in the enfironment variable JAVA_HOME (suffised with and without bin/java
    3. On Windows looks up the global system environment variable for PATH because this is mangled by
       the QGIS startup script.
    """

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    # This function is like the linux which command
    def which(program):

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            # for path in os.environ["PATH"].split(os.pathsep):
            for path in getenv_system("PATH").split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
        return None

    # This function gets a system variable
    # it was necessary to use this instead of os.environ["PATH"] because QGIS overwrites the path variable
    # the win32 libraries appear not to be part of the standard python install, but they are included in the
    # python version that comes with QGIS
    def getenv_system(varname, default=""):
        import winreg

        v = default
        try:
            rkey = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment",
            )
            try:
                v = str(winreg.QueryValueEx(rkey, varname)[0])
                v = winreg.ExpandEnvironmentStrings(v)
            except:
                pass
        finally:
            winreg.CloseKey(rkey)
        return v

    if base_configuration.java_path:
        # A java path is configured: respect it no mather what
        return base_configuration.java_path
    else:
        # By default try JAVA_HOME and PATH
        java_paths = []
        if "JAVA_HOME" in os.environ:
            paths = os.environ["JAVA_HOME"].split(";")
            for path in paths:
                # Include double check as java can be found on different paths
                # /usr/lib/jvm/java8oracle/bin/java
                java_paths += [
                    os.path.join(path.replace('"', "").replace("'", ""), "bin", "java")
                ]
                # C:\ProgramData\Oracle\Java\javapath\java
                java_paths += [
                    os.path.join(path.replace('"', "").replace("'", ""), "java")
                ]

        if platform.system() == "Windows":
            java_path = which("java.exe")
            if java_path:
                java_paths += [java_path]
        else:
            java_paths += ["java"]

        version_output = None
        java_version_re = re.compile(r'.*version "([0-9\.]+).*')
        for java_path in java_paths:
            try:
                startupinfo = None
                if platform.system() == "Windows":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.Popen(
                    [java_path, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                )
                output, err = p.communicate()
                version_output = err.decode("utf-8")
                java_version = java_version_re.match(version_output)
                if is_version_valid(
                    java_version.group(1),
                    "1.8.0",
                    exact_required_version=False,
                    module_tested="Java",
                ):
                    return java_path
            except FileNotFoundError:
                pass

        raise JavaNotFoundError(version_output)


def is_version_valid(
    current_version,
    min_required_version,
    exact_required_version=False,
    module_tested="",
):
    """
    Generic one, it helps us to validate whether a current version is greater or equal to a min_required_version or,
    if exact_required_version, if a current version is exactly the required one.

    Borrowed from 'Asistente LADM-COL'.

    :param current_version: String, in the form 2.9.5
    :param min_required_version: String, in the form 2.9.5
    :param exact_required_version: Boolean, if true, only the exact version is valid. If False, the min_required_version
                                   or any greater version will be accepted.
    :param module_tested: String, only for displaying a log with context
    :return: Whether the current version is valid or not
    """
    if current_version is None:
        return False

    current_version_splitted = current_version.split(".")
    if (
        len(current_version_splitted) < 4
    ):  # We could need 4 places for our custom plugin versions
        current_version_splitted = current_version_splitted + ["0", "0", "0", "0"]
        current_version_splitted = current_version_splitted[:4]

    min_required_version_splitted = min_required_version.split(".")
    if len(min_required_version_splitted) < 4:
        min_required_version_splitted = min_required_version_splitted + [
            "0",
            "0",
            "0",
            "0",
        ]
        min_required_version_splitted = min_required_version_splitted[:4]

    if exact_required_version:
        return min_required_version_splitted == current_version_splitted

    else:  # Min version and subsequent versions should work
        for i in range(len(current_version_splitted)):
            if int(current_version_splitted[i]) < int(min_required_version_splitted[i]):
                return False
            elif int(current_version_splitted[i]) > int(
                min_required_version_splitted[i]
            ):
                return True

    return True


class JavaNotFoundError(FileNotFoundError):
    """
    This error is raised when java could not be detected on the system.
    When the java_version variable is set, java (or any executable) was found
    but in the wrong version.
    If not, no executable was found at all.
    """

    JAVA_DOWNLOAD_URL = "https://adoptium.net/download/"
    PLUGIN_CONFIGURATION_URL = "https://opengisch.github.io/QgisModelBaker/user_guide/plugin_configuration/#interlis-settings"

    def __init__(self, java_version=None):
        super().__init__()

        if java_version:
            self.java_version = java_version
        else:
            self.java_version = None

    @property
    def html_java_version(self):
        if self.java_version:
            return "<br/>".join(self.java_version.splitlines())
        else:
            return ""

    @property
    def error_string(self):
        if self.java_version:
            return QCoreApplication.translate(
                "ili2dbutils",
                'Wrong java version found. Qgis Model Baker requires at least java version 8. Please <a href="{0}">install Java</a> and or <a href="{1}">configure a custom java path</a>.<br/><br/>Java Version:<br/>{2}',
            ).format(
                JavaNotFoundError.JAVA_DOWNLOAD_URL,
                JavaNotFoundError.PLUGIN_CONFIGURATION_URL,
                self.html_java_version,
            )
        else:
            return QCoreApplication.translate(
                "ili2dbutils",
                'Java 8 could not be found. Please <a href="{}">install Java</a> and or <a href="{}">configure a custom java path</a>.'.format(
                    JavaNotFoundError.JAVA_DOWNLOAD_URL,
                    JavaNotFoundError.PLUGIN_CONFIGURATION_URL,
                ),
            )
