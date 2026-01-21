## 2026-01-21 - Ollama MCP Availability Check Bottleneck
**Learning:** The Ollama MCP server performs a network health check (`isAvailable`) on every routing decision when auto-routing or explicit model selection is used. This adds significant latency (up to 5s on timeout) per request if the local instance is unstable or unreachable.
**Action:** Implement short-term caching (e.g., 10s) for availability checks in MCP servers to decouple routing logic from immediate network status.
