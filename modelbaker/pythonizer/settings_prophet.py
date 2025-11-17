from ili2py.mappers.helpers import Index
from qgis.PyQt.QtCore import QFile, QObject

from ..utils.globals import default_log_function


class SettingsProphet(QObject):
    def __init__(self, index: Index, log_function=None) -> None:
        QObject.__init__(self)

        self.log_function = log_function if log_function else default_log_function

        if not log_function:
            self.log_function = default_log_function

        self.index = index

    def smart_inheritance(self):
        """
        Does it make sense to make any suggestions here? I don't know.
        """
        return True

    def enum_info(self):

        return True

    def has_basket_oids(self):
        """
        Is there any BASKET OID definition in the model.
        """
        bid_in_model = self.index.basket_oid_in_model
        bid_in_topics = self.index.basket_oid_in_submodel
        if len(bid_in_model.keys()) + len(bid_in_topics.keys()):
            return True
        return False

    def has_arcs(self):
        """
        Arcs in any classes of the model or imported models.
        """
        line_forms = self.index.geometric_attributes_line_form
        if any(
            "INTERLIS.ARCS" in forms or "ARCS" in forms for forms in line_forms.values()
        ):
            return True
        return False

    def has_multiple_geometrie_columms(self):
        """
        Multiple geometry columns in any classes of the model or imported models.
        """
        classes_geometries = self.index.geometric_classes
        if any(len(columns) > 1 for columns in classes_geometries.values()):
            return True
        return False

    def multi_geometry_structures_on_23(self):
        """
        Multi geometry structures in INTERLIS 23..
        """
        return False

    def is_translation(self):
        return False


class ProphetTools(QObject):
    def __init__(self, log_function=None) -> None:
        QObject.__init__(self)

        self.log_function = log_function if log_function else default_log_function

    def _multi_geometry_mappings(self, multigeometry_structs):
        entries = []
        for element in multigeometry_structs:
            entries.append("[{}]\n{}".format(element, "test"))
        return "\n".join(entries)

    def temp_meta_attr_file(self, multigeometry_structs):
        temporary_filename = "{}/modelbaker-metaattrs.conf".format(QDir.tempPath())
        temporary_file = QFile(temporary_filename)
        if temporary_file.open(QFile.OpenModeFlag.WriteOnly):
            content = self._multi_geometry_mappings(multigeometry_structs)
            if content:
                temporary_file.write(content).encode("utf-8")
                temporary_file.close()
                return temporary_filename
        return None
