"""Exercise the submitted source step against a read-only HA source property."""
import ast,asyncio,pathlib,types,unittest
class FlowTest(unittest.TestCase):
 def test_selected_grant_advances_with_readonly_source(self):
  tree=ast.parse((pathlib.Path(__file__).parents[1]/'custom_components/aerona_companion/config_flow.py').read_text())
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CompanionFlow')
  method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='async_step_user')
  namespace={};exec(compile(ast.Module(body=[method],type_ignores=[]),'flow','exec'),namespace)
  class Base:
   @property
   def source(self):return 'user'
   def _async_current_entries(self):return []
   async def async_step_entities(self):return {'step_id':'entities'}
  obj=Base();obj.hass=types.SimpleNamespace(config_entries=types.SimpleNamespace(async_entries=lambda domain:[types.SimpleNamespace(entry_id='grant-id',title='Grant')]))
  result=asyncio.run(namespace['async_step_user'](obj,{'source':'grant-id'}))
  self.assertEqual(result['step_id'],'entities');self.assertEqual(obj._grant_source,'grant-id');self.assertEqual(obj.source,'user')
