import pytest
from src import mirror

class DummyClient:
    def __init__(self):
        self.connected = True
        self.last_written = None
        self.read_payload = b"\x01\x00\x00\x00" * 4

    def connect(self, ip, rack, slot):
        self.connected = True

    def get_connected(self):
        return self.connected

    # Compatibility with implementations using read_area
    def read_area(self, area, dbnumber, start, size):
        return self.read_payload

    def write_area(self, area, dbnumber, start, data):
        self.last_written = data
        return True

    # Methods used by current PLCMirror implementation (db_* API)
    def db_read(self, dbnumber, start, size):
        return self.read_payload

    def db_write(self, dbnumber, start, data):
        self.last_written = data
        return True

    def disconnect(self):
        self.connected = False


def test_mirror_once(monkeypatch):
    # mock snap7.client.Client to return DummyClient
    dummy_src = DummyClient()
    dummy_dst = DummyClient()

    def make_client_side_effect():
        if not hasattr(make_client_side_effect, "count"):
            make_client_side_effect.count = 0
        make_client_side_effect.count += 1
        return dummy_src if make_client_side_effect.count == 1 else dummy_dst

    class FakeSnap7:
        class client:
            Client = staticmethod(make_client_side_effect)

    monkeypatch.setattr(mirror, "snap7", FakeSnap7)
    m = mirror.PLCMirror("1.2.3.4", "5.6.7.8", db_number=1, db_size=16)
    m.connect()
    raw = m.mirror_once()
    assert raw == dummy_src.read_payload
    assert dummy_dst.last_written == dummy_src.read_payload
    m.disconnect()
