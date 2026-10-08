import importlib.util,pathlib,tempfile,time,unittest
spec=importlib.util.spec_from_file_location('store',pathlib.Path(__file__).parents[1]/'custom_components/aerona_companion/store.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class StoreTest(unittest.TestCase):
 def test_archive(self):
  with tempfile.TemporaryDirectory() as d:
   s=m.Store(d+'/archive.sqlite');s.configure({'interval':60});self.assertEqual(m.Store(s.path).settings()['interval'],60)
   s.add('sample',{'flow':{'state':'unavailable'}});s.add('change',{'old':'off','new':'on'})
   self.assertEqual(len(s.export(0,time.time(),0,1)),1);self.assertEqual(len(s.export(0,time.time(),1,1)),1)
   self.assertEqual(s.export(0,time.time())[0]['payload']['flow']['state'],'unavailable')
   with s.connect() as db:db.execute('INSERT INTO records(ts,kind,payload) VALUES (?,?,?)',(time.time()-100*86400,'sample','{}'))
   s.add('note',{'note':'keep'},0);self.assertEqual(s.status()['records'],4)
   s.add('note',{'note':'prune'},30);self.assertEqual(s.status()['records'],4)
if __name__=='__main__':unittest.main()
