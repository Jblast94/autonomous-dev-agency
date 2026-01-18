"""
Voice Assistant Application
Gradio-based voice interface with STT/LLM/TTS pipeline
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Tuple, Generator
import uuid

import gradio as gr
import numpy as np
import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

class Config:
    """Application configuration from environment variables."""
    
    # Service URLs
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    STT_URL = os.getenv("STT_URL", "http://localhost:8000")
    TTS_URL = os.getenv("TTS_URL", "http://localhost:8880")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://agent:changeme@localhost/agent_memory")
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))
    
    # Voice settings
    TTS_VOICE = os.getenv("TTS_VOICE", "af_bella")
    TTS_SPEED = float(os.getenv("TTS_SPEED", "1.0"))
    
    # Session
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))

config = Config()

# =============================================================================
# STT Client
# =============================================================================

class STTClient:
    """Client for Faster-Whisper speech-to-text service."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio to text."""
        try:
            # Convert numpy array to bytes
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
            # Send to Whisper API
            files = {
                "file": ("audio.wav", audio_bytes, "audio/wav")
            }
            response = await self.client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                files=files,
                data={"model": "whisper-1"}
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("text", "").strip()
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""
    
    async def health_check(self) -> bool:
        """Check if STT service is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False

# =============================================================================
# TTS Client
# =============================================================================

class TTSClient:
    """Client for Kokoro text-to-speech service."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = "af_bella",
        speed: float = 1.0
    ) -> Optional[bytes]:
        """Synthesize text to speech."""
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/audio/speech",
                json={
                    "input": text,
                    "voice": voice,
                    "speed": speed,
                    "response_format": "wav"
                }
            )
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if TTS service is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False

# =============================================================================
# LLM Client
# =============================================================================

class LLMClient:
    """Client for Ollama LLM service."""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def chat(
        self, 
        messages: list[dict],
        stream: bool = False
    ) -> str:
        """Send chat request to LLM."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": stream
                }
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "I'm sorry, I encountered an error processing your request."
    
    async def chat_stream(
        self, 
        messages: list[dict]
    ) -> Generator[str, None, None]:
        """Stream chat response from LLM."""
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                            
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield "I'm sorry, I encountered an error."
    
    async def health_check(self) -> bool:
        """Check if LLM service is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False

# =============================================================================
# Conversation Manager
# =============================================================================

class ConversationManager:
    """Manages conversation history and context."""
    
    def __init__(self):
        self.conversations: dict[str, list[dict]] = {}
        self.system_prompt = """You are a helpful AI assistant integrated into a multi-agent software development framework. You can help with:

- Answering questions about software development
- Discussing architecture and design decisions
- Helping debug code issues
- Planning development tasks
- General knowledge questions

Be concise but helpful. For voice interactions, keep responses natural and conversational.
If you don't know something, say so rather than making things up."""
    
    def get_session(self, session_id: str) -> list[dict]:
        """Get or create conversation session."""
        if session_id not in self.conversations:
            self.conversations[session_id] = [
                {"role": "system", "content": self.system_prompt}
            ]
        return self.conversations[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to conversation history."""
        session = self.get_session(session_id)
        session.append({"role": role, "content": content})
        
        # Keep last 20 messages (plus system prompt)
        if len(session) > 21:
            self.conversations[session_id] = [session[0]] + session[-20:]
    
    def clear_session(self, session_id: str):
        """Clear conversation history for session."""
        if session_id in self.conversations:
            del self.conversations[session_id]

# =============================================================================
# Voice Assistant
# =============================================================================

class VoiceAssistant:
    """Main voice assistant orchestrating STT, LLM, and TTS."""
    
    def __init__(self):
        self.stt = STTClient(config.STT_URL)
        self.tts = TTSClient(config.TTS_URL)
        self.llm = LLMClient(config.OLLAMA_HOST, config.OLLAMA_MODEL)
        self.conversations = ConversationManager()
    
    async def process_audio(
        self, 
        audio: Tuple[int, np.ndarray],
        session_id: str
    ) -> Tuple[str, str, Optional[bytes]]:
        """
        Process audio input through the full pipeline.
        
        Returns: (transcription, response_text, audio_response)
        """
        if audio is None:
            return "", "No audio received.", None
        
        sample_rate, audio_data = audio
        
        # Normalize audio
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / 32768.0
        
        # Step 1: Speech to Text
        logger.info("Processing STT...")
        transcription = await self.stt.transcribe(audio_data, sample_rate)
        
        if not transcription:
            return "", "I couldn't understand that. Could you please try again?", None
        
        logger.info(f"Transcription: {transcription}")
        
        # Step 2: Add to conversation and get LLM response
        self.conversations.add_message(session_id, "user", transcription)
        messages = self.conversations.get_session(session_id)
        
        logger.info("Processing LLM...")
        response_text = await self.llm.chat(messages)
        
        self.conversations.add_message(session_id, "assistant", response_text)
        logger.info(f"Response: {response_text[:100]}...")
        
        # Step 3: Text to Speech
        logger.info("Processing TTS...")
        audio_response = await self.tts.synthesize(
            response_text,
            voice=config.TTS_VOICE,
            speed=config.TTS_SPEED
        )
        
        return transcription, response_text, audio_response
    
    async def process_text(
        self, 
        text: str,
        session_id: str
    ) -> Tuple[str, Optional[bytes]]:
        """
        Process text input (for typing instead of voice).
        
        Returns: (response_text, audio_response)
        """
        if not text.strip():
            return "Please enter a message.", None
        
        # Add to conversation and get LLM response
        self.conversations.add_message(session_id, "user", text)
        messages = self.conversations.get_session(session_id)
        
        logger.info("Processing LLM...")
        response_text = await self.llm.chat(messages)
        
        self.conversations.add_message(session_id, "assistant", response_text)
        
        # Generate audio response
        audio_response = await self.tts.synthesize(
            response_text,
            voice=config.TTS_VOICE,
            speed=config.TTS_SPEED
        )
        
        return response_text, audio_response
    
    async def health_check(self) -> dict:
        """Check health of all services."""
        return {
            "stt": await self.stt.health_check(),
            "tts": await self.tts.health_check(),
            "llm": await self.llm.health_check()
        }

# =============================================================================
# Gradio Interface
# =============================================================================

def create_interface():
    """Create the Gradio web interface."""
    
    assistant = VoiceAssistant()
    
    def generate_session_id():
        return str(uuid.uuid4())
    
    async def handle_audio(audio, session_id, history):
        """Handle audio input from microphone."""
        if session_id is None:
            session_id = generate_session_id()
        
        transcription, response, audio_out = await assistant.process_audio(audio, session_id)
        
        # Update chat history
        if transcription:
            history = history or []
            history.append({"role": "user", "content": transcription})
            history.append({"role": "assistant", "content": response})
        
        return history, audio_out, session_id, ""
    
    async def handle_text(text, session_id, history):
        """Handle text input from textbox."""
        if session_id is None:
            session_id = generate_session_id()
        
        response, audio_out = await assistant.process_text(text, session_id)
        
        # Update chat history
        history = history or []
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": response})
        
        return history, audio_out, session_id, ""
    
    def clear_conversation(session_id):
        """Clear the current conversation."""
        if session_id:
            assistant.conversations.clear_session(session_id)
        return [], generate_session_id()
    
    async def check_health():
        """Check service health status."""
        health = await assistant.health_check()
        status_lines = []
        for service, healthy in health.items():
            icon = "✅" if healthy else "❌"
            status_lines.append(f"{icon} {service.upper()}")
        return "\n".join(status_lines)
    
    # Build the interface
    with gr.Blocks(
        title="Voice Assistant",
        theme=gr.themes.Soft()
    ) as interface:
        
        gr.Markdown("# 🎤 Voice Assistant")
        gr.Markdown("Talk or type to interact with your AI development assistant.")
        
        # Hidden state
        session_id = gr.State(generate_session_id)
        
        with gr.Row():
            with gr.Column(scale=2):
                # Chat display
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=400,
                    type="messages"
                )
                
                # Text input
                with gr.Row():
                    text_input = gr.Textbox(
                        label="Type a message",
                        placeholder="Type here or use the microphone...",
                        scale=4
                    )
                    send_btn = gr.Button("Send", scale=1)
                
                # Audio input
                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="numpy",
                    label="Or speak here"
                )
            
            with gr.Column(scale=1):
                # Audio output
                audio_output = gr.Audio(
                    label="Response Audio",
                    type="filepath",
                    autoplay=True
                )
                
                # Controls
                clear_btn = gr.Button("🗑️ Clear Conversation")
                health_btn = gr.Button("🏥 Check Services")
                health_status = gr.Textbox(
                    label="Service Status",
                    lines=3,
                    interactive=False
                )
        
        # Event handlers
        send_btn.click(
            handle_text,
            inputs=[text_input, session_id, chatbot],
            outputs=[chatbot, audio_output, session_id, text_input]
        )
        
        text_input.submit(
            handle_text,
            inputs=[text_input, session_id, chatbot],
            outputs=[chatbot, audio_output, session_id, text_input]
        )
        
        audio_input.stop_recording(
            handle_audio,
            inputs=[audio_input, session_id, chatbot],
            outputs=[chatbot, audio_output, session_id, text_input]
        )
        
        clear_btn.click(
            clear_conversation,
            inputs=[session_id],
            outputs=[chatbot, session_id]
        )
        
        health_btn.click(
            check_health,
            outputs=[health_status]
        )
    
    return interface

# =============================================================================
# Health endpoint for Docker
# =============================================================================

def health_endpoint():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    logger.info("Starting Voice Assistant...")
    logger.info(f"STT URL: {config.STT_URL}")
    logger.info(f"TTS URL: {config.TTS_URL}")
    logger.info(f"LLM URL: {config.OLLAMA_HOST}")
    logger.info(f"LLM Model: {config.OLLAMA_MODEL}")
    
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
