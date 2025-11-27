"""Vercel serverless function entry point."""
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set VERCEL environment variable before importing
os.environ['VERCEL'] = '1'

from app.server.main import app

# Vercel expects this specific export
app = app
