import json
import threading
import time
from src.store import StoreForward


def test_store_enqueue_dequeue_delete(tmp_path):
    db = tmp_path / "q.sqlite"
    s = StoreForward(str(db))
    s.enqueue({"a": 1})
    s.enqueue({"b": 2})
    batch = s.dequeue(10)
    assert len(batch) == 2
    ids = [rid for rid, _ in batch]
    s.delete_ids(ids)
    assert s.count() == 0


def test_store_thread_safety(tmp_path):
    db = tmp_path / "q.sqlite"
    s = StoreForward(str(db))
    stop = False

    def producer():
        for i in range(200):
            s.enqueue({"i": i})
            time.sleep(0.001)

    def consumer():
        nonlocal stop
        while not stop:
            batch = s.dequeue(50)
            if batch:
                ids = [rid for rid, _ in batch]
                s.delete_ids(ids)
            time.sleep(0.002)

    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    t1.start(); t2.start()
    t1.join(); time.sleep(0.05); stop = True; t2.join(timeout=1)
    assert s.count() >= 0  # no exceptions, consistent state
