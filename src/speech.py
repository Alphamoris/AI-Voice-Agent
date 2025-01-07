from typing import Dict, Optional
import asyncio
from deepgram import Deepgram
import numpy as np
from dataclasses import dataclass
from loguru import logger
import os

@dataclass
class TranscriptionResult:
    text: str
    is_final: bool
    confidence: float
    language: str

class SpeechRecognizer:
    def __init__(self, config: Dict):
        self.config = config
        self.provider = config["default_provider"]
        self.deepgram_client = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize speech recognition clients."""
        if self.provider == "deepgram":
            self.deepgram_client = Deepgram(os.getenv("DEEPGRAM_API_KEY"))
        self.is_initialized = True
            
    async def transcribe(self, audio_data: np.ndarray) -> TranscriptionResult:
        """Transcribe audio data to text."""
        if not self.is_initialized:
            raise RuntimeError("Speech recognizer not initialized")
            
        try:
            if self.provider == "deepgram":
                return await self._transcribe_deepgram(audio_data)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise
            
    async def _transcribe_deepgram(self, audio_data: np.ndarray) -> TranscriptionResult:
        """Transcribe using Deepgram."""
        try:
            # Convert numpy array to bytes
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
            # Get transcription options from config
            options = {
                "model": self.config["providers"]["deepgram"]["model"],
                "language": self.config["providers"]["deepgram"]["language"],
                "interim_results": self.config["providers"]["deepgram"]["interim_results"],
                "punctuate": self.config["providers"]["deepgram"]["punctuate"],
                "diarize": self.config["providers"]["deepgram"]["diarize"]
            }
            
            # Send audio to Deepgram
            response = await self.deepgram_client.transcription.prerecorded(
                {"buffer": audio_bytes, "mimetype": "audio/raw"},
                options
            )
            
            # Extract results
            result = response["results"]["channels"][0]["alternatives"][0]
            
            return TranscriptionResult(
                text=result["transcript"],
                is_final=True,  # For pre-recorded audio, always final
                confidence=result["confidence"],
                language=self.config["providers"]["deepgram"]["language"]
            )
            
        except Exception as e:
            logger.error(f"Deepgram transcription error: {str(e)}")
            raise
            
    def health_check(self) -> Dict:
        """Check the health of the speech recognition service."""
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "provider": self.provider
        }
