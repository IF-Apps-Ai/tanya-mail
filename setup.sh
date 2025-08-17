#!/bin/bash

# Tanya Ma'il API Setup Script
# This script helps set up the Tanya Ma'il API environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "SUCCESS" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "ERROR" ]; then
        echo -e "${RED}❌ $message${NC}"
    elif [ "$status" = "INFO" ]; then
        echo -e "${BLUE}ℹ️  $message${NC}"
    elif [ "$status" = "WARNING" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_status "INFO" "🚀 Setting up Tanya Ma'il API..."

# Check requirements
print_status "INFO" "Checking system requirements..."

if ! command_exists docker; then
    print_status "ERROR" "Docker is required but not installed"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose; then
    print_status "ERROR" "Docker Compose is required but not installed"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

print_status "SUCCESS" "Docker and Docker Compose are installed"

# Check if .env exists
if [ ! -f .env ]; then
    print_status "WARNING" ".env file not found, copying from template..."
    cp .env.template .env
    print_status "SUCCESS" ".env file created from template"
    print_status "WARNING" "⚠️  Please edit .env file and add your OpenAI API key!"
    echo
    echo "Edit the .env file:"
    echo "nano .env"
    echo
    echo "Required: Set your OpenAI API key:"
    echo "OPENAI_API_KEY=your_actual_api_key_here"
    echo
    read -p "Press Enter after you've updated the .env file..."
else
    print_status "SUCCESS" ".env file already exists"
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" .env; then
    print_status "ERROR" "Please set your actual OpenAI API key in .env file"
    echo "Edit .env file and replace 'your_openai_api_key_here' with your actual API key"
    exit 1
fi

print_status "SUCCESS" "Environment configuration looks good"

# Create necessary directories
print_status "INFO" "Creating necessary directories..."
mkdir -p pdf_documents
mkdir -p chroma_pdf_db
print_status "SUCCESS" "Directories created"

# Make scripts executable
chmod +x test_api.sh
print_status "SUCCESS" "Scripts made executable"

# Build and start services
print_status "INFO" "Building and starting services with Docker Compose..."
docker-compose up -d --build

# Wait for services to be ready
print_status "INFO" "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_status "SUCCESS" "Services are running!"
else
    print_status "ERROR" "Some services failed to start"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

# Test the API
print_status "INFO" "Testing API connection..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "SUCCESS" "API is responding!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_status "ERROR" "API is not responding after 30 attempts"
        echo "Check logs with: docker-compose logs tanya-mail-api"
        exit 1
    fi
    sleep 2
done

echo
echo "==================== SETUP COMPLETE ===================="
print_status "SUCCESS" "Tanya Ma'il API is ready!"
echo
print_status "INFO" "🌐 Access points:"
echo "   API Base URL: http://localhost:8000"
echo "   Swagger Docs: http://localhost:8000/docs"
echo "   ReDoc Docs:   http://localhost:8000/redoc"
echo
print_status "INFO" "📁 Directories:"
echo "   PDF uploads:  ./pdf_documents/"
echo "   Vector DB:    ./chroma_pdf_db/"
echo
print_status "INFO" "🔧 Useful commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart:      docker-compose restart"
echo "   Test API:     ./test_api.sh"
echo
print_status "INFO" "📖 Next steps:"
echo "   1. Visit http://localhost:8000/docs for interactive API documentation"
echo "   2. Upload PDF files using the /upload endpoint"
echo "   3. Build vector store using /build-vectorstore"
echo "   4. Start asking questions using /ask endpoint"
echo
print_status "SUCCESS" "🎉 Happy querying!"
