"""Vercel serverless function entry point."""
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.server.main import app

# Vercel expects a variable named 'app'
# This will be the ASGI application
handler = app
