#!/bin/bash

echo "🚀 Tanya Ma'il Setup dengan Virtual Environment"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 tidak ditemukan. Please install Python 3.8 atau lebih baru."
    exit 1
fi

echo "✅ Python 3 ditemukan: $(python3 --version)"

# Create virtual environment
echo "📦 Membuat virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment berhasil dibuat"
else
    echo "⚠️  Virtual environment sudah ada"
fi

# Activate virtual environment
echo "🔄 Mengaktifkan virtual environment..."
source ./venv/bin/activate

# Upgrade pip
echo "🔧 Mengupgrade pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🎯 To use the application:"
echo "1. Activate venv: source ./venv/bin/activate"
echo "2. Set API key: export OPENAI_API_KEY='your-key-here'"
echo "3. Start API: python run_streaming_api.py"
echo "4. Test client: python client_streaming.py"
echo ""
echo "📚 Optional environment variables:"
echo "   export MONGO_URI='mongodb://localhost:27017'"
echo "   export MODEL_NAME='gpt-4o-mini'"
echo ""
echo "🔧 Deactivate venv when done: deactivate"

# Install dependencies
echo "📥 Menginstall dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup berhasil!"
echo "=============================================="
echo "💡 Untuk menggunakan:"
echo "1. Aktivasi venv: source venv/bin/activate"
echo "2. Jalankan API: python run_streaming_api.py"
echo "3. Test client: python client_streaming.py"
echo ""
echo "🛑 Untuk deaktivasi: deactivate"
echo "=============================================="
