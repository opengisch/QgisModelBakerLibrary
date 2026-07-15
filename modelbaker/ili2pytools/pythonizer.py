"""
Metadata:
    Creation Date: 2026-07-07
    Copyright: (C) 2026 by Dave Signer
    Contact: david@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""
import os

from modelbaker.libs.ili2py.interfaces.interlis.interlis_24.ilismeta.ilismeta16_2022_10_10.enum_type import (
    EnumType,
)
from modelbaker.libs.ili2py.mappers.helpers import Index
from modelbaker.libs.ili2py.readers.interlis_24.ilismeta16.xsdata import Imd16Reader
from modelbaker.libs.ili2py.writers.py.python_structure import Enumeration, Library


class BakerPyIndex(Index):
    """Bridge to ili2py, subclassing the ili2py ``Index`` class.

    Provides methods to return objects such as the library or enumerations,
    as well as convenience methods. Does not override any base class behavior.
    """

    def __init__(self, metamodel):
        self.metamodel = metamodel
        super().__init__(self.metamodel.datasection)

    @classmethod
    def from_imd(cls, imd_path: str):
        """Factory method to parse and instantiate itself.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is empty or invalid to read.
        """
        if not os.path.exists(imd_path):
            raise FileNotFoundError(f"IMD file not found at: {imd_path}")

        if os.path.getsize(imd_path) == 0:
            raise ValueError(f"IMD file is empty: {imd_path}")

        try:
            reader = Imd16Reader()
            metamodel = reader.read(imd_path)

            if not metamodel or not hasattr(metamodel, "datasection"):
                raise ValueError("Invalid IMD structure: missing datasection.")
            return cls(metamodel)

        except Exception as e:
            raise ValueError(f"Failed to parse IMD file: {e}") from e

    # get object functions
    def base_index_object(
        self,
    ) -> Index:
        """Returns a plain ``Index`` built from the metamodel data section.

        Returns:
            The base index object.
        """
        return Index(self.metamodel.datasection)

    def library_object(
        self,
    ) -> Library:
        """Returns the ``Library`` object built from the metamodel.

        Returns:
            The library object.
        """
        library_name = self.types_bucket["Model"][-1].name
        library = Library.from_imd(
            self.metamodel.datasection.ModelData, self, library_name
        )
        return library

    def enumeration_object(self, type_object: EnumType) -> Enumeration:
        """Returns the enumeration for the given enum type.

        Args:
            type_object: The enum type to build the enumeration from.

        Returns:
            The corresponding enumeration object.
        """
        enumeration = Enumeration.from_imd(type_object, self)
        return enumeration

    @property
    def data_unit_supers(self) -> dict:
        """Maps basket tids to their parents via ``<IlisMeta16:Super>``.

        Returns:
            A dict mapping a basket tid to its parent basket tid.
        """
        return self._supers("DataUnit")

    @property
    def enumeration_supers(self) -> dict:
        """Maps object tids to their parents via ``<IlisMeta16:Super>``.

        Returns:
            A dict mapping an object tid to its parent object tid.
        """
        return self._supers("EnumType")

    def _supers(self, type_name: str, package_elements_only: bool = True) -> dict:
        """Maps an element tid to its parent tid via ``<IlisMeta16:Super>``.

        Args:
            type_name: The type to inspect (e.g. ``DataUnit`` or ``EnumType``).
            package_elements_only: If True, only elements assigned to a package are considered.

        Returns:
            A dict mapping an element tid to its parent tid.
        """
        result = {}
        for element in self.types_bucket.get(type_name, []):
            in_package = getattr(element, "element_in_package", None)
            if package_elements_only and not in_package:
                continue
            super_ref = getattr(element, "super", None) or getattr(
                element, "super_value", None
            )
            if super_ref:
                result[element.tid] = super_ref.ref
        return result

    def languages(self, model_names: list = None) -> list:
        """Returns the languages of the given models.

        Args:
            model_names: The models to consider. If None, all models are considered.

        Returns:
            A list of language codes.
        """
        languages = []
        for model in self.types_bucket.get("Model", []):
            if model_names and model.name not in model_names:
                continue
            if model.language and model.language not in languages:
                languages.append(model.language)
        return languages

    def attribute_type(self, attribute_iliname: str) -> object:
        """Returns the type object for the given attribute.

        Args:
            attribute_iliname: The ili name of the attribute.

        Returns:
            The attribute's type object.
        """
        attribute_object = self.index.get(attribute_iliname)
        attribute_type_oid = attribute_object.type_value.ref
        return self.index.get(attribute_type_oid)

    def relevant_topics(self, model_name: str = None) -> set:
        """Returns the relevant topics, including extended and dependent topics.

        Args:
            model_name: The model to limit to. If None, all topics are returned.

        Returns:
            A set of topic names.
        """
        relevant_topics_set = set()
        if not model_name:
            # if not limited to the relevant topics, get all the topics
            relevant_topics_set = {
                topic
                for topics in self.submodel_in_package.values()
                for topic in topics
            }
        else:
            relevant_topics_set = set(self.submodel_in_package.get(model_name, []))

        # get the super and dependency mappings
        supers = self.data_unit_supers
        dependencies = self.dependency_depends_on

        # make a mapping from baskets to topics
        basket_topic_map = {
            basket: topic for topic, basket in self.topic_basket.items()
        }

        # get topics recursively starting with the topics of the model
        self._collect_relevant_topics_recursively(
            relevant_topics_set, supers, dependencies, basket_topic_map
        )

        return relevant_topics_set

    def _collect_relevant_topics_recursively(
        self,
        relevant_topics_set: set,
        supers: dict,
        dependencies: dict,
        basket_topic_map: dict,
    ):
        """Recursively adds relevant topics from super and dependency relationships.

        Updates ``relevant_topics_set`` in place. Following parent topics (via ``supers``)
        and dependency topics (via ``dependencies``).

        Args:
            relevant_topics_set: The set of topics to extend in place.
            supers: Mapping of basket tid to parent basket tid.
            dependencies: Mapping of basket tid to dependency basket tids.
            basket_topic_map: Mapping of basket tid to topic name.
        """
        found_topics = set()
        for topic in relevant_topics_set:
            basket = self.topic_basket.get(topic)
            if not basket:
                continue
            if basket in supers:
                # only one super topic
                found_topics.add(basket_topic_map.get(supers[basket]))
            # mulitple dependencies possible
            dependency_topics = {
                basket_topic_map.get(dependency_basket)
                for dependency_basket in dependencies.get(basket, [])
            }
            found_topics.update(dependency_topics)

        if found_topics:
            self._collect_relevant_topics_recursively(
                found_topics, supers, dependencies, basket_topic_map
            )
            relevant_topics_set.update(found_topics)

    def relevant_models(self, relevant_topics: set = None) -> set:
        """Returns the relevant models for the given topics.

        Args:
            relevant_topics: The topics to consider. If None, all models are returned.

        Returns:
            A set of model names.
        """
        # if not limited to the relevant topics, get all the models directly
        if not relevant_topics:
            return set(self.models)

        relevant_models = {
            model
            for model, topics in self.submodel_in_package.items()
            if any(topic in relevant_topics for topic in topics)
        }
        return relevant_models

    def relevant_classes(self, relevant_topics: set = None) -> set:
        """Returns the relevant classes for the given topics.

        Args:
            relevant_topics: The topics to consider. If None, all classes are returned.

        Returns:
            A set of class tids.
        """
        # if not limited to the relevant topics, get all the topics
        if not relevant_topics:
            relevant_topics = {
                topic
                for topics in self.submodel_in_package.values()
                for topic in topics
            }

        topic_baskets_map = self.topic_basket
        relevant_baskets = [topic_baskets_map.get(topic) for topic in relevant_topics]

        # get all the relevant classes by checking if they are allowed in the data unit
        relevant_classes = set()
        all_elements = self.allowed_in_basket_of_data_unit
        for element_basket in all_elements.keys():
            if element_basket in relevant_baskets:
                relevant_classes.update(all_elements[element_basket])
        return relevant_classes

    def relevant_geometric_attributes_per_class(
        self, relevant_topics: set = None
    ) -> dict:
        """Returns the geometric attributes per class for the given topics.

        Args:
            relevant_topics: The topics to consider. If None, all classes are considered.

        Returns:
            A dict mapping a class tid to a list of its geometric attribute tids.
        """
        relevant_classes = self.relevant_classes(relevant_topics)
        geometric_classes = self.geometric_classes
        relevant_geometric_attributes_per_class = {}
        for geometric_classname in geometric_classes.keys():
            if geometric_classname in relevant_classes:
                relevant_geometric_attributes_per_class[
                    geometric_classname
                ] = geometric_classes[geometric_classname]
        return relevant_geometric_attributes_per_class

    def relevant_enumeration_definitions(self, relevant_topics: set = None) -> set:
        """Returns the tids of enum types used as attribute types in the given topics.

        Args:
            relevant_topics: The topics to consider. If None, all classes are considered.

        Returns:
            A set of enum type tids.
        """
        relevant_classes = self.relevant_classes(relevant_topics)

        enum_tids = {
            enum_type.tid for enum_type in self.types_bucket.get("EnumType", [])
        }
        result = set()
        for attribute in self.types_bucket.get("AttrOrParam", []):
            attr_parent = getattr(attribute, "attr_parent", None)
            if not attr_parent or attr_parent.ref not in relevant_classes:
                continue
            type_ref = getattr(attribute, "type_value", None)
            if type_ref and type_ref.ref in enum_tids:
                result.add(type_ref.ref)
        return result
