#!/bin/bash

# Tanya Ma'il API Test Script
# This script tests the API endpoints

echo "🚀 Testing Tanya Ma'il API..."

BASE_URL="http://localhost:8000"

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

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=$4
    
    print_status "INFO" "Testing $method $endpoint - $description"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X $method "$BASE_URL$endpoint")
    http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        print_status "SUCCESS" "HTTP $http_code - $description"
        if [ ! -z "$body" ] && [ "$body" != "null" ]; then
            echo "   Response: $(echo $body | jq -r '.message // .status // .' 2>/dev/null || echo $body | head -c 100)"
        fi
    else
        print_status "ERROR" "HTTP $http_code (expected $expected_status) - $description"
        echo "   Response: $body"
    fi
    echo
}

# Function to test JSON POST endpoint
test_json_post() {
    local endpoint=$1
    local json_data=$2
    local description=$3
    local expected_status=$4
    
    print_status "INFO" "Testing POST $endpoint - $description"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$json_data" \
        "$BASE_URL$endpoint")
    
    http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        print_status "SUCCESS" "HTTP $http_code - $description"
        if [ ! -z "$body" ] && [ "$body" != "null" ]; then
            echo "   Response: $(echo $body | jq -r '.message // .answer // .' 2>/dev/null | head -c 150)..."
        fi
    else
        print_status "ERROR" "HTTP $http_code (expected $expected_status) - $description"
        echo "   Response: $body"
    fi
    echo
}

# Wait for API to be ready
print_status "INFO" "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        print_status "SUCCESS" "API is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_status "ERROR" "API is not responding after 30 attempts"
        exit 1
    fi
    sleep 1
done

echo
echo "==================== API TESTS ===================="
echo

# Test basic endpoints
test_endpoint "GET" "/" "Root endpoint" 200
test_endpoint "GET" "/health" "Health check" 200
test_endpoint "GET" "/files" "List files" 200

# Test conversation endpoints
test_endpoint "GET" "/conversation/history" "Get conversation history" 200
test_endpoint "DELETE" "/conversation/history" "Clear conversation history" 200

# Test configuration
test_json_post "/conversation/config" '{"context_window": 3}' "Configure conversation context" 200

# Test search (might return empty if no documents)
test_endpoint "GET" "/search?query=test&top_k=3" "Search documents" 200

# Test vector store build (might fail if no documents)
test_endpoint "POST" "/build-vectorstore" "Build vector store" 200

# Test question asking (will likely fail without documents)
test_json_post "/ask" '{"question": "What is this document about?", "top_k": 3}' "Ask question" 200

echo
echo "==================== SUMMARY ===================="
print_status "INFO" "API testing completed"
print_status "INFO" "Check individual test results above"
print_status "INFO" "For full testing, upload PDF files first using:"
echo "   curl -X POST \"$BASE_URL/upload\" -H \"Content-Type: multipart/form-data\" -F \"file=@document.pdf\""

echo
print_status "INFO" "API Documentation available at:"
echo "   Swagger UI: $BASE_URL/docs"
echo "   ReDoc: $BASE_URL/redoc"
