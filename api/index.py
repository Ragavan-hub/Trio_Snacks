"""
Vercel serverless entry point for Trio Snacks Flask application
"""
import os
import sys

# Mark environment as Vercel serverless
os.environ.setdefault("VERCEL", "1")

# Ensure project root is on sys.path
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from app import app  # noqa: E402

# Vercel Python runtime looks for `app` (WSGI application)
handler = app
