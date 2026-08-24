import os
import sys

_HERE = os.path.dirname(__file__)
# Guarantee stable import location regardless of pytest's package discovery.
IR_PATH = os.path.normpath(os.path.join(_HERE, "..", "ir"))
if IR_PATH not in sys.path:
    sys.path.insert(0, IR_PATH)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
