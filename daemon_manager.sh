#!/bin/bash

# Tanya Mail API Daemon Manager
# Alternative to systemd for containers/environments without systemd

set -e

# Configuration
APP_NAME="tanya-mail-api"
# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"
PID_FILE="/tmp/${APP_NAME}.pid"
LOG_FILE="$APP_DIR/logs/daemon.log"

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

# Check if daemon is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is dead, remove it
            rm -f "$PID_FILE"
            return 1
        fi
    else
        return 1
    fi
}

# Get daemon PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# Start daemon
start_daemon() {
    log_info "Starting Tanya Mail API daemon..."
    
    if is_running; then
        log_warning "Daemon is already running (PID: $(get_pid))"
        return 0
    fi
    
    # Change to app directory
    cd "$APP_DIR"
    
    # Ensure log directory exists
    mkdir -p logs
    
    # Start the application in background
    nohup bash -c "
        source .venv/bin/activate
        exec gunicorn api:app -c gunicorn_config.py >> '$LOG_FILE' 2>&1
    " &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment and check if it's still running
    sleep 2
    
    if is_running; then
        log_success "✅ Daemon started successfully (PID: $pid)"
        log_info "Logs are being written to: $LOG_FILE"
        
        # Test API after a moment
        sleep 3
        test_api
    else
        log_error "❌ Failed to start daemon"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Stop daemon
stop_daemon() {
    log_info "Stopping Tanya Mail API daemon..."
    
    if ! is_running; then
        log_warning "Daemon is not running"
        return 0
    fi
    
    local pid=$(get_pid)
    
    # Try graceful shutdown first
    kill -TERM "$pid" 2>/dev/null
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && is_running; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if is_running; then
        log_warning "Graceful shutdown failed, force killing..."
        kill -KILL "$pid" 2>/dev/null
        sleep 1
    fi
    
    if ! is_running; then
        log_success "✅ Daemon stopped successfully"
        rm -f "$PID_FILE"
    else
        log_error "❌ Failed to stop daemon"
        return 1
    fi
}

# Restart daemon
restart_daemon() {
    log_info "Restarting Tanya Mail API daemon..."
    stop_daemon
    sleep 2
    start_daemon
}

# Show daemon status
show_status() {
    echo -e "${BLUE}📊 Daemon Status${NC}"
    echo "================"
    echo ""
    
    if is_running; then
        local pid=$(get_pid)
        echo -e "Status: ${GREEN}✅ Running${NC}"
        echo -e "PID: ${BLUE}$pid${NC}"
        
        # Get process info
        local cpu_mem=$(ps -o %cpu,%mem -p "$pid" --no-headers 2>/dev/null || echo "N/A N/A")
        echo -e "CPU/Memory: ${BLUE}$cpu_mem${NC}"
        
        # Get worker count
        local workers=$(pgrep -f "gunicorn.*api:app" | wc -l)
        echo -e "Workers: ${BLUE}$workers${NC}"
        
    else
        echo -e "Status: ${RED}❌ Stopped${NC}"
    fi
    
    echo -e "PID File: ${BLUE}$PID_FILE${NC}"
    echo -e "Log File: ${BLUE}$LOG_FILE${NC}"
    echo ""
    
    # Test API
    test_api
}

# Test API
test_api() {
    log_info "Testing API health..."
    
    # Get port from .env in app directory
    local port=$(grep "^PORT=" "$APP_DIR/.env" | cut -d'=' -f2 2>/dev/null || echo "8804")
    
    local response=$(curl -s -w "\n%{http_code}" "http://localhost:$port/health" -H "Content-Type: application/json" 2>/dev/null || echo -e "\nERROR")
    local http_code=$(echo "$response" | tail -n1)
    local content=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        log_success "✅ API is healthy (Port: $port)"
        echo -e "${GREEN}Response:${NC} $content"
    else
        log_error "❌ API test failed (Port: $port)"
        if [ "$http_code" != "ERROR" ] && [ ! -z "$content" ]; then
            echo -e "${RED}HTTP Code:${NC} $http_code"
            echo -e "${RED}Response:${NC} $content"
        fi
    fi
}

# Show logs
show_logs() {
    local lines=${1:-50}
    
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}📋 Recent Logs (last $lines lines)${NC}"
        echo "================================="
        echo ""
        tail -n "$lines" "$LOG_FILE"
    else
        log_warning "Log file not found: $LOG_FILE"
    fi
}

# Follow logs
follow_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}📋 Following Logs (Ctrl+C to exit)${NC}"
        echo "================================="
        echo ""
        tail -f "$LOG_FILE"
    else
        log_warning "Log file not found: $LOG_FILE"
    fi
}

# Show help
show_help() {
    echo -e "${BLUE}Tanya Mail API Daemon Manager${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the daemon"
    echo "  stop      - Stop the daemon"
    echo "  restart   - Restart the daemon"
    echo "  status    - Show daemon status"
    echo "  test      - Test API health"
    echo "  logs [N]  - Show last N log lines (default: 50)"
    echo "  follow    - Follow logs in real-time"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start            # Start daemon"
    echo "  $0 status           # Check status"
    echo "  $0 logs 100         # Show last 100 lines"
    echo "  $0 follow           # Follow logs"
    echo ""
    echo "Files:"
    echo "  PID: $PID_FILE"
    echo "  Log: $LOG_FILE"
    echo ""
}

# Main command handling
case "${1:-help}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        show_status
        ;;
    test)
        test_api
        ;;
    logs)
        show_logs "${2:-50}"
        ;;
    follow)
        follow_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
