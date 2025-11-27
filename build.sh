#!/bin/bash
# Build script for Vercel deployment
# This runs during Vercel build phase

echo "Installing Python dependencies for Vercel..."

# Use requirements-vercel.txt which excludes Playwright
pip install -r requirements-vercel.txt

echo "Build complete!"
