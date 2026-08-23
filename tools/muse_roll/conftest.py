import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))  # tools/
sys.path.insert(0, os.path.join(HERE, "..", "ir"))  # for muse_ir
sys.path.insert(0, os.path.join(HERE, "..", "muse_diff"))  # for W4
