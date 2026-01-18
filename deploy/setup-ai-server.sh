#!/bin/bash
# Setup script for AI Server (192.168.86.56)
# Run as: ./setup-ai-server.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AI Server Setup Script${NC}"
echo -e "${GREEN}  Hostname: ai (192.168.86.56)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please do not run as root. Run as regular user with sudo access.${NC}"
    exit 1
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
# STEP 3: Mount Data Drives
# =============================================================================
echo -e "${YELLOW}Step 3: Configuring data drives...${NC}"

# Check if drives exist
if [ -b /dev/sdb ] && [ -b /dev/sdc ]; then
    # Create mount points
    sudo mkdir -p /data/models /data/projects
    
    # Check if already mounted
    if ! mountpoint -q /data/models; then
        echo "Checking /dev/sdb partition structure..."
        if ! sudo blkid /dev/sdb1 &> /dev/null; then
            echo -e "${YELLOW}No partition found on /dev/sdb. Creating...${NC}"
            # This is interactive - consider automating if needed
            echo "Run: sudo fdisk /dev/sdb to create partition, then mkfs.ext4 /dev/sdb1"
        else
            echo "Mounting /dev/sdb1 to /data/models..."
            sudo mount /dev/sdb1 /data/models || echo "Mount failed - check partition"
        fi
    fi
    
    if ! mountpoint -q /data/projects; then
        if ! sudo blkid /dev/sdc1 &> /dev/null; then
            echo -e "${YELLOW}No partition found on /dev/sdc. Creating...${NC}"
            echo "Run: sudo fdisk /dev/sdc to create partition, then mkfs.ext4 /dev/sdc1"
        else
            echo "Mounting /dev/sdc1 to /data/projects..."
            sudo mount /dev/sdc1 /data/projects || echo "Mount failed - check partition"
        fi
    fi
else
    echo -e "${YELLOW}Data drives /dev/sdb and/or /dev/sdc not found. Skipping mount.${NC}"
fi

# =============================================================================
# STEP 4: Install/Configure Ollama
# =============================================================================
echo -e "${YELLOW}Step 4: Configuring Ollama...${NC}"

if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo -e "${GREEN}Ollama already installed.${NC}"
fi

# Pull recommended models
echo "Pulling recommended models (this may take a while)..."
ollama pull qwen2.5:1.5b || echo "Failed to pull qwen2.5:1.5b"
ollama pull qwen2.5:3b || echo "Failed to pull qwen2.5:3b"
ollama pull nomic-embed-text || echo "Failed to pull nomic-embed-text"

# =============================================================================
# STEP 5: Setup Project Directory
# =============================================================================
echo -e "${YELLOW}Step 5: Setting up project directory...${NC}"

PROJECT_DIR="$HOME/autonomous-dev-agency"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Creating project directory at $PROJECT_DIR..."
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Create necessary subdirectories
mkdir -p deploy/init-scripts/postgres
mkdir -p deploy/nginx/conf.d
mkdir -p voice-assistant
mkdir -p memory/{checkpoints,episodic,semantic}
mkdir -p PRPs/{templates,active}
mkdir -p logs

# =============================================================================
# STEP 6: Create .env file if not exists
# =============================================================================
echo -e "${YELLOW}Step 6: Checking environment configuration...${NC}"

if [ ! -f "deploy/.env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example deploy/.env
        echo -e "${YELLOW}Created deploy/.env from template. Please edit with your values.${NC}"
        echo "Run: nano deploy/.env"
    else
        echo -e "${RED}.env.example not found. Please create deploy/.env manually.${NC}"
    fi
else
    echo -e "${GREEN}deploy/.env already exists.${NC}"
fi

# =============================================================================
# STEP 7: Create PostgreSQL init script
# =============================================================================
echo -e "${YELLOW}Step 7: Creating database init scripts...${NC}"

cat > deploy/init-scripts/postgres/01-init.sql << 'EOF'
-- Initialize agent memory database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_history_session ON chat_history(session_id);
CREATE INDEX idx_chat_history_created ON chat_history(created_at);

-- Agent state table
CREATE TABLE IF NOT EXISTS agent_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    state_key VARCHAR(200) NOT NULL,
    state_value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_name, state_key)
);

CREATE INDEX idx_agent_state_name ON agent_state(agent_name);

-- Task tracking table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    prp_reference VARCHAR(500),
    assigned_agent VARCHAR(100),
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    confidence_score DECIMAL(3,2),
    token_usage INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_agent ON tasks(assigned_agent);

-- Metrics table for monitoring
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL NOT NULL,
    labels JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_metrics_name ON metrics(metric_name);
CREATE INDEX idx_metrics_time ON metrics(recorded_at);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agent;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agent;
EOF

echo -e "${GREEN}Database init script created.${NC}"

# =============================================================================
# STEP 8: System resource check
# =============================================================================
echo -e "${YELLOW}Step 8: Checking system resources...${NC}"

echo "CPU: $(nproc) cores"
echo "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Disk (root): $(df -h / | awk 'NR==2 {print $4}') free"
echo "Disk (/data): $(df -h /data 2>/dev/null | awk 'NR==2 {print $4}' || echo 'Not mounted')"

# Check if Ollama is running
if systemctl is-active --quiet ollama; then
    echo -e "${GREEN}Ollama service: Running${NC}"
else
    echo -e "${YELLOW}Ollama service: Not running. Starting...${NC}"
    sudo systemctl start ollama
fi

# =============================================================================
# STEP 9: Final instructions
# =============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit deploy/.env with your configuration"
echo "2. Start the services:"
echo "   cd $PROJECT_DIR/deploy"
echo "   docker compose up -d"
echo ""
echo "3. Check service status:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo ""
echo "4. Access services:"
echo "   - Voice Assistant: http://192.168.86.56:7860"
echo "   - Ollama: http://192.168.86.56:11434"
echo "   - STT API: http://192.168.86.56:8000"
echo "   - TTS API: http://192.168.86.56:8880"
echo ""
echo -e "${YELLOW}Note: You may need to log out and back in for Docker group permissions.${NC}"
