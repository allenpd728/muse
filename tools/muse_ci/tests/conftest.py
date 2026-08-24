import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", ".."))          # tools/
sys.path.insert(0, os.path.join(HERE, "..", "..", "ir"))   # for muse_ir
sys.path.insert(0, os.path.join(HERE, "..", "..", "s1_stream"))  # for muse_stream
