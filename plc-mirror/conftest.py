import os, sys
BASE = os.path.dirname(__file__)
src = os.path.join(BASE, 'src')
if os.path.isdir(src) and src not in sys.path:
    sys.path.insert(0, src)
