#!/bin/bash
# Start JIM AI GUI Launcher - Double-click to run

echo "🖥️  Starting JIM AI Desktop Launcher..."
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

# Check if GUI components are available
echo "🔧 Checking GUI dependencies..."
python3 -c "import tkinter" 2>/dev/null || {
    echo "❌ GUI components not available on this system."
    echo "🌐 Opening web interface instead..."
    open http://localhost:8080
    python3 app.py
    exit 0
}

# Check if Flask app is running, if not start it
echo "🌐 Starting web service..."
python3 app.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Start the GUI launcher
echo "🖥️  Opening desktop interface..."
python3 JIM_AI_Launcher.py

# Clean up Flask process when GUI closes
echo "🧹 Cleaning up..."
kill $FLASK_PID 2>/dev/null

echo "✅ JIM AI closed successfully"