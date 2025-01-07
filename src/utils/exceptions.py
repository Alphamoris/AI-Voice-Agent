class VoiceAgentError(Exception):
    """Base exception for Voice Agent Platform."""
    pass

class AudioProcessingError(VoiceAgentError):
    """Raised when there's an error processing audio data."""
    pass

class TranscriptionError(VoiceAgentError):
    """Raised when there's an error during speech recognition."""
    pass

class LLMError(VoiceAgentError):
    """Raised when there's an error with language model processing."""
    pass

class VoiceSynthesisError(VoiceAgentError):
    """Raised when there's an error synthesizing voice."""
    pass

class ConfigurationError(VoiceAgentError):
    """Raised when there's an error in configuration."""
    pass

class SessionError(VoiceAgentError):
    """Raised when there's an error managing sessions."""
    pass

class APIKeyError(VoiceAgentError):
    """Raised when there's an issue with API keys."""
    pass

class ConnectionError(VoiceAgentError):
    """Raised when there's a connection issue with external services."""
    pass
