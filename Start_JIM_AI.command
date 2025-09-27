#!/bin/bash
# Start JIM AI - Double-click to run

echo "🚀 Starting JIM AI Forensic Analysis..."
echo "========================================"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📂 Project directory: $SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "jim-ai-env" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating Python environment..."
source jim-ai-env/bin/activate

# Check if required files exist
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please check installation."
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

echo "🌐 Starting web interface..."
echo "📱 Open your browser to: http://localhost:8080"
echo "🛑 Press Ctrl+C to stop the application"
echo "========================================"

# Start the Flask application
python3 app.py