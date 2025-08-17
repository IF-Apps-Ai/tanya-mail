#!/bin/bash

# Tanya Mail API Monitoring and Maintenance Script

# Configuration
APP_NAME="tanya-mail-api"
LOG_FILE="/var/log/tanya-mail-monitor.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get port from .env
get_port() {
    if [ -f ".env" ]; then
        PORT=$(grep "^PORT=" .env | cut -d'=' -f2 2>/dev/null || echo "8804")
    else
        PORT=8804
    fi
    echo $PORT
}

# Log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE" 2>/dev/null || echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if API is healthy
check_health() {
    local port=$(get_port)
    local response=$(curl -s -w "\n%{http_code}" "http://localhost:$port/health" -H "Content-Type: application/json" 2>/dev/null)
    local http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# Get service status
get_service_status() {
    if systemctl is-active --quiet $APP_NAME 2>/dev/null; then
        echo "active"
    else
        echo "inactive"
    fi
}

# Get process count
get_process_count() {
    local count=$(pgrep -f "gunicorn.*api:app" | wc -l)
    echo $count
}

# Get memory usage
get_memory_usage() {
    local memory=$(ps -o pid,rss,cmd -C python | grep "gunicorn.*api:app" | awk '{sum+=$2} END {printf "%.1f", sum/1024}')
    echo "${memory:-0.0}"
}

# Show system resources
show_resources() {
    echo -e "${BLUE}=== System Resources ===${NC}"
    echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')"
    echo "Memory Usage: $(free -h | awk 'NR==2{printf "%.1f%% (%s/%s)", $3*100/$2, $3, $2}')"
    echo "Disk Usage: $(df -h . | awk 'NR==2{printf "%s (%s)", $5, $4}')"
    echo ""
}

# Monitor function
monitor() {
    local port=$(get_port)
    
    echo -e "${BLUE}🔍 Tanya Mail API Monitor${NC}"
    echo "================================"
    echo ""
    
    while true; do
        clear
        echo -e "${BLUE}🔍 Tanya Mail API Monitor - $(date)${NC}"
        echo "========================================"
        echo ""
        
        # Service status
        local service_status=$(get_service_status)
        local process_count=$(get_process_count)
        local memory_usage=$(get_memory_usage)
        
        echo -e "${BLUE}=== Service Status ===${NC}"
        if [ "$service_status" = "active" ]; then
            echo -e "Service: ${GREEN}✅ Running${NC}"
        else
            echo -e "Service: ${RED}❌ Stopped${NC}"
        fi
        
        echo -e "Processes: ${BLUE}$process_count${NC}"
        echo -e "Memory: ${BLUE}${memory_usage} MB${NC}"
        echo -e "Port: ${BLUE}$port${NC}"
        echo ""
        
        # Health check
        echo -e "${BLUE}=== Health Check ===${NC}"
        if check_health; then
            echo -e "API Health: ${GREEN}✅ Healthy${NC}"
            local health_data=$(curl -s "http://localhost:$port/health" 2>/dev/null)
            echo -e "Response: ${GREEN}$health_data${NC}"
        else
            echo -e "API Health: ${RED}❌ Unhealthy${NC}"
        fi
        echo ""
        
        # System resources
        show_resources
        
        # Recent logs
        echo -e "${BLUE}=== Recent Logs (last 5 lines) ===${NC}"
        if systemctl is-active --quiet $APP_NAME 2>/dev/null; then
            journalctl -u $APP_NAME --no-pager -l -n 5 --since "5 minutes ago" 2>/dev/null | tail -5
        else
            echo "Service not running - no logs available"
        fi
        echo ""
        
        echo -e "${YELLOW}Press Ctrl+C to exit monitoring${NC}"
        sleep 10
    done
}

# Performance test
performance_test() {
    local port=$(get_port)
    echo -e "${BLUE}🚀 Performance Test${NC}"
    echo "===================="
    echo ""
    
    echo "Testing API endpoint performance..."
    echo "Endpoint: http://localhost:$port/health"
    echo ""
    
    # Simple performance test with curl
    echo "Running 10 concurrent requests..."
    
    for i in {1..10}; do
        {
            start_time=$(date +%s.%N)
            response=$(curl -s -w "%{http_code}" "http://localhost:$port/health")
            end_time=$(date +%s.%N)
            duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "N/A")
            echo "Request $i: HTTP $response - ${duration}s"
        } &
    done
    
    wait
    echo ""
    echo "✅ Performance test completed"
}

# Restart service
restart_service() {
    echo -e "${YELLOW}🔄 Restarting Tanya Mail API...${NC}"
    
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}This command requires sudo privileges${NC}"
        echo "Please run: sudo $0 restart"
        exit 1
    fi
    
    systemctl restart $APP_NAME
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service restarted successfully${NC}"
        sleep 3
        
        # Check if it's healthy
        if check_health; then
            echo -e "${GREEN}✅ Service is healthy after restart${NC}"
        else
            echo -e "${RED}❌ Service appears unhealthy after restart${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to restart service${NC}"
        exit 1
    fi
}

# Show logs
show_logs() {
    local lines=${1:-50}
    echo -e "${BLUE}📋 Recent Logs (last $lines lines)${NC}"
    echo "================================="
    echo ""
    
    if systemctl is-active --quiet $APP_NAME 2>/dev/null; then
        journalctl -u $APP_NAME --no-pager -l -n "$lines"
    else
        echo "Service is not running"
    fi
}

# Show help
show_help() {
    echo -e "${BLUE}Tanya Mail API Monitor & Maintenance${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  monitor    - Start real-time monitoring dashboard"
    echo "  status     - Show current status"
    echo "  health     - Check API health"
    echo "  restart    - Restart the service (requires sudo)"
    echo "  logs [N]   - Show last N log lines (default: 50)"
    echo "  perf       - Run performance test"
    echo "  resources  - Show system resources"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 monitor           # Start monitoring"
    echo "  $0 status            # Quick status check"
    echo "  $0 logs 100          # Show last 100 log lines"
    echo "  sudo $0 restart      # Restart service"
    echo ""
}

# Status summary
status_summary() {
    local port=$(get_port)
    local service_status=$(get_service_status)
    local process_count=$(get_process_count)
    local memory_usage=$(get_memory_usage)
    
    echo -e "${BLUE}📊 Tanya Mail API Status${NC}"
    echo "========================"
    echo ""
    
    # Service info
    if [ "$service_status" = "active" ]; then
        echo -e "🟢 Service: ${GREEN}Running${NC}"
    else
        echo -e "🔴 Service: ${RED}Stopped${NC}"
    fi
    
    echo -e "📡 Port: ${BLUE}$port${NC}"
    echo -e "👥 Workers: ${BLUE}$process_count${NC}"
    echo -e "💾 Memory: ${BLUE}${memory_usage} MB${NC}"
    echo ""
    
    # Health check
    if check_health; then
        echo -e "✅ API Health: ${GREEN}Healthy${NC}"
    else
        echo -e "❌ API Health: ${RED}Unhealthy${NC}"
    fi
    
    echo ""
    show_resources
}

# Main command handling
case "${1:-status}" in
    monitor|mon)
        monitor
        ;;
    status)
        status_summary
        ;;
    health)
        local port=$(get_port)
        if check_health; then
            echo -e "${GREEN}✅ API is healthy${NC}"
            curl -s "http://localhost:$port/health" | jq . 2>/dev/null || curl -s "http://localhost:$port/health"
        else
            echo -e "${RED}❌ API is unhealthy${NC}"
        fi
        ;;
    restart)
        restart_service
        ;;
    logs)
        show_logs "${2:-50}"
        ;;
    perf|performance)
        performance_test
        ;;
    resources|res)
        show_resources
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
