#!/bin/bash
# Health Check Script for Autonomous Dev Agency
# Run from any machine on the network

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
AI_SERVER="192.168.86.56"
EAST_SERVER="192.168.86.51"
WINDOWS_HOST="192.168.86.38"

echo "=========================================="
echo "  Autonomous Dev Agency Health Check"
echo "  $(date)"
echo "=========================================="
echo ""

# Function to check HTTP endpoint
check_http() {
    local name=$1
    local url=$2
    local timeout=${3:-5}
    
    if curl -sf --connect-timeout "$timeout" "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name (${url})"
        return 1
    fi
}

# Function to check TCP port
check_port() {
    local name=$1
    local host=$2
    local port=$3
    local timeout=${4:-3}
    
    if timeout "$timeout" bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $name ($host:$port)"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name ($host:$port)"
        return 1
    fi
}

# Track overall status
FAILED=0

# ===========================================================================
# AI Server Checks
# ===========================================================================
echo -e "${YELLOW}AI Server ($AI_SERVER)${NC}"

check_port "SSH" "$AI_SERVER" 22 || ((FAILED++))
check_http "Ollama API" "http://$AI_SERVER:11434/api/tags" || ((FAILED++))
check_http "Faster-Whisper STT" "http://$AI_SERVER:8000/health" 10 || ((FAILED++))
check_http "Kokoro TTS" "http://$AI_SERVER:8880/health" 10 || ((FAILED++))
check_port "PostgreSQL" "$AI_SERVER" 5432 || ((FAILED++))
check_http "ChromaDB" "http://$AI_SERVER:8001/api/v1/heartbeat" || ((FAILED++))
check_http "Voice Assistant" "http://$AI_SERVER:7860" 10 || ((FAILED++))

echo ""

# ===========================================================================
# East Server Checks
# ===========================================================================
echo -e "${YELLOW}East Server ($EAST_SERVER)${NC}"

check_port "SSH" "$EAST_SERVER" 22 || ((FAILED++))
check_port "Redis" "$EAST_SERVER" 6379 || ((FAILED++))
check_http "Netdata" "http://$EAST_SERVER:19999/api/v1/info" || ((FAILED++))
check_http "Nginx" "http://$EAST_SERVER/health" || ((FAILED++))

echo ""

# ===========================================================================
# Windows Workstation Checks (Optional)
# ===========================================================================
echo -e "${YELLOW}Windows Workstation ($WINDOWS_HOST)${NC}"

check_port "SSH" "$WINDOWS_HOST" 22 || echo -e "  ${YELLOW}⚠${NC} SSH (may be disabled)"
check_port "RDP" "$WINDOWS_HOST" 3389 || ((FAILED++))
check_http "llama.cpp (if running)" "http://$WINDOWS_HOST:8080/health" 3 || echo -e "  ${YELLOW}⚠${NC} llama.cpp not running"

echo ""

# ===========================================================================
# Summary
# ===========================================================================
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All critical services healthy!${NC}"
else
    echo -e "${RED}$FAILED service(s) failed health check${NC}"
fi
echo "=========================================="

# Additional diagnostics if there are failures
if [ $FAILED -gt 0 ]; then
    echo ""
    echo "Troubleshooting tips:"
    echo "  - Check Docker containers: docker ps"
    echo "  - Check logs: docker compose logs <service>"
    echo "  - Check network: ping <host>"
    echo "  - Check firewall: sudo ufw status"
fi

exit $FAILED
