# Windows Workstation Setup Guide

This guide covers setting up the Windows workstation (DESKTOP-LIBOQV5) for fast local inference and IDE integration.

## Hardware Overview

- **CPU**: Intel Core i5-8400 (6C/6T @ 2.8-4.0GHz)
- **RAM**: 16 GB DDR4-2666
- **GPU**: AMD Radeon RX 550 (4GB GDDR5)
- **Storage**: 512GB NVMe + 2TB HDD
- **IP**: 192.168.86.38

## Quick Start

```powershell
# Run as Administrator
# 1. Install Chocolatey package manager
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 2. Install required tools
choco install git python312 nodejs-lts cmake -y

# 3. Clone the repository
git clone https://github.com/yourusername/autonomous-dev-agency.git
cd autonomous-dev-agency
```

## Option 1: llama.cpp with Vulkan (Recommended)

The RX 550 supports Vulkan, which llama.cpp can use for GPU-accelerated inference.

### Install Vulkan SDK

1. Download Vulkan SDK from https://vulkan.lunarg.com/sdk/home#windows
2. Run the installer
3. Restart your terminal

### Build llama.cpp with Vulkan

```powershell
# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# Create build directory
mkdir build
cd build

# Configure with Vulkan support
cmake .. -DGGML_VULKAN=ON

# Build
cmake --build . --config Release

# Verify Vulkan is detected
.\bin\Release\llama-cli.exe --version
```

### Download Models

For 4GB VRAM, use small quantized models:

```powershell
# Create models directory
mkdir D:\models

# Download Qwen2.5 1.5B (recommended for fast responses)
# From: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
# Download: qwen2.5-1.5b-instruct-q4_k_m.gguf (~1.1GB)

# Alternative: Phi-3 Mini
# From: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
# Download: Phi-3-mini-4k-instruct-q4.gguf (~2.2GB)
```

### Run llama.cpp Server

```powershell
# Start the server
cd llama.cpp\build\bin\Release

.\llama-server.exe `
    --model D:\models\qwen2.5-1.5b-instruct-q4_k_m.gguf `
    --host 0.0.0.0 `
    --port 8080 `
    --ctx-size 4096 `
    --n-gpu-layers 99 `
    --threads 4

# Test the server
curl http://localhost:8080/health
```

### Create Windows Service (Optional)

To run llama.cpp as a background service:

```powershell
# Install NSSM (Non-Sucking Service Manager)
choco install nssm -y

# Create service
nssm install llamacpp "C:\path\to\llama-server.exe"
nssm set llamacpp AppParameters "--model D:\models\qwen2.5-1.5b-instruct-q4_k_m.gguf --host 0.0.0.0 --port 8080 --ctx-size 4096 --n-gpu-layers 99"
nssm set llamacpp AppDirectory "C:\path\to\llama.cpp"
nssm start llamacpp
```

## Option 2: Ollama (Simpler Setup)

Ollama provides an easier setup but may not utilize the GPU as efficiently.

```powershell
# Install Ollama
winget install Ollama.Ollama

# Pull a small model
ollama pull qwen2.5:1.5b

# Test
ollama run qwen2.5:1.5b "Hello, how are you?"
```

**Note**: Ollama on Windows may default to CPU. Check GPU utilization in Task Manager.

## IDE Integration

### Google Antigravity / Trae.ai

These IDEs support MCP (Model Context Protocol) servers for extending capabilities.

#### MCP Server Configuration

Create `~/.config/antigravity/mcp.json` (or equivalent for your IDE):

```json
{
  "servers": {
    "local-llm": {
      "command": "node",
      "args": ["C:/path/to/mcp-servers/ollama-mcp/index.js"],
      "env": {
        "OLLAMA_HOST": "http://localhost:8080",
        "REMOTE_OLLAMA_HOST": "http://192.168.86.56:11434"
      }
    },
    "voice-pipeline": {
      "command": "node", 
      "args": ["C:/path/to/mcp-servers/voice-mcp/index.js"],
      "env": {
        "STT_URL": "http://192.168.86.56:8000",
        "TTS_URL": "http://192.168.86.56:8880"
      }
    },
    "agent-memory": {
      "command": "node",
      "args": ["C:/path/to/mcp-servers/memory-mcp/index.js"],
      "env": {
        "CHROMA_HOST": "192.168.86.56",
        "CHROMA_PORT": "8001"
      }
    }
  }
}
```

### VS Code (Alternative)

If using VS Code with Continue extension:

```json
// .continue/config.json
{
  "models": [
    {
      "title": "Local Qwen (Fast)",
      "provider": "ollama",
      "model": "qwen2.5:1.5b",
      "apiBase": "http://localhost:8080"
    },
    {
      "title": "Remote Qwen (Smart)",
      "provider": "ollama", 
      "model": "qwen2.5:7b",
      "apiBase": "http://192.168.86.56:11434"
    }
  ]
}
```

## Network Configuration

### Firewall Rules

Allow incoming connections for the llama.cpp server:

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "llama.cpp Server" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

### Test Connectivity

```powershell
# Test connection to AI server
Test-NetConnection -ComputerName 192.168.86.56 -Port 11434
Test-NetConnection -ComputerName 192.168.86.56 -Port 8000
Test-NetConnection -ComputerName 192.168.86.56 -Port 8880

# Test connection to East server
Test-NetConnection -ComputerName 192.168.86.51 -Port 6379
```

## Performance Tuning

### RX 550 Optimization

The RX 550 has limited VRAM (4GB), so optimization is crucial:

1. **Use small models**: Stick to 1.5B-3B parameter models
2. **Use Q4 quantization**: Reduces memory by ~4x
3. **Limit context**: Keep context window at 4096 or less
4. **Close other GPU apps**: Browsers, games, etc. consume VRAM

### Monitor GPU Usage

```powershell
# Install GPU-Z or use Task Manager
# Check for Vulkan utilization, not just GPU %
```

### Expected Performance

| Model | VRAM | Tokens/sec | First Token |
|-------|------|------------|-------------|
| qwen2.5-1.5b-q4 | ~1.5 GB | 25-35 | 200-400ms |
| phi-3-mini-q4 | ~2.5 GB | 15-25 | 300-500ms |

## Troubleshooting

### Vulkan Not Detected

```powershell
# Check Vulkan installation
vulkaninfo

# If not found, reinstall Vulkan SDK
```

### Out of VRAM

```
error: Vulkan memory allocation failed
```

Solutions:
- Close other applications
- Use smaller model
- Reduce context size (`--ctx-size 2048`)
- Use more aggressive quantization (Q3 instead of Q4)

### Slow Performance

If getting <10 tok/s:
1. Verify GPU layers are being used (`--n-gpu-layers 99`)
2. Check Task Manager for GPU utilization
3. Ensure Vulkan is being used, not CPU fallback

### Connection Refused to AI Server

```powershell
# Check if Tailscale is connected
tailscale status

# Verify direct LAN connectivity
ping 192.168.86.56
```

## Quick Reference

```
Windows Workstation: 192.168.86.38
Local LLM API: http://localhost:8080
AI Server Ollama: http://192.168.86.56:11434
AI Server STT: http://192.168.86.56:8000
AI Server TTS: http://192.168.86.56:8880
Voice Assistant UI: http://192.168.86.56:7860
```

## Next Steps

1. ✅ Install llama.cpp with Vulkan
2. ✅ Download and test models
3. ⬜ Set up MCP servers
4. ⬜ Configure IDE integration
5. ⬜ Test end-to-end voice pipeline
