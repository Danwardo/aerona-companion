import sqlite3, json, time
from contextlib import contextmanager
class Store:
    def __init__(self, path):
        self.path=path
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, ts REAL, kind TEXT, payload TEXT)')
            db.execute('CREATE INDEX IF NOT EXISTS time_idx ON records(ts)')
            db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path, timeout=30)
        try:
            with db: yield db
        finally:
            db.close()
    def settings(self):
        with self.connect() as db:
            return {k:json.loads(v) for k,v in db.execute('SELECT key,value FROM settings')}
    def configure(self, values):
        with self.connect() as db:
            for k,v in values.items(): db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',(k,json.dumps(v)))
    def add(self, kind, payload, retention=0):
        now=time.time()
        with self.connect() as db:
            db.execute('INSERT INTO records(ts,kind,payload) VALUES (?,?,?)',(now,kind,json.dumps(payload)))
            if retention: db.execute('DELETE FROM records WHERE ts < ?',(now-retention*86400,))
    def status(self):
        with self.connect() as db:
            count,first,last=db.execute('SELECT COUNT(*),MIN(ts),MAX(ts) FROM records').fetchone()
        return dict(records=count,first=first,last=last)
    def export(self,start,end,offset=0,limit=2000):
        with self.connect() as db:
            rows=db.execute('SELECT id,ts,kind,payload FROM records WHERE ts>=? AND ts<=? ORDER BY id LIMIT ? OFFSET ?',(start,end,limit,offset)).fetchall()
        return [dict(id=i,timestamp=ts,kind=k,payload=json.loads(p)) for i,ts,k,p in rows]
