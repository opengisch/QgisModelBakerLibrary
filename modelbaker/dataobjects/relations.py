from __future__ import annotations

from qgis.core import QgsProject, QgsRelation


class Relation:
    def __init__(self) -> None:
        self.referencing_layer = None
        self.referenced_layer = None
        self.referencing_field = None
        self.referenced_field = None
        self.name = None
        self.strength = QgsRelation.RelationStrength.Association
        self.cardinality_max = None
        self.cardinality_min = None
        self.child_domain_name = None
        self.qgis_relation = None
        self._id = None
        self.translate_name = False

    def dump(self) -> dict:
        definition = dict()
        definition["referencingLayer"] = self.referencing_layer
        definition["referencingField"] = self.referencing_field
        definition["referencedLayer"] = self.referenced_layer
        definition["referencedField"] = self.referenced_field
        definition["strength"] = self.strength
        definition["cardinality_max"] = self.cardinality_max
        definition["cardinality_min"] = self.cardinality_min
        definition["child_domain_name"] = self.child_domain_name

        return definition

    def load(self, definition: str) -> None:
        self.referencing_layer = definition["referencingLayer"]
        self.referencing_field = definition["referencingField"]
        self.referenced_layer = definition["referencedLayer"]
        self.referenced_field = definition["referencedField"]
        self.strength = definition["strength"]
        self.cardinality_max = definition["cardinality_max"]
        self.cardinality_min = definition["cardinality_min"]
        self.child_domain_name = definition["child_domain_name"]

    def create(
        self, qgis_project: QgsProject, relations: list[QgsRelation]
    ) -> QgsRelation:
        relation = QgsRelation()
        project_ids = qgis_project.relationManager().relations().keys()
        base_id = self.name

        suffix = 1
        self._id = base_id

        while self._id in project_ids:
            self._id = "{}_{}".format(base_id, suffix)
            suffix += 1

        while self._id in [rel.id() for rel in relations]:
            self._id = "{}_{}".format(base_id, suffix)
            suffix += 1

        relation.setId(self._id)
        relation.setName(self.name)
        referencing_qgis_layer = self.referencing_layer.create()
        referenced_qgis_layer = self.referenced_layer.create()
        relation.setReferencingLayer(referencing_qgis_layer.id())
        relation.setReferencedLayer(referenced_qgis_layer.id())
        relation.addFieldPair(self.referencing_field, self.referenced_field)
        relation.setStrength(self.strength)

        if self.translate_name:
            # Grab translated table and field names from QGIS objects
            index = referencing_qgis_layer.fields().indexOf(self.referencing_field)
            referencing_field_alias = referencing_qgis_layer.fields().at(index).alias()
            index = referenced_qgis_layer.fields().indexOf(self.referenced_field)
            referenced_field_alias = referenced_qgis_layer.fields().at(index).alias()
            tr_name = "{}_({})_{}_({})".format(
                referencing_qgis_layer.name(),
                referencing_field_alias
                if referencing_field_alias
                else self.referencing_field,
                referenced_qgis_layer.name(),
                referenced_field_alias
                if referenced_field_alias
                else self.referenced_field,
            )
            relation.setName(tr_name)

        self.qgis_relation = relation
        return relation

    @property
    def id(self) -> str:
        return self._id
