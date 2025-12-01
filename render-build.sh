#!/bin/bash
# Build script for Render.com deployment

echo "Installing system dependencies..."
apt-get update
apt-get install -y ffmpeg

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build complete!"
