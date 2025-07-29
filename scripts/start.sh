#!/bin/bash

# Nexus Aggregator - Quick Start Script

echo "🚀 Starting Nexus Aggregator..."
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is required but not installed."
    exit 1
fi

# Use pip3 if available, otherwise pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

echo "📦 Installing dependencies..."
$PIP_CMD install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi

echo "✅ Dependencies installed successfully!"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Using default configuration."
    echo "   You can create a .env file to customize settings."
fi

echo "🌐 Starting the server..."
echo "   Access the API at: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 main.py
