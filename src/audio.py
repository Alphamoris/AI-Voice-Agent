import numpy as np
from typing import Dict, Optional
import sounddevice as sd
from loguru import logger

class AudioProcessor:
    def __init__(self, config: Dict):
        self.sample_rate = config["sample_rate"]
        self.channels = config["channels"]
        self.chunk_size = config["chunk_size"]
        self.buffer_size = config["buffer_size"]
        
        # Initialize audio buffer
        self.buffer = np.zeros((self.buffer_size, self.channels))
        self.buffer_index = 0
        
    def process(self, audio_data: bytes) -> np.ndarray:
        """Process incoming audio data."""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # Reshape if stereo
            if self.channels == 2:
                audio_array = audio_array.reshape(-1, 2)
            
            # Apply noise reduction
            processed_audio = self._reduce_noise(audio_array)
            
            # Apply automatic gain control
            processed_audio = self._apply_agc(processed_audio)
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise
            
    def _reduce_noise(self, audio_array: np.ndarray) -> np.ndarray:
        """Apply basic noise reduction."""
        # Simple noise gate
        noise_threshold = 0.01
        audio_array[np.abs(audio_array) < noise_threshold] = 0
        return audio_array
        
    def _apply_agc(self, audio_array: np.ndarray) -> np.ndarray:
        """Apply Automatic Gain Control."""
        target_rms = 0.2
        current_rms = np.sqrt(np.mean(audio_array**2))
        
        if current_rms > 0:
            gain = target_rms / current_rms
            audio_array = audio_array * gain
            
        return np.clip(audio_array, -1.0, 1.0)
        
    def get_stream_parameters(self) -> Dict:
        """Return audio stream parameters."""
        return {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size
        }
        
    def reset(self):
        """Reset audio processor state."""
        self.buffer = np.zeros((self.buffer_size, self.channels))
        self.buffer_index = 0
