import json, os, sqlite3, time
from threading import Lock
from typing import Dict, List, Tuple

DDL = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    payload TEXT NOT NULL
);
"""

class StoreForward:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = Lock()
        self._conn.execute(DDL)
        self._conn.commit()

    def enqueue(self, payload: Dict):
        with self._lock:
            self._conn.execute('INSERT INTO events(ts, payload) VALUES(?,?)', (time.time(), json.dumps(payload)))
            self._conn.commit()

    def dequeue(self, limit: int = 100) -> List[Tuple[int, Dict]]:
        with self._lock:
            cur = self._conn.execute('SELECT id, payload FROM events ORDER BY id ASC LIMIT ?', (limit,))
            rows = cur.fetchall()
        return [(rid, json.loads(p)) for (rid, p) in rows]

    def delete_ids(self, ids: List[int]):
        if not ids: return
        q = 'DELETE FROM events WHERE id IN (%s)' % ','.join('?' for _ in ids)
        with self._lock:
            self._conn.execute(q, ids)
            self._conn.commit()

    def count(self) -> int:
        with self._lock:
            cur = self._conn.execute('SELECT COUNT(1) FROM events')
            row = cur.fetchone()
        return int(row[0]) if row else 0
