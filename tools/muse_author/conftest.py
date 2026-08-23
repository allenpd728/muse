import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))  # tools/ for muse_author
sys.path.insert(0, os.path.join(HERE, "..", "ir"))  # for muse_ir
sys.path.insert(0, os.path.join(HERE, "..", "muse_budgets"))  # for suggest
