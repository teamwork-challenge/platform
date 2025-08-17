# Ensure local modules (like firebase_db.py) are importable when running pytest from this directory
import os
import sys

current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
