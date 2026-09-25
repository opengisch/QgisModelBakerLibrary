"""
Metadata:
    Creation Date: 2026-09-27
    Copyright: (C) 2026 by Dave Signer
    Contact: david@opengis.ch

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""

import os
import uuid
from typing import Any, Optional

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputBoolean,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtGui import QIcon

from ..iliwrapper.globals import DbIliMode
from ..iliwrapper.ili2dbconfig import Ili2DbCommandConfiguration
from ..utils import db_utils
from .ili2db_algorithm import Ili2gpkgAlgorithm, Ili2pgAlgorithm
from .ili2db_operating import ProcessOperatorBase


class ProcessBasketCreator(ProcessOperatorBase):

    DATASET = "DATASET"
    RELEVANTONLY = "RELEVANTONLY"
    BIDTEMPLATE = "BIDTEMPLATE"

    # Result
    ISVALID = "ISVALID"

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def basket_input_params(self):
        params = []

        dataset_param = QgsProcessingParameterString(
            self.DATASET, self.tr("Dataset Name"), defaultValue="Baseset", optional=True
        )
        dataset_param.setHelp(
            self.tr(
                "The name of the dataset for which the default baskets should be created. If not existing, the dataset will be created."
            )
        )
        params.append(dataset_param)

        relevant_param = QgsProcessingParameterBoolean(
            self.RELEVANTONLY,
            self.tr("Create baskets for relevant topics only"),
            defaultValue=True,
        )
        relevant_param.setHelp(
            self.tr(
                "When topics are considered as relevant (based on their inheritance), only baskets for relevant topics will be created. Otherwise, baskets for all topics will be created."
            )
        )
        params.append(relevant_param)

        bid_template_param = QgsProcessingParameterString(
            self.BIDTEMPLATE,
            self.tr("Basket ID Template"),
            defaultValue=None,
            optional=True,
        )
        bid_template_param.setHelp(
            self.tr(
                r"Expression to generate the Basket ID. You can use text and {t_id} as placeholder for the current t_id. If not provided, an ID will be generated according to the BID domain if existing."
            )
        )
        params.append(bid_template_param)

        return params

    def basket_output_params(self):
        params = []

        params.append(
            QgsProcessingOutputBoolean(self.ISVALID, self.tr("Baskets create result"))
        )

        return params

    def initParameters(self):
        for basket_input_param in self.basket_input_params():
            self.parent.addParameter(basket_input_param)
        for basket_output_param in self.basket_output_params():
            self.parent.addOutput(basket_output_param)

        for connection_input_param in self.parent.connection_input_params():
            self.parent.addParameter(connection_input_param)
        for connection_output_param in self.parent.connection_output_params():
            self.parent.addOutput(connection_output_param)

    def _get_dataset_tid(self, db_connector, dataset_name):
        datasets_info = db_connector.get_datasets_info()
        dataset_tid = -1
        for dataset_record in datasets_info:
            if dataset_record["datasetname"] == dataset_name:
                dataset_tid = dataset_record["t_id"]
                break
        return dataset_tid

    def run(self, configuration, parameters, context, feedback):
        dataset_name = self.parent.parameterAsString(parameters, self.DATASET, context)
        relevant_only = self.parent.parameterAsBool(
            parameters, self.RELEVANTONLY, context
        )
        bid_template = self.parent.parameterAsString(
            parameters, self.BIDTEMPLATE, context
        )

        db_connector = db_utils.get_db_connector(configuration)

        dataset_tid = self._get_dataset_tid(db_connector, dataset_name)
        if dataset_tid < 0:
            feedback.pushInfo(self.tr("Dataset needs to be created first."))
            res, msg = db_connector.create_dataset(dataset_name)
            if not res:
                feedback.pushWarning(
                    self.tr("Dataset creation failed: {msg}").format(msg=msg)
                )
                return {self.ISVALID: False}
            else:
                feedback.pushInfo(self.tr("Dataset created successfully."))
                dataset_tid = self._get_dataset_tid(db_connector, dataset_name)
        else:
            feedback.pushInfo(self.tr("Found existing dataset."))

        existing_baskets = set()
        for basket_record in db_connector.get_baskets_info():
            if basket_record["datasetname"] == dataset_name:
                existing_baskets.add(basket_record["topic"])

        feedback.pushInfo(self.tr("Creating baskets:"))

        for topic_record in db_connector.get_topics_info():
            topic_key = f"{topic_record['model']}.{topic_record['topic']}"
            if topic_record["relevance"] == 0 and relevant_only:
                feedback.pushInfo(
                    self.tr("Skipping non-relevant topic {topic_key}.").format(
                        topic_key=topic_key
                    )
                )
                continue
            if topic_key in existing_baskets:
                feedback.pushInfo(
                    self.tr("Basket for {topic_key} already exists.").format(
                        topic_key=topic_key
                    )
                )
                continue
            bid_value = None
            if bid_template:
                bid_value = bid_template.format(
                    t_id=f"{db_connector.get_next_ili2db_sequence_value()}"
                )
                feedback.pushInfo(
                    self.tr(
                        "Generated Basket ID value based on template: {bid_value}"
                    ).format(bid_value=bid_value)
                )
            else:
                bid_domain = topic_record["bid_domain"]
                if bid_domain == "INTERLIS.UUIDOID":
                    bid_value = str(uuid.uuid4())
                elif bid_domain == "INTERLIS.STANDARDOID":
                    bid_value = (
                        f"%change%{db_connector.get_next_ili2db_sequence_value():08}"
                    )
                elif bid_domain == "INTERLIS.I32OID":
                    bid_value = f"{db_connector.get_next_ili2db_sequence_value()}"
                else:
                    bid_value = f"_{uuid.uuid4()}"
                feedback.pushInfo(
                    self.tr(
                        "Generated Basket ID value based on domain: {bid_value}"
                    ).format(bid_value=bid_value)
                )

            feedback.pushInfo(
                self.tr("Create basket for {topic_key}").format(topic_key=topic_key)
            )
            res, msg = db_connector.create_basket(dataset_tid, topic_key, bid_value)
            if not res:
                feedback.pushWarning(
                    self.tr("Basket creation for {topic_key} failed: {msg}").format(
                        topic_key=topic_key, msg=msg
                    )
                )
                return {self.ISVALID: False}
        return {self.ISVALID: True}

    def get_configuration_from_input(self, parameters, context, tool):

        configuration = Ili2DbCommandConfiguration()
        configuration.base_configuration = self.parent.current_baseconfig()
        configuration.tool = tool

        # get database settings form the parent
        if not self.parent.get_db_configuration_from_input(
            parameters, context, configuration
        ):
            return None

        return configuration


class BasketCreatingPGAlgorithm(Ili2pgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data export from a PostgreSQL database.
    """

    def __init__(self):
        super().__init__()

        # initialize the creator with self as parent
        self.creator = ProcessBasketCreator(self)

    def group(self):
        return self.tr("Database")

    def groupId(self):
        return "database"

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "images/database.svg"))

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_pg_basket_creating"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Create baskets (PostGIS)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "basket",
            "dataset",
            "Postgres",
            "PostGIS",
        ]

    def shortDescription(self) -> str:
        """
        Returns the tooltip text when hovering the algorithm
        """
        return self.tr(
            r"""<html><head/><body>
            <p>Creates baskets in a PostgreSQL database according to the ili2db meta information.</p>
            <p>You can choose to create baskets for all topics or only for relevant topics.</p>
            <p>You can also specify a template for the Basket ID, which can include text and the placeholder {t_id} for the current t_id. It overrides all the domain settings.</p>
            <p>This means you cannot use individual templates for different topics, but you can use the same template for all topics.</p>
        </body></html>
        """
        )

    def shortHelpString(self) -> str:
        """
        Returns the help text on the right.
        """
        return self.tr(
            r"""<html><head/><body>
            <p>Creates baskets in a PostgreSQL database according to the ili2db meta information.</p>
            <p>You can choose to create baskets for all topics or only for relevant topics.</p>
            <p>You can also specify a template for the Basket ID, which can include text and the placeholder {t_id} for the current t_id. It overrides all the domain settings.</p>
            <p>This means you cannot use individual templates for different topics, but you can use the same template for all topics.</p>
        </body></html>
        """
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.creator.initParameters()

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        output_map = {}
        configuration = self.creator.get_configuration_from_input(
            parameters, context, DbIliMode.pg
        )
        if not configuration:
            raise QgsProcessingException(
                self.tr("Invalid input parameters. Cannot start basket creation")
            )
        else:
            output_map.update(
                self.creator.run(configuration, parameters, context, feedback)
            )
            output_map.update(self.get_output_from_db_configuration(configuration))
        return output_map


class BasketCreatingGPKGAlgorithm(Ili2gpkgAlgorithm):
    """
    This is an algorithm from Model Baker.
    It is meant for the data export from a GeoPackage database.
    """

    def __init__(self):
        super().__init__()

        # initialize the creator with self as parent
        self.creator = ProcessBasketCreator(self)

    def group(self):
        return self.tr("Database")

    def groupId(self):
        return "database"

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "images/database.svg"))

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm.
        """
        return "modelbaker_gpkg_basket_creating"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Create baskets (GeoPackage)")

    def tags(self) -> list[str]:

        return [
            "modelbaker",
            "interlis",
            "model",
            "baker",
            "basket",
            "dataset",
            "GeoPackage",
            "gpkg",
        ]

    def shortDescription(self) -> str:
        """
        Returns the tooltip text when hovering the algorithm
        """
        return self.tr(
            r"""<html><head/><body>
            <p>Creates baskets in a GeoPackage database according to the ili2db meta information.</p>
            <p>You can choose to create baskets for all topics or only for relevant topics.</p>
            <p>You can also specify a template for the Basket ID, which can include text and the placeholder {t_id} for the current t_id. It overrides all the domain settings.</p>
            <p>This means you cannot use individual templates for different topics, but you can use the same template for all topics.</p>
        </body></html>
        """
        )

    def shortHelpString(self) -> str:
        """
        Returns the help text on the right.
        """
        return self.tr(
            r"""<html><head/><body>
            <p>Creates baskets in a GeoPackage database according to the ili2db meta information.</p>
            <p>You can choose to create baskets for all topics or only for relevant topics.</p>
            <p>You can also specify a template for the Basket ID, which can include text and the placeholder {t_id} for the current t_id. It overrides all the domain settings.</p>
            <p>This means you cannot use individual templates for different topics, but you can use the same template for all topics.</p>
        </body></html>
        """
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.creator.initParameters()

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """
        output_map = {}
        configuration = self.creator.get_configuration_from_input(
            parameters, context, DbIliMode.gpkg
        )
        if not configuration:
            raise QgsProcessingException(
                self.tr("Invalid input parameters. Cannot start basket creation")
            )
        else:
            output_map.update(
                self.creator.run(configuration, parameters, context, feedback)
            )
            output_map.update(self.get_output_from_db_configuration(configuration))
        return output_map
