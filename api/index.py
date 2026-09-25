import os
import sys

# The Flask app lives in web_viewer/app.py (not a Python package), so make
# that directory importable and pull in its `app` WSGI object. Vercel's
# Python runtime looks for exactly that: a module-level `app`.
_WEB_VIEWER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "web_viewer")
sys.path.insert(0, os.path.abspath(_WEB_VIEWER_DIR))

from app import app  # noqa: E402
