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
import sys
import tempfile

from qgis.testing import start_app, unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "modelbaker", "libs")
)
import modelbaker.libs.ili2py.interfaces.interlis.interlis_24.ilismeta.ilismeta16_2022_10_10 as ilismeta16
from modelbaker.ili2pytools.pythonizer import BakerPyIndex
from modelbaker.iliwrapper.ili2dbconfig import BaseConfiguration
from modelbaker.utils.ili2db_utils import Ili2DbUtils
from tests.utils import testdata_path

start_app()


class TestPythonizer(unittest.TestCase):
    """
    These tests are to check if the Index and the Library are correctly read by ili2db via the Pythonizer tools.
    As well they should check the available functions of the extensions BakerPyIndex.
    """

    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.base_config = BaseConfiguration()

    def test_pythonizer_index_nupla(self):
        """Tests index generation and queries with Nutzungsplanung_V1_2.

        - Some BASKET OIDs in specific topics
        - Some geometries
        - Some enumerations
        """
        ili_file = testdata_path("ilimodels/Nutzungsplanung_V1_2.ili")
        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)

        model_name = "Nutzungsplanung_V1_2"

        # some base index functions
        # check the topics of Nutzungsplanung_V1_2
        all_topics = index.submodel_in_package
        nupla_topics = all_topics.get(model_name)
        assert set(nupla_topics) == {
            "Nutzungsplanung_V1_2.Catalogue_CH",
            "Nutzungsplanung_V1_2.Geobasisdaten",
            "Nutzungsplanung_V1_2.Rechtsvorschriften",
            "Nutzungsplanung_V1_2.TransferMetadaten",
        }

        # check the index for basket oid definition in topics
        bid_in_topics = index.basket_oid_in_submodel
        # - has some in Catalogue_CH and Geobasisdaten
        bid_definition = bid_in_topics.get("Nutzungsplanung_V1_2.Catalogue_CH")
        assert bid_definition
        assert bid_definition == "Nutzungsplanung_V1_2.Catalogue_CH.BASKET"
        bid_definition = bid_in_topics.get("Nutzungsplanung_V1_2.Geobasisdaten")
        assert bid_definition
        assert bid_definition == "Nutzungsplanung_V1_2.Geobasisdaten.BASKET"
        # - has none in Rechtsvorschriften and TransferMetadaten
        bid_definition = bid_in_topics.get("Nutzungsplanung_V1_2.Rechtsvorschriften")
        assert not bid_definition
        bid_definition = bid_in_topics.get("Nutzungsplanung_V1_2.TransferMetadaten")
        assert not bid_definition

        # some baker py index functions
        # check the relevant topics and classes (means includingt supers and dependencies)
        all_topics = index.relevant_topics()
        assert all_topics == {
            "AdministrativeUnitsCH_V1.CHDistricts",
            "AdministrativeUnitsCH_V1.CHCantons",
            "AdministrativeUnits_V1.CountryNames",
            "Nutzungsplanung_V1_2.Rechtsvorschriften",
            "Nutzungsplanung_V1_2.TransferMetadaten",
            "AdministrativeUnits_V1.Countries",
            "CoordSys.CoordsysTopic",
            "AdministrativeUnitsCH_V1.CHAgencies",
            "Nutzungsplanung_V1_2.Geobasisdaten",
            "AdministrativeUnits_V1.AdministrativeUnits",
            "AdministrativeUnits_V1.Agencies",
            "INTERLIS.TIMESYSTEMS",
            "DictionariesCH_V1.Dictionaries",
            "AdministrativeUnitsCH_V1.CHAdministrativeUnions",
            "Nutzungsplanung_V1_2.Catalogue_CH",
            "Dictionaries_V1.Dictionaries",
            "AdministrativeUnitsCH_V1.CHMunicipalities",
        }
        relevant_topics = index.relevant_topics(model_name)
        assert relevant_topics == {
            "Nutzungsplanung_V1_2.Rechtsvorschriften",
            "Nutzungsplanung_V1_2.TransferMetadaten",
            "Nutzungsplanung_V1_2.Catalogue_CH",
            "Nutzungsplanung_V1_2.Geobasisdaten",
        }

        all_models = index.relevant_models()
        assert all_models == {
            "Units",
            "InternationalCodes_V1",
            "GeometryCHLV03_V1",
            "GeometryCHLV95_V1",
            "Localisation_V1",
            "LocalisationCH_V1",
            "CHAdminCodes_V1",
            "AdministrativeUnitsCH_V1",
            "AdministrativeUnits_V1",
            "CoordSys",
            "DictionariesCH_V1",
            "Dictionaries_V1",
            "INTERLIS",
            "Nutzungsplanung_V1_2",
        }
        relevant_models = index.relevant_models(relevant_topics)
        assert relevant_models == {"Nutzungsplanung_V1_2"}

        all_classes = index.relevant_classes()
        assert all_classes == {
            "INTERLIS.TIMESYSTEMS.CALENDAR",
            "INTERLIS.TIMESYSTEMS.TIMEOFDAYSYS",
            "Dictionaries_V1.Dictionaries.Dictionary",
            "DictionariesCH_V1.Dictionaries.Dictionary",
            "CoordSys.CoordsysTopic.Ellipsoid",
            "CoordSys.CoordsysTopic.GravityModel",
            "CoordSys.CoordsysTopic.GeoidModel",
            "CoordSys.CoordsysTopic.GeoCartesian1D",
            "CoordSys.CoordsysTopic.GeoHeight",
            "CoordSys.CoordsysTopic.GeoCartesian2D",
            "CoordSys.CoordsysTopic.GeoCartesian3D",
            "CoordSys.CoordsysTopic.GeoEllipsoidal",
            "CoordSys.CoordsysTopic.ToGeoEllipsoidal",
            "CoordSys.CoordsysTopic.ToGeoCartesian3D",
            "CoordSys.CoordsysTopic.BidirectGeoCartesian2D",
            "CoordSys.CoordsysTopic.BidirectGeoCartesian3D",
            "CoordSys.CoordsysTopic.BidirectGeoEllipsoidal",
            "CoordSys.CoordsysTopic.TransverseMercator",
            "CoordSys.CoordsysTopic.SwissProjection",
            "CoordSys.CoordsysTopic.Mercator",
            "CoordSys.CoordsysTopic.ObliqueMercator",
            "CoordSys.CoordsysTopic.Lambert",
            "CoordSys.CoordsysTopic.Polyconic",
            "CoordSys.CoordsysTopic.Albus",
            "CoordSys.CoordsysTopic.Azimutal",
            "CoordSys.CoordsysTopic.Stereographic",
            "CoordSys.CoordsysTopic.HeightConversion",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnit",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnion",
            "AdministrativeUnits_V1.AdministrativeUnits.UnionMembers",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnit",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnion",
            "AdministrativeUnits_V1.AdministrativeUnits.UnionMembers",
            "AdministrativeUnits_V1.Countries.Country",
            "Dictionaries_V1.Dictionaries.Dictionary",
            "AdministrativeUnits_V1.CountryNames.CountryNamesTranslation",
            "AdministrativeUnits_V1.Agencies.Organisation",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnit",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnion",
            "AdministrativeUnits_V1.AdministrativeUnits.UnionMembers",
            "AdministrativeUnitsCH_V1.CHCantons.CHCanton",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnit",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnion",
            "AdministrativeUnits_V1.AdministrativeUnits.UnionMembers",
            "AdministrativeUnitsCH_V1.CHDistricts.CHDistrict",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnit",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnion",
            "AdministrativeUnits_V1.AdministrativeUnits.UnionMembers",
            "AdministrativeUnitsCH_V1.CHMunicipalities.CHMunicipality",
            "AdministrativeUnits_V1.AdministrativeUnits.AdministrativeUnit",
            "AdministrativeUnits_V1.AdministrativeUnits.UnionMembers",
            "AdministrativeUnitsCH_V1.CHAdministrativeUnions.AdministrativeUnion",
            "AdministrativeUnits_V1.Agencies.Organisation",
            "AdministrativeUnitsCH_V1.CHAgencies.Agency",
            "Nutzungsplanung_V1_2.Catalogue_CH.Catalogue_CH",
            "Nutzungsplanung_V1_2.Rechtsvorschriften.Dokument",
            "Nutzungsplanung_V1_2.Geobasisdaten.Typ",
            "Nutzungsplanung_V1_2.Geobasisdaten.Typ_Kt",
            "Nutzungsplanung_V1_2.Geobasisdaten.Grundnutzung_Zonenflaeche",
            "Nutzungsplanung_V1_2.Geobasisdaten.Linienbezogene_Festlegung",
            "Nutzungsplanung_V1_2.Geobasisdaten.Objektbezogene_Festlegung",
            "Nutzungsplanung_V1_2.Geobasisdaten.Ueberlagernde_Festlegung",
            "Nutzungsplanung_V1_2.Geobasisdaten.Typ_Dokument",
            "Nutzungsplanung_V1_2.Geobasisdaten.Geometrie_Dokument",
            "Nutzungsplanung_V1_2.TransferMetadaten.Amt",
            "Nutzungsplanung_V1_2.TransferMetadaten.Datenbestand",
        }

        relevant_classes = index.relevant_classes(relevant_topics)
        assert relevant_classes == {
            "Nutzungsplanung_V1_2.Catalogue_CH.Catalogue_CH",
            "Nutzungsplanung_V1_2.Rechtsvorschriften.Dokument",
            "Nutzungsplanung_V1_2.Geobasisdaten.Typ",
            "Nutzungsplanung_V1_2.Geobasisdaten.Typ_Kt",
            "Nutzungsplanung_V1_2.Geobasisdaten.Grundnutzung_Zonenflaeche",
            "Nutzungsplanung_V1_2.Geobasisdaten.Linienbezogene_Festlegung",
            "Nutzungsplanung_V1_2.Geobasisdaten.Objektbezogene_Festlegung",
            "Nutzungsplanung_V1_2.Geobasisdaten.Ueberlagernde_Festlegung",
            "Nutzungsplanung_V1_2.Geobasisdaten.Typ_Dokument",
            "Nutzungsplanung_V1_2.Geobasisdaten.Geometrie_Dokument",
            "Nutzungsplanung_V1_2.TransferMetadaten.Amt",
            "Nutzungsplanung_V1_2.TransferMetadaten.Datenbestand",
        }
        relevant_geometric_attributes = index.relevant_geometric_attributes_per_class(
            list(relevant_topics)
        )
        assert relevant_geometric_attributes[
            "Nutzungsplanung_V1_2.Geobasisdaten.Grundnutzung_Zonenflaeche"
        ] == ["Nutzungsplanung_V1_2.Geobasisdaten.Grundnutzung_Zonenflaeche.Geometrie"]
        assert relevant_geometric_attributes[
            "Nutzungsplanung_V1_2.Geobasisdaten.Ueberlagernde_Festlegung"
        ] == ["Nutzungsplanung_V1_2.Geobasisdaten.Ueberlagernde_Festlegung.Geometrie"]

        # check if it returns a library object (if not none)
        library = index.library_object()
        assert library

        # check some attribute types
        assert isinstance(
            index.attribute_type(
                "Nutzungsplanung_V1_2.Geobasisdaten.Typ.Nutzungsziffer"
            ),
            ilismeta16.NumType,
        )
        assert isinstance(
            index.attribute_type(
                "Nutzungsplanung_V1_2.Rechtsvorschriften.Dokument.Rechtsstatus"
            ),
            ilismeta16.EnumType,
        )
        assert isinstance(
            index.attribute_type(
                "Nutzungsplanung_V1_2.Rechtsvorschriften.Dokument.TextImWeb"
            ),
            ilismeta16.MultiValue,
        )

        # and enumerations
        enumeration_object = index.enumeration_object(
            index.attribute_type(
                "Nutzungsplanung_V1_2.Rechtsvorschriften.Dokument.Rechtsstatus"
            )
        )
        assert set(enumeration_object.values) == {
            "inKraft",
            "AenderungMitVorwirkung",
            "AenderungOhneVorwirkung",
        }

    def test_pythonizer_index_kbs(self):
        """Tests index generation and queries with KbS_V1_5.

        - No BASKET OIDs
        - Some geometries
        - Some enumerations
        """

        ili_file = testdata_path("ilimodels/KbS_V1_5.ili")
        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)

        model_name = "KbS_V1_5"
        # some base index functions
        # check the topics of KbS_V1_5
        all_topics = index.submodel_in_package
        kbs_topics = all_topics.get(model_name)
        assert set(kbs_topics) == {
            "KbS_V1_5.Codelisten",
            "KbS_V1_5.Belastete_Standorte",
        }

        # check the index for basket oid definition in topics
        bid_in_topics = index.basket_oid_in_submodel
        # - has none in Codelisten and Belastete_Standorte
        bid_definition = bid_in_topics.get("KbS_V1_5.Codelisten")
        assert not bid_definition
        bid_definition = bid_in_topics.get("KbS_V1_5.Belastete_Standorte")
        assert not bid_definition

        # some baker py index convenience functions
        # check the relevant topics and classes (means includingt supers and dependencies)
        all_topics = index.relevant_topics()
        assert all_topics == {
            "Dictionaries_V1.Dictionaries",
            "DictionariesCH_V1.Dictionaries",
            "INTERLIS.TIMESYSTEMS",
            "KbS_V1_5.Belastete_Standorte",
            "KbS_V1_5.Codelisten",
            "CoordSys.CoordsysTopic",
        }
        relevant_topics = index.relevant_topics(model_name)
        assert relevant_topics == {
            "KbS_V1_5.Codelisten",
            "KbS_V1_5.Belastete_Standorte",
        }

        all_models = index.relevant_models()
        assert all_models == {
            "Units",
            "InternationalCodes_V1",
            "GeometryCHLV03_V1",
            "GeometryCHLV95_V1",
            "LocalisationCH_V1",
            "Localisation_V1",
            "CoordSys",
            "DictionariesCH_V1",
            "Dictionaries_V1",
            "INTERLIS",
            "KbS_V1_5",
        }
        relevant_models = index.relevant_models(relevant_topics)
        assert relevant_models == {"KbS_V1_5"}

        all_classes = index.relevant_classes()
        assert all_classes == {
            "INTERLIS.TIMESYSTEMS.CALENDAR",
            "INTERLIS.TIMESYSTEMS.TIMEOFDAYSYS",
            "Dictionaries_V1.Dictionaries.Dictionary",
            "DictionariesCH_V1.Dictionaries.Dictionary",
            "CoordSys.CoordsysTopic.Ellipsoid",
            "CoordSys.CoordsysTopic.GravityModel",
            "CoordSys.CoordsysTopic.GeoidModel",
            "CoordSys.CoordsysTopic.GeoCartesian1D",
            "CoordSys.CoordsysTopic.GeoHeight",
            "CoordSys.CoordsysTopic.GeoCartesian2D",
            "CoordSys.CoordsysTopic.GeoCartesian3D",
            "CoordSys.CoordsysTopic.GeoEllipsoidal",
            "CoordSys.CoordsysTopic.ToGeoEllipsoidal",
            "CoordSys.CoordsysTopic.ToGeoCartesian3D",
            "CoordSys.CoordsysTopic.BidirectGeoCartesian2D",
            "CoordSys.CoordsysTopic.BidirectGeoCartesian3D",
            "CoordSys.CoordsysTopic.BidirectGeoEllipsoidal",
            "CoordSys.CoordsysTopic.TransverseMercator",
            "CoordSys.CoordsysTopic.SwissProjection",
            "CoordSys.CoordsysTopic.Mercator",
            "CoordSys.CoordsysTopic.ObliqueMercator",
            "CoordSys.CoordsysTopic.Lambert",
            "CoordSys.CoordsysTopic.Polyconic",
            "CoordSys.CoordsysTopic.Albus",
            "CoordSys.CoordsysTopic.Azimutal",
            "CoordSys.CoordsysTopic.Stereographic",
            "CoordSys.CoordsysTopic.HeightConversion",
            "KbS_V1_5.Codelisten.Deponietyp_Definition",
            "KbS_V1_5.Codelisten.Standorttyp_Definition",
            "KbS_V1_5.Codelisten.StatusAltlV_Definition",
            "KbS_V1_5.Codelisten.Untersuchungsmassnahmen_Definition",
            "KbS_V1_5.Belastete_Standorte.ZustaendigkeitKataster",
            "KbS_V1_5.Belastete_Standorte.Belasteter_Standort",
        }
        relevant_classes = index.relevant_classes(relevant_topics)
        assert relevant_classes == {
            "KbS_V1_5.Codelisten.Deponietyp_Definition",
            "KbS_V1_5.Codelisten.Standorttyp_Definition",
            "KbS_V1_5.Codelisten.StatusAltlV_Definition",
            "KbS_V1_5.Codelisten.Untersuchungsmassnahmen_Definition",
            "KbS_V1_5.Belastete_Standorte.ZustaendigkeitKataster",
            "KbS_V1_5.Belastete_Standorte.Belasteter_Standort",
        }
        relevant_geometric_attributes = index.relevant_geometric_attributes_per_class(
            relevant_topics
        )
        assert relevant_geometric_attributes[
            "KbS_V1_5.Belastete_Standorte.Belasteter_Standort"
        ] == [
            "KbS_V1_5.Belastete_Standorte.Belasteter_Standort.Geo_Lage_Polygon",
            "KbS_V1_5.Belastete_Standorte.Belasteter_Standort.Geo_Lage_Punkt",
        ]

        # check some attribute types
        assert isinstance(
            index.attribute_type(
                "KbS_V1_5.Belastete_Standorte.Belasteter_Standort.InBetrieb"
            ),
            ilismeta16.BooleanType,
        )
        assert isinstance(
            index.attribute_type(
                "KbS_V1_5.Belastete_Standorte.Belasteter_Standort.Katasternummer"
            ),
            ilismeta16.TextType,
        )
        assert isinstance(
            index.attribute_type(
                "KbS_V1_5.Belastete_Standorte.Belasteter_Standort.Standorttyp"
            ),
            ilismeta16.EnumType,
        )

        # check if it returns a library object (if not none)
        library = index.library_object()
        assert library

        # and enumerations
        enumeration_object = index.enumeration_object(
            index.attribute_type(
                "KbS_V1_5.Belastete_Standorte.Belasteter_Standort.Standorttyp"
            )
        )
        assert set(enumeration_object.values) == {
            "StaoTyp1",
            "StaoTyp2",
            "StaoTyp3",
            "StaoTyp4",
        }

    def test_pythonizer_index_color_enums(self):
        """Tests index generation and queries with Colors_V2.

        - No BASKET OIDs
        - Some geometries
        - Some enumerations
        """

        ili_file = testdata_path("ilimodels/ColorsParentChildDomain_V2.ili")
        _, imd_file, _ = Ili2DbUtils().compile(ili_file)
        index = BakerPyIndex.from_imd(imd_file)

        model_name = "Colors_V2"
        # some base index functions
        # check the topics of Colors_V2
        all_topics = index.submodel_in_package
        colors_topics = all_topics.get(model_name)
        assert set(colors_topics) == {"Colors_V2.SomeColors"}

        # check the index for basket oid definition in topics
        bid_in_topics = index.basket_oid_in_submodel
        # - has none in Colors_V2
        bid_definition = bid_in_topics.get("Colors_V2.SomeColors")
        assert not bid_definition

        # some baker py index convenience functions
        # check the relevant topics and classes (means includingt supers and dependencies)
        all_topics = index.relevant_topics()
        assert all_topics == {"INTERLIS.TIMESYSTEMS", "Colors_V2.SomeColors"}
        relevant_topics = index.relevant_topics(model_name)
        assert relevant_topics == {
            "Colors_V2.SomeColors",
        }

        all_models = index.relevant_models()
        assert all_models == {
            "INTERLIS",
            "Colors_V2",
        }
        relevant_models = index.relevant_models(relevant_topics)
        assert relevant_models == {"Colors_V2"}

        all_classes = index.relevant_classes()
        assert all_classes == {
            "INTERLIS.TIMESYSTEMS.CALENDAR",
            "INTERLIS.TIMESYSTEMS.TIMEOFDAYSYS",
            "Colors_V2.SomeColors.BaseColorClass",
            "Colors_V2.SomeColors.BlueChildColorClass",
            "Colors_V2.SomeColors.UninheritedCMYColorClass",
            "Colors_V2.SomeColors.GreenChildColorClass",
        }
        relevant_classes = index.relevant_classes(relevant_topics)
        assert relevant_classes == {
            "Colors_V2.SomeColors.BaseColorClass",
            "Colors_V2.SomeColors.BlueChildColorClass",
            "Colors_V2.SomeColors.UninheritedCMYColorClass",
            "Colors_V2.SomeColors.GreenChildColorClass",
        }
        relevant_geometric_attributes = index.relevant_geometric_attributes_per_class(
            relevant_topics
        )
        assert relevant_geometric_attributes == {}

        # check some attribute types - all enums - this is the interresting part of this test case.
        base_type = index.attribute_type("Colors_V2.SomeColors.BaseColorClass.Colors")
        assert isinstance(
            base_type,
            ilismeta16.EnumType,
        )
        assert base_type.name == "Colors"
        assert base_type.tid == "Colors_V2.Colors"

        blue_type = index.attribute_type(
            "Colors_V2.SomeColors.BlueChildColorClass.Colors"
        )
        assert isinstance(
            blue_type,
            ilismeta16.EnumType,
        )
        assert blue_type.name == "BlueChildColors"
        assert blue_type.tid == "Colors_V2.BlueChildColors"

        green_type = index.attribute_type(
            "Colors_V2.SomeColors.GreenChildColorClass.Colors"
        )
        assert isinstance(
            green_type,
            ilismeta16.EnumType,
        )
        assert green_type.name == "GreenChildColors"
        assert green_type.tid == "Colors_V2.GreenChildColors"

        # check if it returns a library object (if not none)
        library = index.library_object()
        assert library

        # and enumerations
        base_enumeration_object = index.enumeration_object(
            index.attribute_type("Colors_V2.SomeColors.BaseColorClass.Colors")
        )
        assert set(base_enumeration_object.values) == {"Green", "Red", "Blue"}

        blue_enumeration_object = index.enumeration_object(
            index.attribute_type("Colors_V2.SomeColors.BlueChildColorClass.Colors")
        )
        assert set(blue_enumeration_object.values) == {
            "Blue.Dark_Blue",
            "Blue.Light_Blue",
            "Blue.Medium_Blue",
        }

        green_enumeration_object = index.enumeration_object(
            index.attribute_type("Colors_V2.SomeColors.GreenChildColorClass.Colors")
        )
        assert set(green_enumeration_object.values) == {
            "Green.Dark_Green",
            "Green.Light_Green",
            "Green.Medium_Green",
        }
