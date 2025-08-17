#!/bin/bash

# Production Deployment Script for Tanya Mail API
# This script sets up the API for production with clustering support

set -e  # Exit on any error

# Configuration
APP_NAME="tanya-mail-api"
APP_DIR="/workspaces/tanya-mail"
SERVICE_USER="codespace"
VENV_DIR="$APP_DIR/.venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Check if current directory is correct
check_directory() {
    if [ ! -f "api.py" ] || [ ! -f "gunicorn_config.py" ]; then
        log_error "Please run this script from the tanya-mail application directory"
        exit 1
    fi
    log_success "✅ Application directory confirmed"
}

# Check virtual environment
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found at $VENV_DIR"
        log_info "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    log_success "✅ Virtual environment found"
}

# Check dependencies
check_dependencies() {
    log_info "Checking Python dependencies..."
    source "$VENV_DIR/bin/activate"
    
    # Check if gunicorn is installed
    if ! python -c "import gunicorn" 2>/dev/null; then
        log_warning "Gunicorn not found, installing..."
        pip install gunicorn
    fi
    
    # Check if all requirements are satisfied
    pip check
    log_success "✅ All dependencies satisfied"
}

# Test configuration
test_configuration() {
    log_info "Testing Gunicorn configuration..."
    source "$VENV_DIR/bin/activate"
    
    # Test if configuration loads correctly
    python -c "
import sys
sys.path.append('.')
try:
    from gunicorn_config import *
    print(f'✅ Configuration loaded successfully')
    print(f'📡 Bind address: {bind}')
    print(f'👥 Workers: {workers}')
    print(f'🔧 Worker class: {worker_class}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"
    log_success "✅ Configuration test passed"
}

# Stop existing processes
stop_existing_processes() {
    log_info "Checking for existing Gunicorn processes..."
    
    # Find and stop existing gunicorn processes for this app
    PIDS=$(pgrep -f "gunicorn.*api:app" || echo "")
    
    if [ ! -z "$PIDS" ]; then
        log_warning "Found existing processes, stopping them..."
        echo "$PIDS" | xargs -r kill -TERM
        sleep 3
        
        # Force kill if still running
        REMAINING_PIDS=$(pgrep -f "gunicorn.*api:app" || echo "")
        if [ ! -z "$REMAINING_PIDS" ]; then
            log_warning "Force killing remaining processes..."
            echo "$REMAINING_PIDS" | xargs -r kill -KILL
        fi
        log_success "✅ Existing processes stopped"
    else
        log_success "✅ No existing processes found"
    fi
}

# Create production directories
create_directories() {
    log_info "Creating production directories..."
    
    # Ensure log directory exists
    mkdir -p logs
    
    # Ensure PDF documents directory exists
    mkdir -p pdf_documents
    
    # Set proper permissions
    chmod 755 logs pdf_documents
    
    log_success "✅ Directories created"
}

# Install systemd service
install_systemd_service() {
    log_info "Installing systemd service..."
    
    if [ "$EUID" -ne 0 ]; then
        log_warning "Systemd service installation requires sudo privileges"
        log_info "You can install manually later with: sudo ./service_manager.sh install"
        return 0
    fi
    
    # Install using the service manager
    ./service_manager.sh install
    log_success "✅ Systemd service installed"
}

# Test API after deployment
test_api_health() {
    log_info "Testing API health..."
    
    # Get port from .env
    PORT=$(grep "^PORT=" .env | cut -d'=' -f2 2>/dev/null || echo "8804")
    
    # Wait a bit for service to start
    log_info "Waiting for service to start..."
    sleep 5
    
    # Test health endpoint
    for i in {1..10}; do
        if curl -s "http://localhost:$PORT/health" > /dev/null; then
            log_success "✅ API is responding on port $PORT"
            
            # Show health response
            HEALTH=$(curl -s "http://localhost:$PORT/health")
            echo -e "${GREEN}Health Status:${NC} $HEALTH"
            return 0
        else
            log_info "Attempt $i/10: API not ready yet, waiting..."
            sleep 2
        fi
    done
    
    log_error "❌ API health check failed after 10 attempts"
    return 1
}

# Show deployment summary
show_summary() {
    PORT=$(grep "^PORT=" .env | cut -d'=' -f2 2>/dev/null || echo "8804")
    
    echo ""
    echo "=================================="
    echo -e "${GREEN}🚀 DEPLOYMENT SUMMARY${NC}"
    echo "=================================="
    echo -e "📁 Application: ${BLUE}Tanya Mail API${NC}"
    echo -e "📂 Directory: ${BLUE}$APP_DIR${NC}"
    echo -e "🌐 Port: ${BLUE}$PORT${NC}"
    echo -e "👥 Clustering: ${GREEN}Enabled${NC} (Multi-worker with Gunicorn)"
    echo -e "🔧 Service: ${BLUE}$APP_NAME${NC}"
    echo ""
    echo "📋 Management Commands:"
    echo "  sudo systemctl start $APP_NAME     # Start service"
    echo "  sudo systemctl stop $APP_NAME      # Stop service"  
    echo "  sudo systemctl restart $APP_NAME   # Restart service"
    echo "  systemctl status $APP_NAME         # Check status"
    echo "  journalctl -u $APP_NAME -f         # View logs"
    echo ""
    echo "🔗 API Endpoints:"
    echo "  http://localhost:$PORT/             # Root endpoint"
    echo "  http://localhost:$PORT/health       # Health check"
    echo "  http://localhost:$PORT/docs         # API documentation"
    echo ""
    echo "📊 Service Manager:"
    echo "  ./service_manager.sh status         # Check status"
    echo "  ./service_manager.sh test           # Test API"
    echo "  ./service_manager.sh logs           # View logs"
    echo ""
}

# Main deployment function
main() {
    echo -e "${BLUE}🚀 Starting Tanya Mail API Production Deployment${NC}"
    echo "=================================================="
    echo ""
    
    # Run all checks and setup
    check_directory
    check_venv
    check_dependencies
    test_configuration
    create_directories
    stop_existing_processes
    
    log_info "Starting service with clustering..."
    
    # Start the service using our run script
    nohup ./run_gunicorn.sh > /dev/null 2>&1 &
    
    # Test the deployment
    test_api_health
    
    # Show summary
    show_summary
    
    log_success "🎉 Production deployment completed successfully!"
    echo ""
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    test)
        test_api_health
        ;;
    stop)
        stop_existing_processes
        ;;
    help|--help|-h)
        echo "Usage: $0 [deploy|test|stop|help]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full production deployment (default)"
        echo "  test    - Test API health"
        echo "  stop    - Stop existing processes"
        echo "  help    - Show this help"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
