from ili2py.mappers.helpers import Index
from qgis.PyQt.QtCore import QFile, QObject

from ..utils.globals import default_log_function


class SettingsProphet(QObject):
    def __init__(self, index: Index, models: list, log_function=None) -> None:
        QObject.__init__(self)

        self.log_function = log_function if log_function else default_log_function

        if not log_function:
            self.log_function = default_log_function

        self.index = index
        self.models = models

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
        # get all the geometric attributes of the relevant classes
        relevant_geometric_attributes = []
        relevant_geometric_attributes_per_class = (
            self._relevant_geometric_attributes_per_class()
        )
        for relevant_classname in relevant_geometric_attributes_per_class.keys():
            relevant_geometric_attributes += relevant_geometric_attributes_per_class[
                relevant_classname
            ]

        # get the line form of the relevant geometry attributes
        line_forms = self.index.geometric_attributes_line_form
        line_forms_of_interest = []
        for attribute in line_forms.keys():
            if attribute in relevant_geometric_attributes:
                line_forms_of_interest += line_forms[attribute]

        return bool(
            "INTERLIS.ARCS" in line_forms_of_interest
            or "ARCS" in line_forms_of_interest
        )

    def has_multiple_geometrie_columms(self):
        """
        Multiple geometry columns in any classes of the model or imported models.
        """
        relevant_geometric_attributes_per_class = (
            self._relevant_geometric_attributes_per_class()
        )
        if any(
            len(columns) > 1
            for columns in relevant_geometric_attributes_per_class.values()
        ):
            return True
        return False

    def multi_geometry_structures_on_23(self):
        """
        Multi geometry structures in INTERLIS 23..
        """
        return False

    def _relevant_classes(self):
        # get the relevant baskets of the models
        relevant_topics = []
        all_topics = self.index.submodel_in_package
        for model in self.models:
            if model in all_topics.keys():
                relevant_topics += all_topics[model]
        topic_baskets_map = self.index.topic_basket
        relevant_baskets = [topic_baskets_map.get(topic) for topic in relevant_topics]

        # get all the relevant classes by checking if they are allowed in the data unit
        relevant_classes = []
        all_elements = self.index.allowed_in_basket_of_data_unit
        for element_basket in all_elements.keys():
            if element_basket in relevant_baskets:
                relevant_classes += all_elements[element_basket]
        return relevant_classes

    def _relevant_geometric_attributes_per_class(self):
        relevant_classes = self._relevant_classes()
        geometric_classes = self.index.geometric_classes
        relevant_geometric_attributes_per_class = {}
        for geometric_classname in geometric_classes.keys():
            if geometric_classname in relevant_classes:
                relevant_geometric_attributes_per_class[
                    geometric_classname
                ] = geometric_classes[geometric_classname]
        return relevant_geometric_attributes_per_class

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
