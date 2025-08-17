#!/bin/bash

# Tanya Mail API Service Management Script
# Usage: ./service_manager.sh [install|start|stop|restart|status|logs|uninstall]

SERVICE_NAME="tanya-mail-api"
SERVICE_FILE="$SERVICE_NAME.service"
SYSTEMD_DIR="/etc/systemd/system"
CURRENT_DIR=$(pwd)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root for system operations
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This operation requires root privileges. Please run with sudo."
        exit 1
    fi
}

# Install service
install_service() {
    print_status "Installing Tanya Mail API Service..."
    
    # Get current directory and user
    local app_dir=$(pwd)
    local current_user=$(whoami)
    
    # Check if template exists
    if [ ! -f "${SERVICE_FILE}.template" ]; then
        print_error "Service template file '${SERVICE_FILE}.template' not found in current directory!"
        exit 1
    fi
    
    check_root
    
    # Generate service file from template
    print_info "Generating service file for current directory: $app_dir"
    sed -e "s|{{APP_DIR}}|$app_dir|g" \
        -e "s|{{USER}}|$current_user|g" \
        "${SERVICE_FILE}.template" > "$SERVICE_FILE"
    
    # Copy service file to systemd directory
    cp "$SERVICE_FILE" "$SYSTEMD_DIR/"
    
    # Set proper permissions
    chmod 644 "$SYSTEMD_DIR/$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service to start on boot
    systemctl enable "$SERVICE_NAME"
    
    print_status "Service installed and enabled successfully!"
    print_info "You can now use: sudo systemctl start $SERVICE_NAME"
}

# Start service
start_service() {
    print_status "Starting Tanya Mail API Service..."
    check_root
    systemctl start "$SERVICE_NAME"
    
    if [ $? -eq 0 ]; then
        print_status "Service started successfully!"
        sleep 2
        systemctl status "$SERVICE_NAME" --no-pager -l
    else
        print_error "Failed to start service!"
        exit 1
    fi
}

# Stop service
stop_service() {
    print_status "Stopping Tanya Mail API Service..."
    check_root
    systemctl stop "$SERVICE_NAME"
    
    if [ $? -eq 0 ]; then
        print_status "Service stopped successfully!"
    else
        print_error "Failed to stop service!"
        exit 1
    fi
}

# Restart service
restart_service() {
    print_status "Restarting Tanya Mail API Service..."
    check_root
    systemctl restart "$SERVICE_NAME"
    
    if [ $? -eq 0 ]; then
        print_status "Service restarted successfully!"
        sleep 2
        systemctl status "$SERVICE_NAME" --no-pager -l
    else
        print_error "Failed to restart service!"
        exit 1
    fi
}

# Check service status
check_status() {
    print_status "Checking Tanya Mail API Service status..."
    systemctl status "$SERVICE_NAME" --no-pager -l
    
    print_info "\n=== Recent logs ==="
    journalctl -u "$SERVICE_NAME" --no-pager -l -n 20
}

# View service logs
view_logs() {
    print_status "Viewing Tanya Mail API Service logs..."
    echo -e "${BLUE}Press Ctrl+C to exit log view${NC}"
    journalctl -u "$SERVICE_NAME" -f
}

# Uninstall service
uninstall_service() {
    print_warning "Uninstalling Tanya Mail API Service..."
    check_root
    
    # Stop service if running
    systemctl stop "$SERVICE_NAME" 2>/dev/null
    
    # Disable service
    systemctl disable "$SERVICE_NAME" 2>/dev/null
    
    # Remove service file
    rm -f "$SYSTEMD_DIR/$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Service uninstalled successfully!"
}

# Test API endpoint
test_api() {
    print_status "Testing API endpoint..."
    
    # Get port from .env file
    if [ -f ".env" ]; then
        PORT=$(grep "^PORT=" .env | cut -d'=' -f2)
        if [ -z "$PORT" ]; then
            PORT=8804
        fi
    else
        PORT=8804
    fi
    
    print_info "Testing health endpoint on port $PORT..."
    
    response=$(curl -s -w "\n%{http_code}" "http://localhost:$PORT/health" -H "Content-Type: application/json")
    http_code=$(echo "$response" | tail -n1)
    content=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        print_status "✅ API is healthy!"
        echo -e "${GREEN}Response:${NC} $content"
    else
        print_error "❌ API test failed! HTTP Code: $http_code"
        if [ ! -z "$content" ]; then
            echo -e "${RED}Response:${NC} $content"
        fi
    fi
}

# Show help
show_help() {
    echo -e "${BLUE}Tanya Mail API Service Manager${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  install   - Install service to systemd"
    echo "  start     - Start the service"
    echo "  stop      - Stop the service"  
    echo "  restart   - Restart the service"
    echo "  status    - Check service status and recent logs"
    echo "  logs      - View live service logs"
    echo "  test      - Test API endpoints"
    echo "  uninstall - Remove service from systemd"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo $0 install    # Install service"
    echo "  sudo $0 start      # Start service"
    echo "  $0 status          # Check status (no sudo needed)"
    echo "  $0 test            # Test API (no sudo needed)"
    echo ""
}

# Main logic
case "$1" in
    install)
        install_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    test)
        test_api
        ;;
    uninstall)
        uninstall_service
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
