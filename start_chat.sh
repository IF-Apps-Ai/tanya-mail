#!/bin/bash
# Tanya Ma'il Chat Streaming Launcher
# Quick launcher untuk chat streaming interface

echo "🚀 Starting Tanya Ma'il Streaming Chat Interface..."
echo "=================================================="

# Check if API server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "⚠️  API server tidak berjalan. Memulai server..."
    echo "📡 Starting API server in background..."
    
    # Start API server in background
    nohup python run_streaming_api.py > api_server.log 2>&1 &
    
    # Wait for server to start
    echo "⏳ Menunggu server startup..."
    sleep 8
    
    # Check if server is now running
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API server berhasil dijalankan!"
    else
        echo "❌ Gagal menjalankan API server. Check log: api_server.log"
        exit 1
    fi
else
    echo "✅ API server sudah berjalan!"
fi

echo ""
echo "🤖 Memulai Chat Streaming Interface..."
echo "💡 Tips: Ketik 'help' untuk bantuan atau 'exit' untuk keluar"
echo "=================================================="
echo ""

# Start chat streaming interface
python chat_streaming.py
