import yaml
from typing import Dict, Any
from pathlib import Path

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
        
    def _load_config(self):
        """Load configuration from yaml file."""
        config_path = Path("config.yaml")
        if not config_path.exists():
            raise FileNotFoundError("config.yaml not found")
            
        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
                
            if value is None:
                return default
                
        return value
        
    def get_all(self) -> Dict:
        """Get entire configuration."""
        return self._config.copy()
        
    def validate(self) -> bool:
        """Validate configuration."""
        required_keys = [
            "app.name",
            "app.version",
            "audio.sample_rate",
            "audio.channels",
            "speech_recognition.default_provider",
            "llm.default_provider",
            "voice.default_provider"
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                raise ValueError(f"Missing required configuration: {key}")
                
        return True
