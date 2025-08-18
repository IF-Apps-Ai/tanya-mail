#!/bin/bash

# Quick commands untuk AI Document Analysis Bulk PDF Processor

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get APP_NAME from .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    APP_NAME=$(grep "^APP_NAME=" "$SCRIPT_DIR/.env" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    APP_NAME=${APP_NAME:-"AI Document Processor"}
else
    APP_NAME="AI Document Processor"
fi

# Alias functions
bulk_pdf() {
    cd "$SCRIPT_DIR"
    ./process_bulk_pdf.sh "$@"
}

bulk_pdf_preview() {
    cd "$SCRIPT_DIR"
    ./process_bulk_pdf.sh --dry-run "$@"
}

bulk_pdf_force() {
    cd "$SCRIPT_DIR"
    ./process_bulk_pdf.sh --force "$@"
}

# Export functions
export -f bulk_pdf
export -f bulk_pdf_preview  
export -f bulk_pdf_force

echo "🚀 ${APP_NAME} Bulk PDF Commands loaded!"
echo ""
echo "Available commands:"
echo "  bulk_pdf              - Process all PDFs in pdf_input"
echo "  bulk_pdf_preview      - Preview files without processing"  
echo "  bulk_pdf_force        - Force reprocess existing files"
echo ""
echo "Examples:"
echo "  bulk_pdf"
echo "  bulk_pdf_preview"
echo "  bulk_pdf --folder documents"
echo "  bulk_pdf_force"
echo ""
echo "📁 Put your PDF files in the 'pdf_input' folder first!"
