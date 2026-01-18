# Infrastructure Plan

## Overview

This document details the complete infrastructure plan for the Autonomous Multi-Agent Software Development Agency, based on the actual hardware resources available.

## Hardware Inventory

### Server 1: AI Server (Primary)

| Property | Value |
|----------|-------|
| **Hostname** | `ai` |
| **IP Address** | 192.168.86.56 |
| **Hardware** | Dell Precision Tower 5810 |
| **OS** | Ubuntu 24.04.3 LTS |
| **CPU** | Intel Xeon E5-1650 v3 (6C/12T @ 3.5GHz) |
| **RAM** | 32 GB DDR4 |
| **Storage** | 477GB SSD (boot) + 2x 932GB HDD (unmounted) |
| **GPU** | NVIDIA NVS 310 (512MB - display only) |
| **Network** | 1 Gbps Ethernet |

**Role**: Heavy LLM inference (CPU), STT/TTS services, databases, Docker orchestration

**Resource Allocation**:
| Component | RAM | Notes |
|-----------|-----|-------|
| Ollama | 8-12 GB | Qwen2.5 7B model |
| Faster-Whisper | 2 GB | tiny.en model |
| Kokoro TTS | 2 GB | |
| PostgreSQL | 2 GB | Agent state, chat history |
| ChromaDB | 2-4 GB | Vector memory |
| Voice Assistant | 2 GB | Gradio app |
| System/Buffer | 4-6 GB | |
| **Total** | ~24-30 GB | Within 32GB limit |

### Server 2: Windows Workstation

| Property | Value |
|----------|-------|
| **Hostname** | `DESKTOP-LIBOQV5` |
| **IP Address** | 192.168.86.38 |
| **Hardware** | Dell OptiPlex 3070 |
| **OS** | Windows 11 Pro |
| **CPU** | Intel Core i5-8400 (6C/6T @ 2.8-4.0GHz) |
| **RAM** | 16 GB DDR4-2666 |
| **Storage** | 512GB NVMe + 2TB HDD + 3TB USB |
| **GPU** | **AMD Radeon RX 550 (4GB GDDR5)** + Intel UHD 630 |
| **Network** | 1 Gbps Ethernet + Tailscale VPN |

**Role**: Primary development workstation, fast small-model inference via Vulkan/llama.cpp

**Key Capability**: The RX 550 with 4GB VRAM can run quantized models up to ~3B parameters via llama.cpp with Vulkan backend. This enables fast (<500ms) responses for simple queries.

**Resource Allocation**:
| Component | RAM/VRAM | Notes |
|-----------|----------|-------|
| IDE (Antigravity/Trae) | 4 GB RAM | Development environment |
| llama.cpp | 1.5-2 GB VRAM | Qwen2.5 1.5B model |
| Browser | 4 GB RAM | |
| System | 5 GB RAM | |
| **Total** | ~13-15 GB RAM | Near capacity |

### Server 3: East Server (Supporting)

| Property | Value |
|----------|-------|
| **Hostname** | `linux-home` |
| **IP Address** | 192.168.86.51 |
| **Hardware** | Dell OptiPlex 3050 |
| **OS** | Ubuntu 24.04.3 LTS |
| **CPU** | Intel Core i5-7500 (4C/4T @ 3.4GHz) |
| **RAM** | 16 GB DDR4 |
| **Storage** | 1.8TB HDD + 13GB Optane (swap) |
| **GPU** | AMD Radeon R5 430 (2GB - display only) |
| **Network** | 1 Gbps Ethernet + Tailscale VPN |

**Role**: Supporting services (Redis, monitoring), n8n workflows

**⚠️ CRITICAL**: Root partition at 97% capacity - requires immediate cleanup!

**Resource Allocation**:
| Component | RAM | Notes |
|-----------|-----|-------|
| Redis | 1-2 GB | Message queue |
| n8n | 2-3 GB | Existing workflows |
| Netdata | 512 MB | Monitoring |
| Nginx | 256 MB | Reverse proxy |
| System | 4 GB | |
| **Total** | ~8-10 GB | Well within limit |

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          LAN: 192.168.86.0/24                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│   │   AI Server     │    │    Windows      │    │   East Server   │   │
│   │  192.168.86.56  │    │  192.168.86.38  │    │  192.168.86.51  │   │
│   │                 │    │                 │    │                 │   │
│   │  Ports:         │    │  Ports:         │    │  Ports:         │   │
│   │  - 11434 Ollama │    │  - 22 SSH       │    │  - 6379 Redis   │   │
│   │  - 8000 STT     │    │  - 3389 RDP     │    │  - 19999 Netdata│   │
│   │  - 8880 TTS     │    │  - 8080 llama   │    │  - 80 Nginx     │   │
│   │  - 5432 Postgres│    │                 │    │                 │   │
│   │  - 8001 Chroma  │    │                 │    │                 │   │
│   │  - 7860 Voice   │    │                 │    │                 │   │
│   └────────┬────────┘    └────────┬────────┘    └────────┬────────┘   │
│            │                      │                      │             │
│            └──────────────────────┼──────────────────────┘             │
│                                   │                                     │
│                          ┌────────▼────────┐                           │
│                          │  Router/Gateway │                           │
│                          │  192.168.86.1   │                           │
│                          └────────┬────────┘                           │
│                                   │                                     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │
                           ┌────────▼────────┐
                           │    Tailscale    │
                           │   Mesh VPN      │
                           └─────────────────┘
```

## Service Architecture

### Voice Pipeline

```
User speaks
     │
     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Microphone  │────►│ Faster-      │────►│  LLM Router  │────►│ Kokoro TTS   │
│  (Windows)   │     │ Whisper      │     │              │     │              │
└──────────────┘     │ (AI Server)  │     │              │     │ (AI Server)  │
                     └──────────────┘     └──────┬───────┘     └──────────────┘
                                                 │                      │
                          ┌──────────────────────┼──────────────────────┘
                          │                      │
                          ▼                      ▼
                   ┌─────────────┐        ┌─────────────┐
                   │ Quick Path  │        │ Complex Path│
                   │ RX 550 GPU  │        │ Ollama CPU  │
                   │ ~200-400ms  │        │ ~3-8 sec    │
                   │ (Windows)   │        │ (AI Server) │
                   └─────────────┘        └─────────────┘
```

### Model Deployment

| Location | Model | Size | Use Case | Latency |
|----------|-------|------|----------|---------|
| Windows (llama.cpp) | qwen2.5-1.5b-q4_k_m | 1.5 GB VRAM | Quick responses, routing | 200-400ms |
| AI Server (Ollama) | qwen2.5:3b | 3 GB RAM | Medium complexity | 2-4 sec |
| AI Server (Ollama) | qwen2.5:7b | 6 GB RAM | Complex reasoning | 5-10 sec |
| AI Server (Ollama) | nomic-embed-text | 500 MB RAM | Embeddings | 100ms |
| External (API) | Claude API | - | Very complex tasks | 1-2 sec |

### Database Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Server (192.168.86.56)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌───────────────────┐       ┌───────────────────┐        │
│   │    PostgreSQL     │       │     ChromaDB      │        │
│   │    Port: 5432     │       │    Port: 8001     │        │
│   │                   │       │                   │        │
│   │  Tables:          │       │  Collections:     │        │
│   │  - chat_history   │       │  - conversations  │        │
│   │  - agent_state    │       │  - codebase       │        │
│   │  - tasks          │       │  - documentation  │        │
│   │  - metrics        │       │                   │        │
│   └───────────────────┘       └───────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Inter-service messaging
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   East Server (192.168.86.51)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌───────────────────┐                                    │
│   │      Redis        │                                    │
│   │    Port: 6379     │                                    │
│   │                   │                                    │
│   │  Channels:        │                                    │
│   │  - agent_tasks    │                                    │
│   │  - agent_results  │                                    │
│   │  - notifications  │                                    │
│   └───────────────────┘                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Phases

### Phase 1: Foundation (Week 1)

**Goals**: Get voice assistant operational with basic functionality

**Tasks**:
1. ☐ Clean disk space on East server (CRITICAL)
2. ☐ Install Docker on AI server
3. ☐ Mount HDD drives on AI server
4. ☐ Deploy Docker Compose stack on AI server
5. ☐ Pull Ollama models
6. ☐ Test STT → LLM → TTS pipeline
7. ☐ Deploy Redis on East server

**Success Criteria**:
- Voice assistant responds to spoken queries
- End-to-end latency <10s for simple queries
- All services healthy and monitored

### Phase 2: Integration (Week 2-3)

**Goals**: Connect Windows workstation for fast inference and IDE integration

**Tasks**:
1. ☐ Set up llama.cpp with Vulkan on Windows
2. ☐ Create LLM routing logic (fast vs complex)
3. ☐ Build MCP server for Ollama
4. ☐ Build MCP server for voice pipeline
5. ☐ Integrate with Antigravity IDE
6. ☐ Implement conversation memory

**Success Criteria**:
- Quick responses (<1.5s) via Windows GPU
- MCP servers functional in IDE
- Persistent conversation history

### Phase 3: Agent Framework (Week 4-6)

**Goals**: Implement multi-agent capabilities

**Tasks**:
1. ☐ Define agent roles and permissions
2. ☐ Implement PRP workflow
3. ☐ Create agent orchestrator
4. ☐ Add guardrails and escalation
5. ☐ Implement producer-critic loop
6. ☐ Build evaluation harness

**Success Criteria**:
- Agents can complete simple development tasks
- Human escalation works correctly
- Metrics dashboard operational

### Phase 4: Optimization (Month 2+)

**Goals**: Improve performance and add GPU

**Tasks**:
1. ☐ Profile and optimize bottlenecks
2. ☐ Consider GPU upgrade (RTX 3060 12GB)
3. ☐ Implement memory consolidation
4. ☐ Add more specialized agents
5. ☐ Integrate with external tools (GitHub, etc.)

## Resource Monitoring

### Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Voice response latency (simple) | <3s | >5s |
| Voice response latency (complex) | <10s | >15s |
| STT accuracy | >95% | <90% |
| Ollama memory usage | <12GB | >14GB |
| AI Server CPU usage | <70% avg | >85% sustained |
| East Server disk usage | <80% | >90% |
| Redis memory | <1GB | >1.5GB |

### Monitoring Endpoints

- **Netdata**: http://192.168.86.51:19999
- **Ollama Status**: http://192.168.86.56:11434/api/tags
- **Voice Assistant Health**: http://192.168.86.56:7860/health
- **PostgreSQL**: Connect via `psql -h 192.168.86.56 -U agent -d agent_memory`

## Backup Strategy

### What to Backup

| Data | Location | Frequency | Method |
|------|----------|-----------|--------|
| PostgreSQL | AI Server | Daily | pg_dump to /data/backups |
| ChromaDB | AI Server | Daily | Volume snapshot |
| Conversation history | PostgreSQL | Daily | Included in pg_dump |
| Agent configurations | Git repo | On change | Git push |
| PRPs | Git repo | On change | Git push |

### Backup Script

```bash
#!/bin/bash
# Run daily via cron: 0 2 * * * /home/user/backup.sh

BACKUP_DIR="/data/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# PostgreSQL
docker exec agent-postgres pg_dump -U agent agent_memory > "$BACKUP_DIR/postgres.sql"

# ChromaDB (stop container briefly)
docker stop chromadb
tar -czf "$BACKUP_DIR/chromadb.tar.gz" /var/lib/docker/volumes/deploy_chroma_data
docker start chromadb

# Cleanup old backups (keep 7 days)
find /data/backups -type d -mtime +7 -exec rm -rf {} +
```

## Security Considerations

1. **Network Isolation**: All services on internal LAN only
2. **External Access**: Via Tailscale VPN only
3. **Secrets Management**: Use `.env` files (not committed to git)
4. **Database Auth**: Strong passwords, no default credentials
5. **Container Security**: Run as non-root where possible
6. **Updates**: Regular security updates via `apt upgrade`

## Troubleshooting

### Common Issues

**Ollama out of memory**:
```bash
# Check memory usage
docker stats
# Reduce model size or kill other processes
ollama rm qwen2.5:7b
ollama pull qwen2.5:3b
```

**STT not responding**:
```bash
# Check container logs
docker logs faster-whisper
# Restart container
docker compose restart faster-whisper
```

**East server disk full**:
```bash
# Emergency cleanup
sudo apt clean
docker system prune -af
sudo journalctl --vacuum-size=100M
```

**Voice latency too high**:
- Check network connectivity between servers
- Verify Ollama isn't swapping to disk
- Consider routing simple queries to Windows GPU

## Future Upgrades

### Recommended Hardware Upgrades

| Upgrade | Cost (Est.) | Benefit |
|---------|-------------|---------|
| RTX 3060 12GB for AI Server | $250-300 | 5-10x faster inference |
| RAM upgrade (32GB → 64GB) | $80-100 | Run larger models |
| NVMe for AI Server HDDs | $100-150 | Faster model loading |

### GPU Upgrade Path

With an RTX 3060 12GB on the AI Server:
- Can run Qwen2.5:14B or Llama3:8B at 30-50 tok/s
- Voice latency drops to <2s for all queries
- Enables local image generation capabilities
