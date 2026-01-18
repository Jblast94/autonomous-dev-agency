# Autonomous Multi-Agent Software Development Agency

A self-hosted AI-native development framework optimized for voice-first interaction and local LLM inference. Built for a hybrid infrastructure of Ubuntu servers and Windows workstations.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WINDOWS WORKSTATION (192.168.86.38)              │
│                    Primary Development + Fast Inference             │
├─────────────────────────────────────────────────────────────────────┤
│  • Google Antigravity IDE / Trae.ai IDE                            │
│  • llama.cpp + Vulkan (RX 550 4GB) for fast small-model inference  │
│  • Voice input capture (microphone)                                 │
│  • MCP servers bridging to infrastructure                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ API calls over LAN
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI SERVER (192.168.86.56)                        │
│                    Heavy Lifting + State Management                 │
├─────────────────────────────────────────────────────────────────────┤
│  • Ollama (CPU) - larger models (7B-13B) for complex reasoning     │
│  • Faster-Whisper STT service                                       │
│  • Kokoro TTS service                                               │
│  • PostgreSQL - chat history, agent state                          │
│  • ChromaDB - vector memory                                         │
│  • Docker orchestration                                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Message queue
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EAST SERVER (192.168.86.51)                      │
│                    Supporting Services                              │
├─────────────────────────────────────────────────────────────────────┤
│  • Redis - inter-agent message queue                               │
│  • n8n - workflow automation                                        │
│  • Nginx reverse proxy                                              │
│  • Monitoring (Netdata)                                             │
└─────────────────────────────────────────────────────────────────────┘
```

## 📋 Infrastructure Summary

| Server | Hostname | IP | Role | CPU | RAM | GPU |
|--------|----------|-----|------|-----|-----|-----|
| **Primary AI** | `ai` | 192.168.86.56 | LLM + Orchestration | Xeon E5-1650 v3 (6C/12T) | 32 GB | Display only |
| **Windows Dev** | `DESKTOP-LIBOQV5` | 192.168.86.38 | Development + Fast Inference | i5-8400 (6C/6T) | 16 GB | **RX 550 4GB** |
| **East Server** | `linux-home` | 192.168.86.51 | Supporting Services | i5-7500 (4C/4T) | 16 GB | Display only |

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose on AI server
- Ollama installed on AI server
- llama.cpp with Vulkan support on Windows (optional, for fast inference)
- Tailscale for secure mesh networking (recommended)

### 1. Clone and Configure

```bash
git clone https://github.com/yourusername/autonomous-dev-agency.git
cd autonomous-dev-agency

# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

### 2. Deploy AI Server Stack

```bash
# SSH to AI server
ssh ai@192.168.86.56

# Deploy core services
cd autonomous-dev-agency/deploy
./setup-ai-server.sh
```

### 3. Deploy Supporting Services (East Server)

```bash
# SSH to East server
ssh linux-home@192.168.86.51

# Deploy Redis and monitoring
cd autonomous-dev-agency/deploy
./setup-east-server.sh
```

### 4. Configure Windows Workstation

See [docs/windows-setup.md](docs/windows-setup.md) for llama.cpp and MCP server configuration.

## 📁 Repository Structure

```
autonomous-dev-agency/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
├── .claude/
│   ├── commands/                     # Reusable Claude Code commands
│   │   ├── generate-prp.md
│   │   ├── execute-prp.md
│   │   ├── review-and-evolve.md
│   │   └── security-audit.md
│   ├── agents/                       # Specialized agent definitions
│   │   ├── backend-developer.md
│   │   ├── frontend-developer.md
│   │   ├── test-specialist.md
│   │   └── security-reviewer.md
│   └── settings.local.json
├── deploy/
│   ├── docker-compose.yml            # Main stack for AI server
│   ├── docker-compose.east.yml       # East server services
│   ├── setup-ai-server.sh
│   ├── setup-east-server.sh
│   └── setup-windows.ps1
├── voice-assistant/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                        # Gradio-based voice UI
│   ├── stt_client.py
│   ├── tts_client.py
│   ├── llm_router.py
│   └── memory_manager.py
├── mcp-servers/
│   ├── ollama-mcp/                   # MCP server for Ollama
│   ├── voice-mcp/                    # MCP server for voice pipeline
│   └── memory-mcp/                   # MCP server for agent memory
├── agents/
│   ├── config/
│   │   ├── agents.yaml
│   │   ├── tasks.yaml
│   │   └── guardrails.yaml
│   ├── orchestrator.py
│   ├── planning_agent.py
│   └── tools/
│       ├── claude_code_tool.py
│       └── escalation_tool.py
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md
│   └── active/
├── memory/
│   ├── checkpoints/
│   ├── episodic/
│   └── semantic/
├── docs/
│   ├── architecture.md
│   ├── infrastructure-plan.md
│   ├── windows-setup.md
│   ├── voice-pipeline.md
│   └── mcp-integration.md
├── scripts/
│   ├── health-check.sh
│   ├── backup-memory.sh
│   └── model-management.sh
├── .env.example
├── CLAUDE.md                         # Global Claude Code rules
├── AGENTS.md                         # Root agent instructions
└── README.md
```

## 🎤 Voice Pipeline

The voice assistant provides natural voice interaction with your development environment:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Microphone   │───►│ Faster-      │───►│ LLM Router   │───►│ Kokoro TTS   │
│ (Windows)    │    │ Whisper      │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                         │                     │                    │
                         ▼                     ▼                    ▼
                    ~300-500ms          Quick: ~200ms         ~500ms-1s
                                       Complex: ~3-8s
```

### Latency Targets

| Response Type | Target | Path |
|--------------|--------|------|
| Quick acknowledgment | <1.5s | Windows GPU (Qwen 1.5B) |
| Simple query | <3s | AI Server CPU (Qwen 3B) |
| Complex reasoning | <10s | AI Server CPU (Qwen 7B) or Claude API |

## 🤖 Agent Roles

The framework defines specialized agent roles that can be combined or split based on team size:

| Role | Primary Function | Tool Access |
|------|------------------|-------------|
| **Orchestrator** | Task coordination | Subagent management |
| **Senior Developer** | Complex implementation | Full filesystem, git |
| **Test Specialist** | Test strategy, automation | Test frameworks |
| **Security Reviewer** | Vulnerability analysis | SAST tools, read-only |
| **Documentation Writer** | Technical docs | Markdown tools |

See [docs/architecture.md](docs/architecture.md) for full role definitions.

## 📊 Monitoring

Health checks and metrics are available at:

- **Netdata**: http://192.168.86.51:19999 (East server)
- **Ollama Status**: http://192.168.86.56:11434/api/tags
- **Voice Pipeline Health**: http://192.168.86.56:7860/health

## 🔧 Configuration

### Environment Variables

```bash
# AI Server
OLLAMA_HOST=http://localhost:11434
POSTGRES_PASSWORD=your-secure-password
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Voice Pipeline
STT_URL=http://localhost:8000
TTS_URL=http://localhost:8880
WHISPER_MODEL=tiny.en

# Claude API (optional, for complex tasks)
ANTHROPIC_API_KEY=your-api-key
```

### Model Configuration

| Component | Model | Location | VRAM/RAM |
|-----------|-------|----------|----------|
| Fast inference | qwen2.5-1.5b-q4_k_m | Windows (llama.cpp) | 1.5 GB VRAM |
| STT | faster-whisper-tiny | AI Server | 2 GB RAM |
| Complex LLM | qwen2.5:7b | AI Server (Ollama) | 6 GB RAM |
| TTS | kokoro-82m | AI Server | 2 GB RAM |
| Embeddings | nomic-embed-text | AI Server (Ollama) | 500 MB RAM |

## 📈 Scaling Path

| Phase | Timeline | Changes |
|-------|----------|---------|
| **Current** | Now | CPU-only inference, voice assistant operational |
| **Phase 2** | Month 1-2 | Add GPU to AI server (RTX 3060 12GB recommended) |
| **Phase 3** | Month 3+ | Dedicated inference server or cloud hybrid |

## 🛡️ Guardrails

The framework implements four-layer guardrails to prevent runaway agent behavior:

1. **Input Guardrails**: Task boundary validation, injection detection
2. **Action Guardrails**: RBAC, rate limits, autonomy thresholds
3. **Output Guardrails**: PII scanning, confidence scoring
4. **Operational Guardrails**: Circuit breakers, token budgets, time-boxing

## 📚 Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Infrastructure Plan](docs/infrastructure-plan.md)
- [Windows Setup Guide](docs/windows-setup.md)
- [Voice Pipeline Details](docs/voice-pipeline.md)
- [MCP Integration](docs/mcp-integration.md)

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome via issues.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.
