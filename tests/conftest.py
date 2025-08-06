# tests/conftest.py
import os
import sys

# Insert project root into sys.path so `agents` and `utils` can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
