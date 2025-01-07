import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import yaml
import asyncio
from typing import Dict, Optional
from src.audio import AudioProcessor
from src.speech import SpeechRecognizer
from src.llm import LanguageModel
from src.voice import VoiceSynthesizer
from src.utils.config import Config
from src.utils.session import SessionManager
from src.utils.exceptions import *
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Voice Agent Platform",
    description="Real-time voice conversation platform with AI capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
except Exception as e:
    logger.error(f"Failed to load configuration: {str(e)}")
    raise ConfigurationError("Failed to load configuration file")

# Verify API keys
required_keys = {
    "RETELL_API_KEY": "Retell.ai",
    "OPENAI_API_KEY": "OpenAI",
    "DEEPGRAM_API_KEY": "Deepgram",
    "ELEVENLABS_API_KEY": "ElevenLabs"
}

for key, service in required_keys.items():
    if not os.getenv(key):
        raise APIKeyError(f"Missing API key for {service}")

# Initialize components
try:
    audio_processor = AudioProcessor(config["audio"])
    speech_recognizer = SpeechRecognizer(config["speech_recognition"])
    language_model = LanguageModel(config["llm"])
    voice_synthesizer = VoiceSynthesizer(config["voice"])
    session_manager = SessionManager()
except Exception as e:
    logger.error(f"Component initialization failed: {str(e)}")
    raise ConfigurationError("Failed to initialize components")

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    try:
        logger.info("Starting AI Voice Agent Platform")
        await speech_recognizer.initialize()
        await language_model.initialize()
        await voice_synthesizer.initialize()
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise ConfigurationError("Failed to initialize services")

@app.websocket("/ws/conversation")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for voice conversations."""
    await websocket.accept()
    session_id = session_manager.create_session()
    
    try:
        logger.info(f"New conversation session started: {session_id}")
        
        while True:
            try:
                # Receive audio data with timeout
                audio_data = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=30.0
                )
                
                # Process audio
                try:
                    processed_audio = audio_processor.process(audio_data)
                except Exception as e:
                    raise AudioProcessingError(f"Audio processing failed: {str(e)}")
                
                # Speech recognition
                try:
                    transcript = await speech_recognizer.transcribe(processed_audio)
                except Exception as e:
                    raise TranscriptionError(f"Speech recognition failed: {str(e)}")
                
                if transcript.is_final:
                    # Generate response using LLM
                    try:
                        response = await language_model.generate_response(
                            transcript.text,
                            session_id=session_id
                        )
                    except Exception as e:
                        raise LLMError(f"Language model processing failed: {str(e)}")
                    
                    # Synthesize voice
                    try:
                        audio_response = await voice_synthesizer.synthesize(response)
                    except Exception as e:
                        raise VoiceSynthesisError(f"Voice synthesis failed: {str(e)}")
                    
                    # Send response back to client
                    await websocket.send_bytes(audio_response)
                    
                # Update session activity
                session_manager.update_session(session_id)
                
            except asyncio.TimeoutError:
                logger.warning(f"Session {session_id} timed out")
                await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
                break
                
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in conversation: {error_msg}")
        try:
            await websocket.send_json({"error": error_msg})
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
    finally:
        session_manager.end_session(session_id)
        # Cleanup any resources
        try:
            await websocket.close()
        except:
            pass

@app.get("/health")
async def health_check():
    """Check the health of all components."""
    try:
        components_status = {
            "speech_recognition": speech_recognizer.health_check(),
            "language_model": language_model.health_check(),
            "voice_synthesis": voice_synthesizer.health_check(),
            "sessions": {
                "active_sessions": session_manager.get_active_sessions_count()
            }
        }
        
        # Check if any component is unhealthy
        all_healthy = all(
            status.get("status") == "healthy" 
            for status in components_status.values() 
            if isinstance(status, dict) and "status" in status
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": components_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during health check"
        )

@app.exception_handler(VoiceAgentError)
async def voice_agent_exception_handler(request, exc):
    """Handle Voice Agent specific exceptions."""
    logger.error(f"Voice Agent error: {str(exc)}")
    return {"error": str(exc), "type": exc.__class__.__name__}

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logger.add(
        "logs/voice_agent.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )
