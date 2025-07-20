#!/bin/bash
# Quick Start Script for Interactive Storytelling API

echo "🏛️ Interactive Storytelling API - Quick Start"
echo "============================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed or not in PATH!"
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python found: $(python --version)"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found! Please run this script from the project directory."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies!"
    exit 1
fi

echo "✅ Dependencies installed successfully!"

# Check if .env file exists and has API key
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create a .env file with your Gemini API key."
    exit 1
fi

if ! grep -q "GEMINI_API_KEY=AIzaSy" .env; then
    echo "⚠️  Gemini API key not found in .env file!"
    echo "Please add your Gemini API key to the .env file."
fi

echo ""
echo "🚀 Starting the API server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API documentation: http://localhost:8000/docs"
echo "🎮 Test interface: Open app.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
