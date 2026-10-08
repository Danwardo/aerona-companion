"""Read-only state logger, with authenticated paginated downloads."""
import time
from datetime import timedelta
import voluptuous as vol
from homeassistant.core import callback
from homeassistant.components import websocket_api
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers import config_validation as cv
from .store import Store
from .const import DOMAIN
async def async_setup(hass,config):
    return True

async def async_setup_entry(hass,entry):
    conf={'entities':entry.options.get('entities',entry.data['entities']),'interval':60,'retention_days':0}
    store=await hass.async_add_executor_job(Store,hass.config.path('aerona_companion.sqlite'))
    settings={'interval':conf['interval'],'retention_days':conf['retention_days'],'enabled':True}
    settings.update(await hass.async_add_executor_job(store.settings))
    data={'store':store,'settings':settings,'entities':conf['entities'],'last_sample':0}
    hass.data[DOMAIN]=data
    data['entry']=entry
    async def write(kind,payload):
        if settings['enabled']:
            await hass.async_add_executor_job(store.add,kind,payload,settings['retention_days'])
    def snapshot():
        return {role:{'entity_id':entity,'state':hass.states.get(entity).state if hass.states.get(entity) else 'missing','unit':hass.states.get(entity).attributes.get('unit_of_measurement') if hass.states.get(entity) else None} for role,entity in conf['entities'].items()}
    async def changed(event):
        old,new=event.data['old_state'],event.data['new_state']
        if old and new and old.state==new.state:return
        await write('change',{'entity_id':event.data['entity_id'],'old':old.state if old else None,'new':new.state if new else None,'readings':snapshot()})
    async def tick(now):
        if time.time()-data['last_sample']>=settings['interval']:
            await write('sample',snapshot());data['last_sample']=time.time()
    remove_states=async_track_state_change_event(hass,list(conf['entities'].values()),changed)
    remove_tick=async_track_time_interval(hass,tick,timedelta(seconds=10))
    @callback
    def stop(event):remove_states();remove_tick()
    entry.async_on_unload(remove_states)
    entry.async_on_unload(remove_tick)
    entry.async_on_unload(entry.add_update_listener(update_options))
    await write('session',{'event':'logger_started','readings':snapshot()})
    if not hass.data.get(DOMAIN+'_registered'):
        await register_frontend(hass)
        hass.data[DOMAIN+'_registered']=True
    websocket_api.async_register_command(hass,ws_status)
    websocket_api.async_register_command(hass,ws_configure)
    websocket_api.async_register_command(hass,ws_note)
    websocket_api.async_register_command(hass,ws_export)
    return True
@websocket_api.websocket_command({vol.Required('type'):'aerona_companion/status'})
@websocket_api.async_response
async def ws_status(hass,connection,msg):
    d=hass.data[DOMAIN];status=await hass.async_add_executor_job(d['store'].status)
    connection.send_result(msg['id'],{'settings':d['settings'],'entities':d['entities'],'missing':[role for role,entity in d['entities'].items() if not hass.states.get(entity) or hass.states.get(entity).state in ['unknown','unavailable']],**status})
@websocket_api.websocket_command({vol.Required('type'):'aerona_companion/configure',vol.Required('interval'):vol.All(vol.Coerce(int),vol.Range(min=10,max=3600)),vol.Required('retention_days'):vol.All(vol.Coerce(int),vol.Range(min=0,max=36500)),vol.Required('enabled'):bool})
@websocket_api.async_response
async def ws_configure(hass,connection,msg):
    if not connection.user.is_admin:
        connection.send_error(msg['id'],'unauthorized','Administrator required');return
    d=hass.data[DOMAIN];values={k:msg[k] for k in ['interval','retention_days','enabled']}
    await hass.async_add_executor_job(d['store'].configure,values)
    d['settings'].update(values)
    await hass.async_add_executor_job(d['store'].add,'session',{'event':'configuration_changed','settings':values},0)
    connection.send_result(msg['id'],values)
@websocket_api.websocket_command({vol.Required('type'):'aerona_companion/note',vol.Required('note'):vol.All(str,vol.Length(min=1,max=1000))})
@websocket_api.async_response
async def ws_note(hass,connection,msg):
    if not connection.user.is_admin:
        connection.send_error(msg['id'],'unauthorized','Administrator required');return
    d=hass.data[DOMAIN]
    await hass.async_add_executor_job(d['store'].add,'note',{'note':msg['note']},0)
    connection.send_result(msg['id'],True)
@websocket_api.websocket_command({vol.Required('type'):'aerona_companion/export',vol.Required('start'):vol.Coerce(float),vol.Required('end'):vol.Coerce(float),vol.Optional('offset',default=0):vol.All(int,vol.Range(min=0))})
@websocket_api.async_response
async def ws_export(hass,connection,msg):
    if not connection.user.is_admin:
        connection.send_error(msg['id'],'unauthorized','Administrator required');return
    rows=await hass.async_add_executor_job(hass.data[DOMAIN]['store'].export,msg['start'],msg['end'],msg['offset'])
    connection.send_result(msg['id'],rows)

async def update_options(hass,entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass,entry):
    from homeassistant.components import frontend
    frontend.async_remove_panel(hass,'aerona-companion')
    hass.data.pop(DOMAIN,None)
    hass.data.pop(DOMAIN+'_registered',None)
    return True

async def register_frontend(hass):
    from pathlib import Path
    from homeassistant.components.http import StaticPathConfig
    from homeassistant.components import frontend
    if not hass.data.get(DOMAIN+'_static'):
        await hass.http.async_register_static_paths([StaticPathConfig('/aerona_companion/frontend',str(Path(__file__).parent/'frontend'),False)])
        hass.data[DOMAIN+'_static']=True
    frontend.async_register_built_in_panel(hass,component_name='custom',sidebar_title='Aerona Companion',sidebar_icon='mdi:heat-pump',frontend_url_path='aerona-companion',config={'_panel_custom':{'name':'aerona-companion-panel','module_url':'/aerona_companion/frontend/aerona-luxe.js?v=030','embed_iframe':False,'trust_external':False}},require_admin=True)
