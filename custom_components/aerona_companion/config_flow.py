import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector
from .const import DOMAIN,SUFFIXES,LABELS,REQUIRED

def guesses(hass,source):
    registry=er.async_get(hass)
    entries=er.async_entries_for_config_entry(registry,source)
    result={}
    for role,suffix in SUFFIXES.items():
        matches=[e for e in entries if e.unique_id.endswith(suffix) and not e.disabled_by]
        if len(matches)==1:result[role]=matches[0].entity_id
    return result

def schema(defaults):
    fields={}
    for role in LABELS:
        key=vol.Required if role in REQUIRED else vol.Optional
        kwargs={'default':defaults[role]} if defaults.get(role) else {}
        domains=['binary_sensor'] if role in ['compressor','defrost','heating_demand','dhw_active'] else ['number'] if role.startswith('curve_') or role.startswith('outdoor_') else ['input_number','number'] if role.startswith('tariff_') and role!='tariff_price' else ['sensor']
        fields[key(role,**kwargs)]=selector.EntitySelector(selector.EntitySelectorConfig(domain=domains))
    return vol.Schema(fields)

class CompanionFlow(config_entries.ConfigFlow,domain=DOMAIN):
    VERSION=1
    async def async_step_user(self,user_input=None):
        if self._async_current_entries():return self.async_abort(reason='single_instance_allowed')
        sources={e.entry_id:e.title for e in self.hass.config_entries.async_entries('grant_aerona3')}
        if not sources:return self.async_abort(reason='grant_missing')
        if user_input:
            self._grant_source=user_input['source'];return await self.async_step_entities()
        return self.async_show_form(step_id='user',data_schema=vol.Schema({vol.Required('source'):vol.In(sources)}))
    async def async_step_entities(self,user_input=None):
        if user_input is not None:
            return self.async_create_entry(title='Aerona Companion',data={'source':self._grant_source,'entities':user_input})
        return self.async_show_form(step_id='entities',data_schema=schema(guesses(self.hass,self._grant_source)))
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):return CompanionOptions()

class CompanionOptions(config_entries.OptionsFlow):
    async def async_step_init(self,user_input=None):
        if user_input is not None:return self.async_create_entry(title='',data={'entities':user_input})
        return self.async_show_form(step_id='init',data_schema=schema(self.config_entry.options.get('entities',self.config_entry.data['entities'])))
