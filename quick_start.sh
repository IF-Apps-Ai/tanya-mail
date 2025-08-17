#!/bin/bash

echo "🏃 Quick Start Tanya Ma'il dengan Virtual Environment"
echo "===================================================="

# Setup venv if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📋 Installing/updating dependencies..."
pip install -r requirements.txt

# Check environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set!"
    echo "Please set it: export OPENAI_API_KEY='your-key-here'"
    echo ""
fi

# Start API server in background
echo "🚀 Starting API server..."
python run_streaming_api.py &
API_PID=$!

# Wait for API to start
echo "⏳ Waiting for API to start..."
sleep 3

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API server is running!"
    
    # Check if we have documents
    DOCS=$(curl -s http://localhost:8000/files | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))")
    
    if [ "$DOCS" = "0" ]; then
        echo ""
        echo "📭 No documents found. Please:"
        echo "1. Upload a PDF file using the client"
        echo "2. Build the vector store"
        echo ""
    else
        echo "📚 Found $DOCS document(s)"
    fi
    
    echo ""
    echo "🎯 Ready to use! Run in another terminal:"
    echo "   source venv/bin/activate"
    echo "   python client_streaming.py"
    echo ""
    echo "Press Ctrl+C to stop the API server"
    echo ""
    
    # Wait for interrupt
    wait $API_PID
else
    echo "❌ Failed to start API server"
    kill $API_PID 2>/dev/null
    exit 1
fi
