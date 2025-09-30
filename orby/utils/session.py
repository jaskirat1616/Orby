"""Session management for Orby."""
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import hashlib


@dataclass
class Session:
    """A conversation session."""
    name: str
    created_at: datetime
    model: str
    backend: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class SessionManager:
    """Manages conversation sessions."""
    
    def __init__(self):
        self.sessions_dir = Path.home() / ".orby" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[Session] = None
    
    def create_session(self, name: str, model: str = "default", backend: str = "ollama") -> Session:
        """Create a new session."""
        session = Session(
            name=name,
            created_at=datetime.now(),
            model=model,
            backend=backend
        )
        self.current_session = session
        return session
    
    def save_session(self, session: Session = None, name: str = None) -> bool:
        """Save a session to disk."""
        if session is None:
            session = self.current_session
        
        if session is None:
            return False
        
        # Use provided name or session's name
        session_name = name or session.name
        
        # Create filename
        filename = f"{session_name}.json"
        filepath = self.sessions_dir / filename
        
        try:
            # Convert session to serializable format
            session_data = {
                'name': session.name,
                'created_at': session.created_at.isoformat(),
                'model': session.model,
                'backend': session.backend,
                'messages': session.messages,
                'metadata': session.metadata,
                'tags': session.tags
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def load_session(self, name: str) -> Optional[Session]:
        """Load a session from disk."""
        filename = f"{name}.json"
        filepath = self.sessions_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Convert back to Session object
            session = Session(
                name=session_data['name'],
                created_at=datetime.fromisoformat(session_data['created_at']),
                model=session_data['model'],
                backend=session_data['backend'],
                messages=session_data['messages'],
                metadata=session_data.get('metadata', {}),
                tags=session_data.get('tags', [])
            )
            
            self.current_session = session
            return session
        except Exception:
            return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions."""
        sessions = []
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                sessions.append({
                    'name': session_data['name'],
                    'created_at': session_data['created_at'],
                    'model': session_data['model'],
                    'backend': session_data['backend'],
                    'tags': session_data.get('tags', []),
                    'file': session_file.name
                })
            except Exception:
                continue
        
        return sessions
    
    def delete_session(self, name: str) -> bool:
        """Delete a saved session."""
        filename = f"{name}.json"
        filepath = self.sessions_dir / filename
        
        if filepath.exists():
            try:
                filepath.unlink()
                return True
            except Exception:
                return False
        return False
    
    def add_message_to_current_session(self, message: Dict[str, Any]):
        """Add a message to the current session."""
        if self.current_session:
            self.current_session.messages.append(message)
    
    def get_session_summary(self, session: Session) -> str:
        """Get a summary of a session."""
        message_count = len(session.messages)
        tag_str = ", ".join(session.tags) if session.tags else "None"
        
        return f"Session '{session.name}' with {message_count} messages. Tags: {tag_str}"
    
    def tag_session(self, session: Session, tags: List[str]):
        """Add tags to a session."""
        session.tags.extend(tags)
        # Remove duplicates
        session.tags = list(set(session.tags))


# Global session manager instance
session_manager = SessionManager()