import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        
    def create_session(self) -> str:
        """Create a new session and return session ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "is_active": True
        }
        return session_id
        
    def update_session(self, session_id: str):
        """Update session last activity time."""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.now()
            
    def end_session(self, session_id: str):
        """End a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["is_active"] = False
            logger.info(f"Session ended: {session_id}")
            
    def cleanup_inactive_sessions(self, max_age_minutes: int = 30):
        """Remove inactive sessions older than max_age_minutes."""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session_data in self.sessions.items():
            if not session_data["is_active"]:
                age = current_time - session_data["last_activity"]
                if age > timedelta(minutes=max_age_minutes):
                    sessions_to_remove.append(session_id)
                    
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            logger.info(f"Removed inactive session: {session_id}")
            
    def get_active_sessions_count(self) -> int:
        """Return the number of active sessions."""
        return sum(1 for session in self.sessions.values() if session["is_active"])
