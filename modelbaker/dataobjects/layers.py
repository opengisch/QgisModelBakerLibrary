"""
/***************************************************************************
                              -------------------
        begin                : 2016-11-14
        git sha              : :%H$
        copyright            : (C) 2016 by OPENGIS.ch
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
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Union

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsDataSourceUri,
    QgsExpressionContextUtils,
    QgsLayerDefinition,
    QgsRasterLayer,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication, QSettings

if TYPE_CHECKING:
    from .fields import Field
    from .project import Project

from ..generator.config import BASKET_FIELDNAMES, IGNORED_FIELDNAMES
from ..utils.globals import OptimizeStrategy
from .form import Form, FormFieldWidget, FormRelationWidget, FormTab


class Layer:
    def __init__(
        self,
        provider: str = None,
        uri: str = None,
        name: str = None,
        srid: Optional[int] = None,
        extent: Optional[str] = None,
        geometry_column: str = None,
        wkb_type: QgsWkbTypes = QgsWkbTypes.Type.Unknown,
        alias: Optional[str] = None,
        is_domain: bool = False,  # is enumeration or catalogue
        is_structure: bool = False,
        is_nmrel: bool = False,
        display_expression: str = None,
        coordinate_precision: Optional[float] = None,
        is_basket_table: bool = False,
        is_dataset_table: bool = False,
        ili_name: Optional[str] = None,
        is_relevant: bool = True,
        all_topics: list[
            str
        ] = [],  # all the topics this class (or an instance of it) are located
        relevant_topics: list[
            str
        ] = [],  # the topics of the most extended instance of it only
        definitionfile: Optional[str] = None,
        qmlstylefile: Optional[str] = None,
        styles: dict[str, dict[str, str]] = {},
        is_enum: bool = False,
        base_class: str = None,
        provider_names_map: dict[
            str, str
        ] = {},  # provider specific column names (e.g. T_Id vs t_id)
    ) -> None:
        self.provider = provider
        self.uri = uri
        self.name = name
        if extent is not None:
            extent_coords = extent.split(";")
            extent = QgsRectangle(
                float(extent_coords[0]),
                float(extent_coords[1]),
                float(extent_coords[2]),
                float(extent_coords[3]),
            )
        self.extent = extent
        self.geometry_column = geometry_column
        self.wkb_type = wkb_type
        self.alias = alias
        self.__layer = None
        self.fields = list()
        self.is_domain = is_domain
        self.is_structure = is_structure
        self.is_enum = is_enum
        self.base_class = base_class
        self.provider_names_map = provider_names_map

        self.is_nmrel = is_nmrel
        self.srid = srid
        """ If is_nmrel is set to true it is a junction table in a N:M relation.
        Or in ili2db terms, the table is marked as ASSOCIATION in t_ili2db_table_prop.settings. """

        self.display_expression = display_expression

        self.coordinate_precision = coordinate_precision

        self.is_basket_table = is_basket_table
        self.is_dataset_table = is_dataset_table

        self.ili_name = ili_name

        self.is_relevant = is_relevant
        self.all_topics = all_topics
        self.relevant_topics = relevant_topics

        self.definitionfile = definitionfile
        self.qmlstylefile = qmlstylefile
        self.styles = styles

        self.__form = Form()

        # legend settings
        self.expanded = True
        self.checked = True
        self.featurecount = False

    def dump(self) -> dict:
        definition = dict()
        definition["provider"] = self.provider
        definition["uri"] = self.uri
        definition["isdomain"] = self.is_domain
        definition["isstructure"] = self.is_structure
        definition["isenum"] = self.is_enum
        definition["isnmrel"] = self.is_nmrel
        definition["isbaskettable"] = self.is_basket_table
        definition["isdatasettable"] = self.is_dataset_table
        definition["displayexpression"] = self.display_expression
        definition["coordinateprecision"] = self.coordinate_precision
        definition["ili_name"] = self.ili_name
        definition["is_relevant"] = self.is_relevant
        definition["all_topics"] = self.all_topics
        definition["relevant_topics"] = self.relevant_topics
        definition["definitionfile"] = self.definitionfile
        definition["qmlstylefile"] = self.qmlstylefile
        definition["styles"] = self.styles
        definition["form"] = self.__form.dump()
        definition["base_class"] = self.base_class
        return definition

    def load(self, definition: dict) -> None:
        self.provider = definition["provider"]
        self.uri = definition["uri"]
        self.is_domain = definition["isdomain"]
        self.is_structure = definition["isstructure"]
        self.is_enum = definition["isenum"]
        self.is_nmrel = definition["isnmrel"]
        self.is_basket_table = definition["isbaskettable"]
        self.is_dataset_table = definition["isdatasettable"]
        self.display_expression = definition["displayexpression"]
        self.coordinate_precision = definition["coordinateprecision"]
        self.ili_name = definition["ili_name"]
        self.is_relevant = definition["is_relevant"]
        self.all_topics = definition["all_topics"]
        self.relevant_topics = definition["relevant_topics"]
        self.definitionfile = definition["definitionfile"]
        self.qmlstylefile = definition["qmlstylefile"]
        self.styles = definition["styles"]
        self.__form.load(definition["form"])
        self.base_class = definition["base_class"]

    def create(self) -> Union[QgsRasterLayer, QgsVectorLayer]:
        if self.definitionfile:
            if self.__layer is None:
                layers = QgsLayerDefinition.loadLayerDefinitionLayers(
                    self.definitionfile
                )
                if layers:
                    self.__layer = layers[0]
            return self.__layer

        if self.__layer is None:
            layer_name = self.alias or self.name

            settings = QSettings()
            # Take the "CRS for new layers" config, overwrite it while loading layers and...
            old_proj_value = settings.value(
                "/Projections/defaultBehaviour", "prompt", type=str
            )
            settings.setValue("/Projections/defaultBehaviour", "useProject")
            self.__layer = self._create_layer(self.uri, layer_name, self.provider)
            settings.setValue("/Projections/defaultBehavior", old_proj_value)

            if (
                self.srid is not None
                and not self.__layer.crs().authid() == "EPSG:{}".format(self.srid)
            ):
                crs = QgsCoordinateReferenceSystem().fromEpsgId(self.srid)
                if not crs.isValid():
                    crs = QgsCoordinateReferenceSystem(self.srid)  # Fallback
                self.__layer.setCrs(crs)
            if self.is_domain or self.is_dataset_table:
                self.__layer.setReadOnly()
            if self.display_expression:
                self.__layer.setDisplayExpression(self.display_expression)
            if self.coordinate_precision and self.coordinate_precision < 1:
                self.__layer.geometryOptions().setGeometryPrecision(
                    self.coordinate_precision
                )
                self.__layer.geometryOptions().setRemoveDuplicateNodes(True)

        for field in self.fields:
            field.create(self)

        return self.__layer

    def create_form(self, project: Project) -> None:
        edit_form = self.__form.create(self, self.__layer, project)
        self.__layer.setEditFormConfig(edit_form)

    def load_styles(self) -> None:
        if self.qmlstylefile:
            self.__layer.loadNamedStyle(self.qmlstylefile)
        if self.styles:
            for style_name in self.styles.keys():
                # add the new style (because otherwise we overwrite the previous one)
                self.__layer.styleManager().addStyleFromLayer(style_name)
                self.__layer.styleManager().setCurrentStyle(style_name)
                style_properties = self.styles[style_name]
                style_qmlstylefile = style_properties.get("qmlstylefile")
                if style_qmlstylefile:
                    self.__layer.loadNamedStyle(style_qmlstylefile)
            # set the default style
            self.__layer.styleManager().setCurrentStyle("default")

    def store_variables(self, project: Project) -> None:
        """
        Set the layer variables according to the strategy
        """
        interlis_topics = ",".join(
            sorted(self.all_topics)
            if project.optimize_strategy == OptimizeStrategy.NONE
            else sorted(self.relevant_topics)
        )
        QgsExpressionContextUtils.setLayerVariable(
            self.__layer, "interlis_topic", interlis_topics
        )

        QgsExpressionContextUtils.setLayerVariable(
            self.__layer, "oid_domain", self.oid_domain
        )

    def _create_layer(
        self, uri: str, layer_name: str, provider: str
    ) -> Union[QgsRasterLayer, QgsVectorLayer]:
        if provider and provider.lower() == "wms":
            return QgsRasterLayer(uri, layer_name, provider)
        # return QgsVectorLayer even when it's an invalid layer with no provider
        return QgsVectorLayer(uri, layer_name, provider)

    def post_generate(self, project: Project) -> None:
        """
        Will be called when the whole project has been generated and
        therefore all relations are available and the form
        can also be generated.
        """
        has_tabs = False
        for relation in project.relations:
            if relation.referenced_layer == self:
                has_tabs = True
                break

        if has_tabs:
            num_fields = len([f for f in self.fields if not f.hidden])
            if num_fields > 5:
                num_tabs = 2
            else:
                num_tabs = 1
            tab = FormTab(QCoreApplication.translate("FormTab", "General"), num_tabs)
            for field in self.fields:
                if not field.hidden:
                    widget = FormFieldWidget(field.alias, field.name)
                    tab.addChild(widget)

            self.__form.add_element(tab)

            relations_to_add = []
            for relation in project.relations:
                if relation.referenced_layer == self:
                    if (
                        not relation.referencing_layer.is_relevant
                        and project.optimize_strategy == OptimizeStrategy.GROUP
                    ):
                        continue

                    # 1:n relation will be added only if does not point to a pure link table
                    if (
                        not relation.referencing_layer.isPureLinkTable(project)
                        or Qgis.QGIS_VERSION_INT < 31600
                    ):
                        relations_to_add.append((relation, None))

                    else:
                        for nm_relation in project.relations:
                            if nm_relation == relation:
                                continue

                            if nm_relation.referenced_layer.ili_name == self.ili_name:
                                continue

                            if (
                                not nm_relation.referenced_layer.is_relevant
                                and project.optimize_strategy == OptimizeStrategy.GROUP
                            ):
                                continue

                            if nm_relation.referenced_layer.is_basket_table:
                                continue

                            if (
                                nm_relation.referencing_layer
                                == relation.referencing_layer
                            ):
                                relations_to_add.append((relation, nm_relation))

            for relation, nm_relation in relations_to_add:
                if nm_relation and Qgis.QGIS_VERSION_INT < 31600:
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        'QGIS version older than 3.16. Relation editor widget for relation "{}" will not be added.'.format(
                            nm_relation.name
                        )
                    )
                    continue

                if nm_relation:
                    tab = FormTab(nm_relation.referenced_layer.alias)
                else:
                    tab = FormTab(relation.referencing_layer.alias)

                widget = FormRelationWidget(relation, nm_relation)
                tab.addChild(widget)
                self.__form.add_element(tab)

        else:
            for field in self.fields:
                if not field.hidden:
                    widget = FormFieldWidget(field.alias, field.name)
                    self.__form.add_element(widget)

    def source(self) -> QgsDataSourceUri:
        return QgsDataSourceUri(self.uri)

    @property
    def layer(self) -> Union[QgsRasterLayer, QgsVectorLayer]:
        return self.__layer

    @property
    def real_id(self) -> Optional[str]:
        """
        The layer id. Only valid after creating the layer.
        """
        if self.__layer:
            return self.__layer.id()
        else:
            return None

    @property
    def oid_domain(self) -> Optional[str]:
        t_ili_tid_field = self.t_ili_tid_field
        if t_ili_tid_field:
            return t_ili_tid_field.oid_domain
        return None

    @property
    def t_ili_tid_field(self) -> Optional[Field]:
        for field in self.fields:
            if field.name.lower() == "t_ili_tid":
                return field
        return None

    def isPureLinkTable(self, project: Project) -> bool:
        """
        Returns True if the layer is a pure link table in a n:m relation.
        With "pure" it is meant the layer has no more fields than foreign keys and its id.
        """

        remaining_fields = set()
        for field in self.fields:
            if field.name not in IGNORED_FIELDNAMES + BASKET_FIELDNAMES:
                remaining_fields.add(field.name)

        # Remove all fields that are referencing fields
        for relation in project.relations:
            if relation.referencing_layer != self:
                continue
            remaining_fields.discard(relation.referencing_field)

        return len(remaining_fields) == 0
