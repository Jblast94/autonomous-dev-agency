/**
 * MCP Server for Ollama LLM Integration
 * 
 * Provides tools for interacting with local and remote Ollama instances,
 * with intelligent routing between fast (local GPU) and smart (remote CPU) models.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

// Configuration from environment
const LOCAL_OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://localhost:8080';
const REMOTE_OLLAMA_HOST = process.env.REMOTE_OLLAMA_HOST || 'http://192.168.86.56:11434';
const DEFAULT_LOCAL_MODEL = process.env.LOCAL_MODEL || 'qwen2.5:1.5b';
const DEFAULT_REMOTE_MODEL = process.env.REMOTE_MODEL || 'qwen2.5:7b';

/**
 * Ollama API client
 */
class OllamaClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async chat(model, messages, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        messages,
        stream: false,
        ...options,
      }),
    });

    if (!response.ok) {
      throw new Error(`Ollama error: ${response.status} ${await response.text()}`);
    }

    const data = await response.json();
    return data.message?.content || '';
  }

  async generate(model, prompt, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        prompt,
        stream: false,
        ...options,
      }),
    });

    if (!response.ok) {
      throw new Error(`Ollama error: ${response.status} ${await response.text()}`);
    }

    const data = await response.json();
    return data.response || '';
  }

  async listModels() {
    const response = await fetch(`${this.baseUrl}/api/tags`);
    if (!response.ok) {
      throw new Error(`Ollama error: ${response.status}`);
    }
    const data = await response.json();
    return data.models || [];
  }

  async isAvailable() {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`, {
        signal: AbortSignal.timeout(5000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Initialize clients
const localClient = new OllamaClient(LOCAL_OLLAMA_HOST);
const remoteClient = new OllamaClient(REMOTE_OLLAMA_HOST);

/**
 * Determine which client to use based on task complexity
 */
function estimateComplexity(prompt) {
  const wordCount = prompt.split(/\s+/).length;
  const hasCodeRequest = /code|implement|function|class|debug|fix/i.test(prompt);
  const hasAnalysisRequest = /analyze|explain|compare|evaluate/i.test(prompt);
  const hasSimpleRequest = /hello|hi|thanks|yes|no|ok/i.test(prompt);

  if (hasSimpleRequest && wordCount < 20) return 'simple';
  if (hasCodeRequest || hasAnalysisRequest || wordCount > 100) return 'complex';
  return 'medium';
}

/**
 * Create the MCP server
 */
const server = new Server(
  {
    name: 'ollama-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'chat',
        description: 'Chat with an LLM. Automatically routes to fast local model for simple queries or smart remote model for complex tasks.',
        inputSchema: {
          type: 'object',
          properties: {
            message: {
              type: 'string',
              description: 'The message to send to the LLM',
            },
            system: {
              type: 'string',
              description: 'Optional system prompt',
            },
            model: {
              type: 'string',
              description: 'Specific model to use (overrides auto-routing)',
            },
            prefer: {
              type: 'string',
              enum: ['fast', 'smart', 'auto'],
              description: 'Routing preference: fast (local), smart (remote), or auto',
            },
          },
          required: ['message'],
        },
      },
      {
        name: 'generate',
        description: 'Generate text completion from a prompt',
        inputSchema: {
          type: 'object',
          properties: {
            prompt: {
              type: 'string',
              description: 'The prompt for text generation',
            },
            model: {
              type: 'string',
              description: 'Model to use',
            },
            max_tokens: {
              type: 'number',
              description: 'Maximum tokens to generate',
            },
          },
          required: ['prompt'],
        },
      },
      {
        name: 'list_models',
        description: 'List available models on local and remote Ollama instances',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'health_check',
        description: 'Check the health of local and remote Ollama instances',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'chat': {
        const { message, system, model, prefer = 'auto' } = args;
        
        // Determine routing
        let client, modelToUse;
        
        if (model) {
          // Explicit model specified
          const localAvailable = await localClient.isAvailable();
          client = localAvailable ? localClient : remoteClient;
          modelToUse = model;
        } else if (prefer === 'fast') {
          client = localClient;
          modelToUse = DEFAULT_LOCAL_MODEL;
        } else if (prefer === 'smart') {
          client = remoteClient;
          modelToUse = DEFAULT_REMOTE_MODEL;
        } else {
          // Auto-routing based on complexity
          const complexity = estimateComplexity(message);
          
          if (complexity === 'simple' && await localClient.isAvailable()) {
            client = localClient;
            modelToUse = DEFAULT_LOCAL_MODEL;
          } else {
            client = remoteClient;
            modelToUse = complexity === 'complex' ? DEFAULT_REMOTE_MODEL : DEFAULT_LOCAL_MODEL;
          }
        }

        // Build messages
        const messages = [];
        if (system) {
          messages.push({ role: 'system', content: system });
        }
        messages.push({ role: 'user', content: message });

        // Make request
        const response = await client.chat(modelToUse, messages);
        
        return {
          content: [
            {
              type: 'text',
              text: response,
            },
          ],
          metadata: {
            model: modelToUse,
            endpoint: client.baseUrl,
          },
        };
      }

      case 'generate': {
        const { prompt, model, max_tokens } = args;
        const modelToUse = model || DEFAULT_REMOTE_MODEL;
        
        const response = await remoteClient.generate(modelToUse, prompt, {
          num_predict: max_tokens,
        });
        
        return {
          content: [{ type: 'text', text: response }],
        };
      }

      case 'list_models': {
        const results = { local: [], remote: [] };
        
        try {
          results.local = await localClient.listModels();
        } catch (e) {
          results.local = [{ error: e.message }];
        }
        
        try {
          results.remote = await remoteClient.listModels();
        } catch (e) {
          results.remote = [{ error: e.message }];
        }
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'health_check': {
        const health = {
          local: {
            url: LOCAL_OLLAMA_HOST,
            available: await localClient.isAvailable(),
          },
          remote: {
            url: REMOTE_OLLAMA_HOST,
            available: await remoteClient.isAvailable(),
          },
        };
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(health, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Ollama MCP server running');
}

main().catch(console.error);
