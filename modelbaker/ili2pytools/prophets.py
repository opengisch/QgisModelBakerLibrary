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

from qgis.PyQt.QtCore import QObject

from modelbaker.ili2pytools.pythonizer import BakerPyIndex

from ..utils.globals import default_log_function


class ModelProphet(QObject):
    """Provides model insights derived from a ``BakerPyIndex`` for a given model."""

    def __init__(
        self,
        index: BakerPyIndex,
        model_name: str = None,
        model_blacklist: list = None,
        log_function=None,
    ) -> None:
        """Initializes the prophet.

        Args:
            index: The index.
            model_name: The model we require the info for. If None, all models are considered.
            model_blacklist: Model names to exclude (e.g. technical models).
            log_function: Optional logging callback.
        """
        QObject.__init__(self)

        self.log_function = log_function if log_function else default_log_function
        if not log_function:
            self.log_function = default_log_function

        self.index = index
        self.model_name = model_name
        self.model_blacklist = model_blacklist
        self.relevant_topics = self.index.relevant_topics(model_name=self.model_name)

    def has_basket_oids(self) -> bool:
        """Returns whether any relevant topic defines a basket OID."""
        bid_in_topics = self.index.basket_oid_in_submodel

        bid_in_relevant_topics = {
            topic: bid_in_topics[topic]
            for topic in self.relevant_topics
            if topic in bid_in_topics
        }
        if len(bid_in_relevant_topics.keys()):
            return True
        return False

    def has_extended_topics(self) -> bool:
        """Returns whether any relevant topic extends another topic."""
        # check if one of the relevant topics is a parent topic of an extension
        supers = self.index.data_unit_supers
        for topic in self.relevant_topics:
            basket = self.index.topic_basket.get(topic)
            if basket and basket in supers:
                return True
        return False

    def has_enumerations(self) -> bool:
        """Returns whether the relevant models/topics contain enumerations."""
        relevant_enums = self.index.relevant_enumeration_definitions(
            self.relevant_topics
        )
        if relevant_enums:
            return True
        return False

    def has_extended_enumerations(self) -> bool:
        """Returns whether the relevant models/topics contain extended enumerations."""
        supers = self.index.enumeration_supers
        if not supers:
            return False

        relevant_enums = self.index.relevant_enumeration_definitions(
            self.relevant_topics
        )
        for tid in relevant_enums:
            if tid in supers.keys():
                return True
        return False

    def has_arcs(self) -> bool:
        """Returns whether any class in the relevant topics uses arcs."""
        # get all the geometric attributes of the relevant classes
        relevant_geometric_attributes = self._relevant_geometric_attributes()

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

    def has_multiple_geometry_columns(self) -> bool:
        """Returns whether any class in the relevant topics has multiple geometry columns."""
        relevant_geometric_attributes_per_class = (
            self.index.relevant_geometric_attributes_per_class(self.relevant_topics)
        )
        if any(
            len(columns) > 1
            for columns in relevant_geometric_attributes_per_class.values()
        ):
            return True
        return False

    def filtered_models(self) -> set:
        """Returns the models excluding the blacklisted ones.

        Returns:
            A set of model names.
        """
        return set(self.index.models) - set(self.model_blacklist or [])

    def relevant_models(self) -> set:
        """Returns the models according to the relevant topics.

        Returns:
            A set of model names.
        """
        return self.index.relevant_models(self.relevant_topics)

    def filtered_relevant_models(self) -> set:
        """Returns the relevant models according to the relevant topics excluding the blacklisted models.

        Returns:
            A set of model names.
        """
        return set(self.index.relevant_models(self.relevant_topics)) - set(
            self.model_blacklist or []
        )

    def _relevant_geometric_attributes(self) -> list:
        """Returns a flat list of geometric attributes for the relevant topics.

        Returns:
            A list of geometric attribute tids.
        """
        relevant_geometric_attributes = []
        relevant_geometric_attributes_per_class = (
            self.index.relevant_geometric_attributes_per_class(self.relevant_topics)
        )
        for relevant_classname in relevant_geometric_attributes_per_class.keys():
            relevant_geometric_attributes += relevant_geometric_attributes_per_class[
                relevant_classname
            ]
        return relevant_geometric_attributes

    def available_languages(self, models: list = None) -> list:
        """Returns all the found languages of the given models.

        This is relevant when one model is a translation model.

        Args:
            models: The models to consider. If None, all models are considered.

        Returns:
            A list of language codes.
        """
        languages = self.index.languages(models)
        return languages


class SettingsProphet(QObject):
    """Suggests ili2db command settings based on the models properties.
    This Prophet can handle multiple models and will return the union of all relevant settings.
    It uses the ModelProphet to get the relevant information for each model."""

    def __init__(
        self,
        model_indexes: dict[str, BakerPyIndex],
        model_blacklist: list = None,
        log_function=None,
    ) -> None:
        """Initializes the settings prophet.

        Args:
            model_indexes: A dictionary of model indexes, based on str (model_name) -> BakerPyIndex.
            model_blacklist: Model names to exclude (e.g. technical models).
            log_function: Optional logging callback.
        """
        self.model_prophets = {}
        for model_name in model_indexes.keys():
            index = model_indexes[model_name]
            model_prophet = ModelProphet(
                index=index,
                model_name=model_name,
                model_blacklist=model_blacklist,
                log_function=log_function,
            )
            self.model_prophets[model_name] = model_prophet

    def contains_enumerations(self) -> bool:
        """Returns whether any relevant model/topic of one model contains enumerations.

        This is relevant because without enumerations the enumeration ili2db option
        makes no sense.
        """
        for model_prophet in self.model_prophets.values():
            if model_prophet.has_enumerations():
                return True
        return False

    def contains_extended_enumerations(self) -> bool:
        """Returns whether the relevant models/topics of one model contain extended enumerations.

        This is relevant because ``--createEnumTabs`` does not work with smart1
        inheritance when extended enumerations exist.
        """
        for model_prophet in self.model_prophets.values():
            if model_prophet.has_extended_enumerations():
                return True
        return False

    def contains_arcs(self) -> bool:
        """Returns whether any class in the relevant topics of one model uses arcs.

        This is relevant because without arcs the stroke arcs option makes no sense.
        """
        for model_prophet in self.model_prophets.values():
            if model_prophet.has_arcs():
                return True
        return False

    def contains_multiple_geometry_columns(self) -> bool:
        """Returns whether any class in the relevant topics of one model has multiple geometry columns.

        This is relevant because without them the GeoPackage multi geometry option
        makes no sense.
        """
        for model_prophet in self.model_prophets.values():
            if model_prophet.has_multiple_geometry_columns():
                return True
        return False

    def needs_basket_column(self) -> bool:
        """Returns whether a basket column is required in one of the models.

        A basket column is required when a relevant topic defines a basket OID
        or extends another topic.
        This is relevant to know because when one of those is true, the
        ``--createBasketColumn`` option is then not optional.
        """
        for model_prophet in self.model_prophets.values():
            if model_prophet.has_basket_oids() or model_prophet.has_extended_topics():
                return True
        return False

    def language_infos(self) -> tuple[bool, list[str], str | None]:
        """Detects translation state and returns language information.

        Detection is based on comparing all (blacklist-filtered) models and
        languages against the relevant ones. If additional models/languages
        exist, the model is treated as a translation model. If there is more than one
        translated model (what rarely makes sense), the last one is assumed to be the original language.
        This is a heuristic and may not be accurate in all cases.

        Returns:
            A tuple of (is_translation, languages, preferred_language), where
            preferred_language is the assumed original language.
        """
        is_translation = False
        all_languages = []
        preferred_language = None

        for model_prophet in self.model_prophets.values():
            filtered_models = model_prophet.filtered_models()
            relevant_models = model_prophet.relevant_models()
            languages_of_relevant_models = model_prophet.available_languages(
                relevant_models
            )
            languages = model_prophet.available_languages(filtered_models)

            if len(filtered_models) == len(relevant_models) or len(languages) == len(
                languages_of_relevant_models
            ):
                # when there are not more models than the relevant ones, then it is not a translation model.
                # when there are not more languages than the relevant ones, then it is not a translation model.
                is_translation = False
                all_languages.extend(languages)
                preferred_language = None
            else:
                # otherwise we assume it's a translation model and we return the languages
                # and the preferred language (the first one of the ones that are not relevant (because this might be the original)).
                original_languages = []
                for lang in languages:
                    if lang not in languages_of_relevant_models:
                        original_languages.append(lang)
                is_translation = True
                all_languages.extend(languages)
                preferred_language = (
                    original_languages[0] if original_languages else None
                )

        return is_translation, all_languages, preferred_language
