from src import mirror
class DummyClient:
    def __init__(self):
        self.connected = True
        self.last_written = None
        self.read_payload = b"X"*16
    def connect(self, *a, **k):
        pass
    def get_connected(self):
        return True
    def read_area(self, *a, **k):
        return self.read_payload
    def write_area(self, *a, **k):
        self.last_written = a, k
        return True
    def disconnect(self):
        pass

def factory():
    if not hasattr(factory, 'n'):
        factory.n = 0
    factory.n += 1
    return DummyClient()

class FakeSnap7:
    class client:
        Client = staticmethod(factory)

mirror.snap7 = FakeSnap7
m = mirror.PLCMirror('1.2.3.4','5.6.7.8')
m.connect()
raw = m.mirror_once()
print('OK', len(raw))
m.disconnect()
