#!/bin/bash
# Build script for Render deployment

echo "Setting up Python environment..."
python --version

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!" 