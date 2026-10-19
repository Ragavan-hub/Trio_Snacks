"""
Vercel serverless entry point for Trio Snacks Flask application
"""
import os
import sys
import traceback

# Mark environment as Vercel serverless
os.environ.setdefault("VERCEL", "1")

# Ensure project root is on sys.path
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from app import app
except Exception as e:
    # Print the full startup traceback directly to Vercel logs
    print("CRITICAL: Failed to import Flask app:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    raise e

# Vercel's Python runtime directly expects the callable 'app'
# (No need to assign to handler)