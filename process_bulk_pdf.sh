#!/bin/bash

# Bulk PDF Processor Runner
# Script wrapper untuk menjalankan bulk PDF processor dengan virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    log_error "Virtual environment tidak ditemukan!"
    log_info "Jalankan: ./setup_venv.sh"
    exit 1
fi

# Check if bulk processor exists
if [ ! -f "bulk_pdf_processor.py" ]; then
    log_error "bulk_pdf_processor.py tidak ditemukan!"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if pdf_input folder exists
if [ ! -d "pdf_input" ]; then
    log_warning "Folder pdf_input tidak ditemukan, membuat folder baru..."
    mkdir -p pdf_input
    log_success "Folder pdf_input berhasil dibuat"
fi

# Get APP_NAME from .env file
if [ -f ".env" ]; then
    APP_NAME=$(grep "^APP_NAME=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    APP_NAME=${APP_NAME:-"Tanya Mail"}
else
    APP_NAME="Tanya Mail"
fi

# Show help if no arguments
if [ $# -eq 0 ]; then
    echo -e "${BLUE}🚀 ${APP_NAME} - Bulk PDF Processor${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h           Tampilkan help"
    echo "  --dry-run           Preview file tanpa memproses"
    echo "  --folder <folder>   Folder sumber PDF (default: pdf_input)"
    echo "  --force             Force reprocess file yang sudah ada"
    echo ""
    echo "Contoh:"
    echo "  $0                           # Proses semua PDF di pdf_input"
    echo "  $0 --dry-run                 # Preview file yang akan diproses"
    echo "  $0 --folder documents        # Proses PDF di folder documents"
    echo "  $0 --force                   # Proses ulang semua file"
    echo ""
    echo -e "${YELLOW}📁 Pastikan file PDF sudah diletakkan di folder pdf_input${NC}"
    exit 0
fi

# Run the bulk processor
log_info "Menjalankan bulk PDF processor..."
python bulk_pdf_processor.py "$@"

# Check exit status
if [ $? -eq 0 ]; then
    log_success "✅ Bulk processing selesai"
else
    log_error "❌ Bulk processing gagal"
    exit 1
fi
