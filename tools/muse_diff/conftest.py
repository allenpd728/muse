import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))  # tools/ for muse_diff
sys.path.insert(0, os.path.join(HERE, "..", "ir"))  # for muse_ir
