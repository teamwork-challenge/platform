# Ensure project and back modules are importable when running pytest from cli directory
import os
import sys

# Add repository root and back/ to sys.path so tests can import firebase_test_setup and back modules
repo_root = os.path.dirname(os.path.dirname(__file__))
back_dir = os.path.join(repo_root, "back")

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if back_dir not in sys.path:
    sys.path.insert(0, back_dir)
