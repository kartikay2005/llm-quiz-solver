"""Vercel serverless function entry point."""
import sys
import os

# Set environment before any imports
os.environ['VERCEL'] = '1'

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import FastAPI app
try:
    from app.server.main import app
    
    # Vercel handler - this is the entry point
    def handler(request):
        """ASGI handler for Vercel."""
        return app(request)
    
except Exception as e:
    # Fallback minimal app for debugging
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"error": str(e), "message": "Failed to import main app"}
    
    @app.get("/healthz")
    def health():
        return {"status": "error", "detail": str(e)}
    
    def handler(request):
        return app(request)
