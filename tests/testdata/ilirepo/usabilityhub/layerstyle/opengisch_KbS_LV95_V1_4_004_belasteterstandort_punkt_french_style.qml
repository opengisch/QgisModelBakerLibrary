<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.11-Białowieża" readOnly="0" styleCategories="LayerConfiguration|Fields|Forms">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <fieldConfiguration>
    <field name="t_id" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="t_basket" configurationFlags="None">
      <editWidget type="RelationReference">
        <config>
          <Option type="Map">
            <Option name="AllowAddFeatures" type="bool" value="false"/>
            <Option name="AllowNULL" type="bool" value="true"/>
            <Option name="FilterExpression" type="QString" value="&quot;topic&quot; = 'KbS_LV95_V1_4.Belastete_Standorte' and attribute(get_feature('t_ili2db_dataset', 't_id', &quot;dataset&quot;), 'datasetname') != 'Catalogueset'"/>
            <Option name="FilterFields" type="invalid"/>
            <Option name="OrderByValue" type="bool" value="true"/>
            <Option name="Relation" type="QString" value="belasteter_standort_t_basket_fkey_1"/>
            <Option name="ShowForm" type="bool" value="false"/>
            <Option name="ShowOpenFormButton" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="t_ili_tid" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="katasternummer" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="url_standort" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geo_lage_polygon" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="standorttyp" configurationFlags="None">
      <editWidget type="RelationReference">
        <config>
          <Option type="Map">
            <Option name="AllowAddFeatures" type="bool" value="false"/>
            <Option name="AllowNULL" type="bool" value="false"/>
            <Option name="MapIdentification" type="bool" value="false"/>
            <Option name="OrderByValue" type="bool" value="false"/>
            <Option name="ReadOnly" type="bool" value="false"/>
            <Option name="ReferencedLayerDataSource" type="QString" value="dbname='test data' host=localhost user='postgres' key='t_id' checkPrimaryKeyUnicity='1' table=&quot;kbs_test1126&quot;.&quot;standorttyp&quot;"/>
            <Option name="ReferencedLayerId" type="QString" value="Standorttyp_c4e588ae_fdc1_49f2_b73b_72e9b0fe13bc"/>
            <Option name="ReferencedLayerName" type="QString" value="Standorttyp"/>
            <Option name="ReferencedLayerProviderKey" type="QString" value="postgres"/>
            <Option name="Relation" type="QString" value="belasteter_standort_standorttyp_fkey_1"/>
            <Option name="ShowForm" type="bool" value="false"/>
            <Option name="ShowOpenFormButton" type="bool" value="true"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="inbetrieb" configurationFlags="None">
      <editWidget type="CheckBox">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="nachsorge" configurationFlags="None">
      <editWidget type="CheckBox">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="statusaltlv" configurationFlags="None">
      <editWidget type="RelationReference">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ersteintrag" configurationFlags="None">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option name="calendar_popup" type="bool" value="true"/>
            <Option name="display_format" type="QString" value="M/d/yy"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="letzteanpassung" configurationFlags="None">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option name="calendar_popup" type="bool" value="true"/>
            <Option name="display_format" type="QString" value="M/d/yy"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="url_kbs_auszug" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_de" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_fr" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_rm" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_it" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung_en" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="zustaendigkeitkataster" configurationFlags="None">
      <editWidget type="RelationReference">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" index="0" field="t_id"/>
    <alias name="" index="1" field="t_basket"/>
    <alias name="" index="2" field="t_ili_tid"/>
    <alias name="Katasternummer" index="3" field="katasternummer"/>
    <alias name="URL_Standort" index="4" field="url_standort"/>
    <alias name="Geo_Lage_Polygon" index="5" field="geo_lage_polygon"/>
    <alias name="Standorttyp" index="6" field="standorttyp"/>
    <alias name="InBetrieb" index="7" field="inbetrieb"/>
    <alias name="Nachsorge" index="8" field="nachsorge"/>
    <alias name="StatusAltlV" index="9" field="statusaltlv"/>
    <alias name="Ersteintrag" index="10" field="ersteintrag"/>
    <alias name="LetzteAnpassung" index="11" field="letzteanpassung"/>
    <alias name="URL_KbS_Auszug" index="12" field="url_kbs_auszug"/>
    <alias name="Bemerkung" index="13" field="bemerkung"/>
    <alias name="" index="14" field="bemerkung_de"/>
    <alias name="" index="15" field="bemerkung_fr"/>
    <alias name="Remarque en Romane" index="16" field="bemerkung_rm"/>
    <alias name="Remarque en Italien" index="17" field="bemerkung_it"/>
    <alias name="" index="18" field="bemerkung_en"/>
    <alias name="ZustaendigkeitKataster" index="19" field="zustaendigkeitkataster"/>
  </aliases>
  <defaults>
    <default expression="" applyOnUpdate="0" field="t_id"/>
    <default expression="" applyOnUpdate="0" field="t_basket"/>
    <default expression="" applyOnUpdate="0" field="t_ili_tid"/>
    <default expression="" applyOnUpdate="0" field="katasternummer"/>
    <default expression="" applyOnUpdate="0" field="url_standort"/>
    <default expression="" applyOnUpdate="0" field="geo_lage_polygon"/>
    <default expression="" applyOnUpdate="0" field="standorttyp"/>
    <default expression="" applyOnUpdate="0" field="inbetrieb"/>
    <default expression="" applyOnUpdate="0" field="nachsorge"/>
    <default expression="" applyOnUpdate="0" field="statusaltlv"/>
    <default expression="" applyOnUpdate="0" field="ersteintrag"/>
    <default expression="" applyOnUpdate="0" field="letzteanpassung"/>
    <default expression="" applyOnUpdate="0" field="url_kbs_auszug"/>
    <default expression="" applyOnUpdate="0" field="bemerkung"/>
    <default expression="" applyOnUpdate="0" field="bemerkung_de"/>
    <default expression="" applyOnUpdate="0" field="bemerkung_fr"/>
    <default expression="" applyOnUpdate="0" field="bemerkung_rm"/>
    <default expression="" applyOnUpdate="0" field="bemerkung_it"/>
    <default expression="" applyOnUpdate="0" field="bemerkung_en"/>
    <default expression="" applyOnUpdate="0" field="zustaendigkeitkataster"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" constraints="3" notnull_strength="1" field="t_id" unique_strength="1"/>
    <constraint exp_strength="0" constraints="1" notnull_strength="1" field="t_basket" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="t_ili_tid" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" notnull_strength="1" field="katasternummer" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="url_standort" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="geo_lage_polygon" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" notnull_strength="1" field="standorttyp" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="inbetrieb" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="nachsorge" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" notnull_strength="1" field="statusaltlv" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" notnull_strength="1" field="ersteintrag" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" notnull_strength="1" field="letzteanpassung" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="url_kbs_auszug" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="bemerkung" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="bemerkung_de" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="bemerkung_fr" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="bemerkung_rm" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="bemerkung_it" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" notnull_strength="0" field="bemerkung_en" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" notnull_strength="1" field="zustaendigkeitkataster" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="t_id"/>
    <constraint desc="" exp="" field="t_basket"/>
    <constraint desc="" exp="" field="t_ili_tid"/>
    <constraint desc="" exp="" field="katasternummer"/>
    <constraint desc="" exp="" field="url_standort"/>
    <constraint desc="" exp="" field="geo_lage_polygon"/>
    <constraint desc="" exp="" field="standorttyp"/>
    <constraint desc="" exp="" field="inbetrieb"/>
    <constraint desc="" exp="" field="nachsorge"/>
    <constraint desc="" exp="" field="statusaltlv"/>
    <constraint desc="" exp="" field="ersteintrag"/>
    <constraint desc="" exp="" field="letzteanpassung"/>
    <constraint desc="" exp="" field="url_kbs_auszug"/>
    <constraint desc="" exp="" field="bemerkung"/>
    <constraint desc="" exp="" field="bemerkung_de"/>
    <constraint desc="" exp="" field="bemerkung_fr"/>
    <constraint desc="" exp="" field="bemerkung_rm"/>
    <constraint desc="" exp="" field="bemerkung_it"/>
    <constraint desc="" exp="" field="bemerkung_en"/>
    <constraint desc="" exp="" field="zustaendigkeitkataster"/>
  </constraintExpressions>
  <expressionfields/>
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
    <attributeEditorContainer showLabel="1" name="Général" visibilityExpressionEnabled="0" columnCount="2" groupBox="0" visibilityExpression="">
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
    <attributeEditorContainer showLabel="1" name="Parzellenidentifikation" visibilityExpressionEnabled="0" columnCount="1" groupBox="0" visibilityExpression="">
      <attributeEditorRelation showLabel="1" nmRelationId="" label="" name="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey_1" relation="parzellenidentifikation_belsttr_stndr_przllnvrweis_fkey_1" forceSuppressFormPopup="0" relationWidgetTypeId="">
        <editor_configuration type="Map">
          <Option name="buttons" type="QString" value="AllButtons"/>
        </editor_configuration>
      </attributeEditorRelation>
    </attributeEditorContainer>
    <attributeEditorContainer showLabel="1" name="Deponie" visibilityExpressionEnabled="0" columnCount="1" groupBox="0" visibilityExpression="">
      <attributeEditorRelation showLabel="1" nmRelationId="" label="" name="deponietyp__belasteter_standort_dpntyp_fkey_1" relation="deponietyp__belasteter_standort_dpntyp_fkey_1" forceSuppressFormPopup="0" relationWidgetTypeId="">
        <editor_configuration type="Map">
          <Option name="buttons" type="QString" value="AllButtons"/>
        </editor_configuration>
      </attributeEditorRelation>
    </attributeEditorContainer>
    <attributeEditorContainer showLabel="1" name="Egrid" visibilityExpressionEnabled="0" columnCount="1" groupBox="0" visibilityExpression="">
      <attributeEditorRelation showLabel="1" nmRelationId="" label="" name="egrid__belasteter_standort_egrid_fkey_1" relation="egrid__belasteter_standort_egrid_fkey_1" forceSuppressFormPopup="0" relationWidgetTypeId="">
        <editor_configuration type="Map">
          <Option name="buttons" type="QString" value="AllButtons"/>
        </editor_configuration>
      </attributeEditorRelation>
    </attributeEditorContainer>
    <attributeEditorContainer showLabel="1" name="Untersuchungsmassnahmen" visibilityExpressionEnabled="0" columnCount="1" groupBox="0" visibilityExpression="">
      <attributeEditorRelation showLabel="1" nmRelationId="" label="" name="untersmassn__belsttr_stndrchngsmssnhmen_fkey_1" relation="untersmassn__belsttr_stndrchngsmssnhmen_fkey_1" forceSuppressFormPopup="0" relationWidgetTypeId="">
        <editor_configuration type="Map">
          <Option name="buttons" type="QString" value="AllButtons"/>
        </editor_configuration>
      </attributeEditorRelation>
    </attributeEditorContainer>
  </attributeEditorForm>
  <editable>
    <field name="bemerkung" editable="1"/>
    <field name="bemerkung_de" editable="1"/>
    <field name="bemerkung_en" editable="1"/>
    <field name="bemerkung_fr" editable="1"/>
    <field name="bemerkung_it" editable="1"/>
    <field name="bemerkung_rm" editable="1"/>
    <field name="ersteintrag" editable="1"/>
    <field name="geo_lage_polygon" editable="1"/>
    <field name="inbetrieb" editable="1"/>
    <field name="katasternummer" editable="1"/>
    <field name="letzteanpassung" editable="1"/>
    <field name="nachsorge" editable="1"/>
    <field name="standorttyp" editable="1"/>
    <field name="statusaltlv" editable="1"/>
    <field name="t_basket" editable="1"/>
    <field name="t_id" editable="1"/>
    <field name="t_ili_tid" editable="1"/>
    <field name="url_kbs_auszug" editable="1"/>
    <field name="url_standort" editable="1"/>
    <field name="zustaendigkeitkataster" editable="1"/>
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
  <previewExpression>'French: '||standorttyp ||' - '||katasternummer</previewExpression>
  <layerGeometryType>0</layerGeometryType>
</qgis>
