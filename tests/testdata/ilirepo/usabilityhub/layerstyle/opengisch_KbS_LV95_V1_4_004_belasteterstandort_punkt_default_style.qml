<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis readOnly="0" version="3.22.11-Białowieża" styleCategories="LayerConfiguration|Forms">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <fieldConfiguration>
    <field name="t_id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="t_basket">
      <editWidget type="RelationReference">
        <config>
          <Option type="Map">
            <Option value="false" name="AllowAddFeatures" type="bool"/>
            <Option value="true" name="AllowNULL" type="bool"/>
            <Option value="&quot;topic&quot; = 'KbS_LV95_V1_4.Belastete_Standorte' and attribute(get_feature('t_ili2db_dataset', 't_id', &quot;dataset&quot;), 'datasetname') != 'Catalogueset'" name="FilterExpression" type="QString"/>
            <Option name="FilterFields"/>
            <Option value="true" name="OrderByValue" type="bool"/>
            <Option value="belasteter_standort_t_basket_fkey_1" name="Relation" type="QString"/>
            <Option value="false" name="ShowForm" type="bool"/>
            <Option value="false" name="ShowOpenFormButton" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="t_ili_tid">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="katasternummer">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="url_standort">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geo_lage_polygon">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="standorttyp">
      <editWidget type="RelationReference">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="inbetrieb">
      <editWidget type="CheckBox">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="nachsorge">
      <editWidget type="CheckBox">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="statusaltlv">
      <editWidget type="RelationReference">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ersteintrag">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option value="true" name="calendar_popup" type="bool"/>
            <Option value="M/d/yy" name="display_format" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="letzteanpassung">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option value="true" name="calendar_popup" type="bool"/>
            <Option value="M/d/yy" name="display_format" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="url_kbs_auszug">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_de">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_fr">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_rm">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_it">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_en">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="zustaendigkeitkataster">
      <editWidget type="RelationReference">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>tablayout</editorlayout>
  <attributeEditorForm>
    <attributeEditorContainer showLabel="1" visibilityExpressionEnabled="0" visibilityExpression="" name="Allgemein" columnCount="2" groupBox="0">
      <attributeEditorField showLabel="1" name="bemerkung" index="13"/>
      <attributeEditorField showLabel="1" name="bemerkung_de" index="14"/>
      <attributeEditorField showLabel="1" name="bemerkung_en" index="18"/>
      <attributeEditorField showLabel="1" name="bemerkung_fr" index="15"/>
      <attributeEditorField showLabel="1" name="bemerkung_it" index="17"/>
      <attributeEditorField showLabel="1" name="bemerkung_rm" index="16"/>
      <attributeEditorField showLabel="1" name="ersteintrag" index="10"/>
      <attributeEditorField showLabel="1" name="geo_lage_polygon" index="5"/>
      <attributeEditorField showLabel="1" name="geo_lage_punkt" index="-1"/>
      <attributeEditorField showLabel="1" name="inbetrieb" index="7"/>
      <attributeEditorField showLabel="1" name="katasternummer" index="3"/>
      <attributeEditorField showLabel="1" name="letzteanpassung" index="11"/>
      <attributeEditorField showLabel="1" name="nachsorge" index="8"/>
      <attributeEditorField showLabel="1" name="standorttyp" index="6"/>
      <attributeEditorField showLabel="1" name="statusaltlv" index="9"/>
      <attributeEditorField showLabel="1" name="url_kbs_auszug" index="12"/>
      <attributeEditorField showLabel="1" name="url_standort" index="4"/>
      <attributeEditorField showLabel="1" name="zustaendigkeitkataster" index="19"/>
    </attributeEditorContainer>
    <attributeEditorContainer showLabel="1" visibilityExpressionEnabled="0" visibilityExpression="" name="Parzellenidentifikation" columnCount="1" groupBox="0">
      <attributeEditorRelation showLabel="1" name="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey_1" relationWidgetTypeId="" label="" forceSuppressFormPopup="0" relation="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey_1" nmRelationId="">
        <editor_configuration type="Map">
          <Option value="AllButtons" name="buttons" type="QString"/>
        </editor_configuration>
      </attributeEditorRelation>
    </attributeEditorContainer>
    <attributeEditorContainer showLabel="1" visibilityExpressionEnabled="0" visibilityExpression="" name="Deponie" columnCount="1" groupBox="0">
      <attributeEditorRelation showLabel="1" name="deponietyp__belasteter_standort_dpntyp_fkey_1" relationWidgetTypeId="" label="" forceSuppressFormPopup="0" relation="deponietyp__belasteter_standort_dpntyp_fkey_1" nmRelationId="">
        <editor_configuration type="Map">
          <Option value="AllButtons" name="buttons" type="QString"/>
        </editor_configuration>
      </attributeEditorRelation>
    </attributeEditorContainer>
    <attributeEditorContainer showLabel="1" visibilityExpressionEnabled="0" visibilityExpression="" name="Egrid" columnCount="1" groupBox="0">
      <attributeEditorRelation showLabel="1" name="egrid__belasteter_standort_egrid_fkey_1" relationWidgetTypeId="" label="" forceSuppressFormPopup="0" relation="egrid__belasteter_standort_egrid_fkey_1" nmRelationId="">
        <editor_configuration type="Map">
          <Option value="AllButtons" name="buttons" type="QString"/>
        </editor_configuration>
      </attributeEditorRelation>
    </attributeEditorContainer>
    <attributeEditorContainer showLabel="1" visibilityExpressionEnabled="0" visibilityExpression="" name="Untersuchungsmassnahmen" columnCount="1" groupBox="0">
      <attributeEditorRelation showLabel="1" name="untersmassn__belsttr_stndrchngsmssnhmen_fkey_1" relationWidgetTypeId="" label="" forceSuppressFormPopup="0" relation="untersmassn__belsttr_stndrchngsmssnhmen_fkey_1" nmRelationId="">
        <editor_configuration type="Map">
          <Option value="AllButtons" name="buttons" type="QString"/>
        </editor_configuration>
      </attributeEditorRelation>
    </attributeEditorContainer>
  </attributeEditorForm>
  <editable>
    <field editable="1" name="bemerkung"/>
    <field editable="1" name="bemerkung_de"/>
    <field editable="1" name="bemerkung_en"/>
    <field editable="1" name="bemerkung_fr"/>
    <field editable="1" name="bemerkung_it"/>
    <field editable="1" name="bemerkung_rm"/>
    <field editable="1" name="ersteintrag"/>
    <field editable="1" name="geo_lage_polygon"/>
    <field editable="1" name="inbetrieb"/>
    <field editable="1" name="katasternummer"/>
    <field editable="1" name="letzteanpassung"/>
    <field editable="1" name="nachsorge"/>
    <field editable="1" name="standorttyp"/>
    <field editable="1" name="statusaltlv"/>
    <field editable="1" name="t_basket"/>
    <field editable="1" name="t_id"/>
    <field editable="1" name="t_ili_tid"/>
    <field editable="1" name="url_kbs_auszug"/>
    <field editable="1" name="url_standort"/>
    <field editable="1" name="zustaendigkeitkataster"/>
  </editable>
  <labelOnTop>
    <field name="bemerkung" labelOnTop="0"/>
    <field name="bemerkung_de" labelOnTop="0"/>
    <field name="bemerkung_en" labelOnTop="0"/>
    <field name="bemerkung_fr" labelOnTop="0"/>
    <field name="bemerkung_it" labelOnTop="0"/>
    <field name="bemerkung_rm" labelOnTop="0"/>
    <field name="ersteintrag" labelOnTop="0"/>
    <field name="geo_lage_polygon" labelOnTop="0"/>
    <field name="inbetrieb" labelOnTop="0"/>
    <field name="katasternummer" labelOnTop="0"/>
    <field name="letzteanpassung" labelOnTop="0"/>
    <field name="nachsorge" labelOnTop="0"/>
    <field name="standorttyp" labelOnTop="0"/>
    <field name="statusaltlv" labelOnTop="0"/>
    <field name="t_basket" labelOnTop="0"/>
    <field name="t_id" labelOnTop="0"/>
    <field name="t_ili_tid" labelOnTop="0"/>
    <field name="url_kbs_auszug" labelOnTop="0"/>
    <field name="url_standort" labelOnTop="0"/>
    <field name="zustaendigkeitkataster" labelOnTop="0"/>
  </labelOnTop>
  <reuseLastValue>
    <field name="bemerkung" reuseLastValue="0"/>
    <field name="bemerkung_de" reuseLastValue="0"/>
    <field name="bemerkung_en" reuseLastValue="0"/>
    <field name="bemerkung_fr" reuseLastValue="0"/>
    <field name="bemerkung_it" reuseLastValue="0"/>
    <field name="bemerkung_rm" reuseLastValue="0"/>
    <field name="ersteintrag" reuseLastValue="0"/>
    <field name="geo_lage_polygon" reuseLastValue="0"/>
    <field name="inbetrieb" reuseLastValue="0"/>
    <field name="katasternummer" reuseLastValue="0"/>
    <field name="letzteanpassung" reuseLastValue="0"/>
    <field name="nachsorge" reuseLastValue="0"/>
    <field name="standorttyp" reuseLastValue="0"/>
    <field name="statusaltlv" reuseLastValue="0"/>
    <field name="t_basket" reuseLastValue="0"/>
    <field name="t_id" reuseLastValue="0"/>
    <field name="t_ili_tid" reuseLastValue="0"/>
    <field name="url_kbs_auszug" reuseLastValue="0"/>
    <field name="url_standort" reuseLastValue="0"/>
    <field name="zustaendigkeitkataster" reuseLastValue="0"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>'Default: '||standorttyp ||' - '||katasternummer</previewExpression>
  <layerGeometryType>0</layerGeometryType>
</qgis>
