#!/bin/bash
# Setup script for East Server (192.168.86.51)
# Run as: ./setup-east-server.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  East Server Setup Script${NC}"
echo -e "${GREEN}  Hostname: linux-home (192.168.86.51)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please do not run as root. Run as regular user with sudo access.${NC}"
    exit 1
fi

# =============================================================================
# STEP 0: CRITICAL - Free Disk Space
# =============================================================================
echo -e "${RED}Step 0: CRITICAL - Checking disk space...${NC}"

ROOT_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
ROOT_FREE=$(df -h / | awk 'NR==2 {print $4}')

echo "Root partition usage: ${ROOT_USAGE}%"
echo "Root partition free: ${ROOT_FREE}"

if [ "$ROOT_USAGE" -gt 90 ]; then
    echo -e "${RED}WARNING: Root partition is ${ROOT_USAGE}% full!${NC}"
    echo "Attempting to free space..."
    
    # Clean apt cache
    sudo apt clean
    sudo apt autoremove -y
    
    # Clean old journal logs
    sudo journalctl --vacuum-time=3d
    
    # Clean old kernels (keep current + 1 previous)
    sudo apt purge $(dpkg -l 'linux-*' | sed '/^ii/!d;/'"$(uname -r | sed "s/\(.*\)-\([^0-9]\+\)/\1/")"'/d;s/^[^ ]* [^ ]* \([^ ]*\).*/\1/;/[0-9]/!d' | head -n -1) 2>/dev/null || true
    
    # If Docker is installed, clean it
    if command -v docker &> /dev/null; then
        echo "Cleaning Docker..."
        docker system prune -af --volumes 2>/dev/null || true
    fi
    
    # Show result
    NEW_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    NEW_FREE=$(df -h / | awk 'NR==2 {print $4}')
    echo -e "${GREEN}After cleanup: ${NEW_USAGE}% used, ${NEW_FREE} free${NC}"
    
    if [ "$NEW_USAGE" -gt 95 ]; then
        echo -e "${RED}Still critically low on space. Please manually free space before continuing.${NC}"
        echo "Consider moving large directories to /data partition:"
        echo "  sudo du -sh /var/* | sort -hr | head -10"
        exit 1
    fi
fi

# =============================================================================
# STEP 1: System Updates
# =============================================================================
echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# =============================================================================
# STEP 2: Install Docker
# =============================================================================
echo -e "${YELLOW}Step 2: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker installed. You may need to log out and back in for group changes.${NC}"
else
    echo -e "${GREEN}Docker already installed.${NC}"
fi

# Install Docker Compose plugin
if ! docker compose version &> /dev/null; then
    sudo apt install -y docker-compose-plugin
fi

# =============================================================================
# STEP 3: Setup Project Directory
# =============================================================================
echo -e "${YELLOW}Step 3: Setting up project directory...${NC}"

PROJECT_DIR="$HOME/autonomous-dev-agency"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Create subdirectories
mkdir -p deploy/nginx-east/conf.d
mkdir -p logs

# =============================================================================
# STEP 4: Create Nginx Config
# =============================================================================
echo -e "${YELLOW}Step 4: Creating Nginx configuration...${NC}"

cat > deploy/nginx-east/nginx.conf << 'EOF'
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    keepalive_timeout 65;

    # Upstream definitions for AI server services
    upstream ai_voice {
        server 192.168.86.56:7860;
    }

    upstream ai_ollama {
        server 192.168.86.56:11434;
    }

    upstream ai_stt {
        server 192.168.86.56:8000;
    }

    upstream ai_tts {
        server 192.168.86.56:8880;
    }

    server {
        listen 80;
        server_name _;

        # Health check endpoint
        location /health {
            return 200 'OK';
            add_header Content-Type text/plain;
        }

        # Proxy to Voice Assistant
        location /voice/ {
            proxy_pass http://ai_voice/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Proxy to Ollama API
        location /api/ollama/ {
            proxy_pass http://ai_ollama/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Netdata monitoring
        location /netdata/ {
            proxy_pass http://localhost:19999/;
            proxy_set_header Host $host;
        }
    }
}
EOF

echo -e "${GREEN}Nginx configuration created.${NC}"

# =============================================================================
# STEP 5: System resource check
# =============================================================================
echo -e "${YELLOW}Step 5: Checking system resources...${NC}"

echo "CPU: $(nproc) cores"
echo "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Disk (root): $(df -h / | awk 'NR==2 {print $4}') free"
echo "Disk (/data): $(df -h /data 2>/dev/null | awk 'NR==2 {print $4}' || echo 'Not mounted')"

# =============================================================================
# STEP 6: Start Services
# =============================================================================
echo -e "${YELLOW}Step 6: Starting services...${NC}"

cd "$PROJECT_DIR/deploy"

# Check if docker-compose.east.yml exists
if [ -f "docker-compose.east.yml" ]; then
    docker compose -f docker-compose.east.yml up -d
    echo -e "${GREEN}Services started.${NC}"
else
    echo -e "${YELLOW}docker-compose.east.yml not found. Copy it from the repository first.${NC}"
fi

# =============================================================================
# STEP 7: Final instructions
# =============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services running on this server:"
echo "  - Redis: localhost:6379"
echo "  - Netdata: http://192.168.86.51:19999"
echo "  - Nginx Proxy: http://192.168.86.51:80"
echo ""
echo "To check status:"
echo "  docker compose -f docker-compose.east.yml ps"
echo "  docker compose -f docker-compose.east.yml logs -f"
echo ""
echo -e "${YELLOW}Note: You may need to log out and back in for Docker group permissions.${NC}"
