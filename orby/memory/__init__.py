"""Enhanced memory system for Orby with robust memory management."""
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import hashlib
import threading
from .memory_db import MemoryDatabase
from .context_manager import ContextManager


@dataclass
class MemoryEntry:
    """A single memory entry."""
    content: str
    timestamp: datetime
    content_type: str = "text"
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0  # 0.0 to 1.0 scale
    metadata: Dict[str, Any] = field(default_factory=dict)
    entry_id: Optional[int] = None


class EnhancedMemorySystem:
    """Enhanced memory system with SQLite backend, ephemeral and persistent storage."""
    
    def __init__(self, session_id: Optional[str] = None, project_path: Optional[Path] = None, 
                 memory_enabled: bool = True):
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.project_path = project_path or Path.cwd()
        
        # Memory control flag
        self.memory_enabled = memory_enabled
        
        # Ephemeral memory (session-based) - stores recent items in RAM for quick access
        self.session_memory: List[MemoryEntry] = []
        self.session_memory_limit = 100  # Max items in session memory
        
        # Persistent memory (SQLite-based)
        self.memory_db = MemoryDatabase()
        
        # Advanced context manager with embeddings and smart chunking
        self.context_manager = ContextManager()
        
        # Ensure session exists in DB
        self.memory_db.create_session(self.session_id, str(self.project_path))
    
    def set_memory_enabled(self, enabled: bool):
        """Enable or disable memory functionality."""
        self.memory_enabled = enabled
        if not enabled:
            # Clear memory when disabling
            self.clear_session_memory()
            # Note: We don't clear persistent memory as user might want to re-enable
    
    def add_to_session_memory(self, content: str, content_type: str = "text", 
                             tags: List[str] = None, importance: float = 1.0, 
                             metadata: Dict[str, Any] = None) -> int:
        """Add an entry to both ephemeral and persistent memory with advanced context management."""
        if not self.memory_enabled:
            # Return a dummy ID if memory is disabled
            return -1
        
        # Add to ephemeral memory
        entry = MemoryEntry(
            content=content,
            timestamp=datetime.now(),
            content_type=content_type,
            tags=tags or [],
            importance=importance,
            metadata=metadata or {}
        )
        
        self.session_memory.insert(0, entry)  # Insert at beginning for recency
        
        # Keep session memory within limits
        if len(self.session_memory) > self.session_memory_limit:
            self.session_memory = self.session_memory[:self.session_memory_limit]
        
        # Add to persistent memory
        entry_id = self.memory_db.add_memory_entry(
            session_id=self.session_id,
            content=content,
            content_type=content_type,
            importance=importance,
            tags=tags,
            metadata=metadata
        )
        
        # Also add to context manager for advanced search and embeddings
        try:
            self.context_manager.add_content(
                session_id=self.session_id,
                content=content,
                content_type=content_type,
                importance=importance,
                tags=tags,
                metadata=metadata
            )
        except Exception:
            # If context manager fails, continue with basic functionality
            pass
        
        # Update the ephemeral entry with the DB ID
        entry.entry_id = entry_id
        
        return entry_id
    
    def search_session_memory(self, query: str, content_type: Optional[str] = None, 
                             max_results: int = 10) -> List[MemoryEntry]:
        """Search in session memory with relevance ranking using embeddings and keyword search."""
        if not self.memory_enabled:
            return []
        
        query_lower = query.lower()
        
        # First, search in ephemeral memory
        ephemeral_results = []
        for entry in self.session_memory:
            if query_lower in entry.content.lower():
                ephemeral_results.append(entry)
        
        # Search using context manager (with embeddings if available)
        try:
            context_results = self.context_manager.search_by_similarity(
                session_id=self.session_id,
                query=query,
                top_k=max_results
            )
            
            # Convert context results to MemoryEntry objects
            context_entries = []
            for chunk in context_results:
                entry = MemoryEntry(
                    content=chunk.content,
                    timestamp=datetime.fromisoformat(chunk.created_at),
                    content_type=chunk.content_type,
                    tags=chunk.tags,
                    importance=chunk.importance,
                    metadata=chunk.metadata,
                    entry_id=chunk.id
                )
                context_entries.append(entry)
        except Exception:
            # Fallback to basic search if context manager fails
            context_entries = []
        
        # Then search in persistent memory as backup
        persistent_results = self.memory_db.search_memory(
            session_id=self.session_id,
            query=query,
            content_type=content_type,
            limit=max_results
        )
        
        persistent_entries = []
        for row in persistent_results:
            entry = MemoryEntry(
                content=row['content'],
                timestamp=datetime.fromisoformat(row['created_at']),
                content_type=row['content_type'],
                tags=row['tags'],
                importance=row['importance'],
                metadata=row['metadata'],
                entry_id=row['id']
            )
            persistent_entries.append(entry)
        
        # Combine results: context results first (more relevant), then ephemeral, then persistent
        all_results = context_entries + ephemeral_results + persistent_entries
        
        # Remove duplicates based on content
        seen_contents = set()
        unique_results = []
        for entry in all_results:
            content_hash = hashlib.md5(entry.content.encode()).hexdigest()
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(entry)
        
        # Sort by importance and recency
        unique_results.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        
        return unique_results[:max_results]
    
    def get_context(self, max_entries: int = 20, include_types: Optional[List[str]] = None) -> str:
        """Get relevant context from both memory types with advanced chunking and retrieval."""
        if not self.memory_enabled:
            return ""
        
        # Get context from the context manager which uses embeddings and smart retrieval
        try:
            context = self.context_manager.get_context_for_session(
                session_id=self.session_id,
                max_chunks=max_entries,
                content_types=include_types
            )
            return context
        except Exception:
            # Fallback to basic database context if context manager fails
            return self.memory_db.get_session_context(
                session_id=self.session_id,
                max_entries=max_entries,
                include_types=include_types
            )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the current session."""
        # Get basic stats from the main DB
        basic_stats = self.memory_db.get_session_summary(self.session_id)
        
        # Get advanced stats from the context manager
        try:
            context_stats = self.context_manager.get_session_stats(self.session_id)
            # Combine the stats
            combined_stats = {**basic_stats, **context_stats}
            return combined_stats
        except Exception:
            # If context manager fails, return basic stats
            return basic_stats
    
    def clear_session_memory(self):
        """Clear ephemeral session memory."""
        self.session_memory = []
    
    def clear_persistent_memory(self):
        """Clear persistent memory for the session."""
        self.memory_db.delete_session_memory(self.session_id)
        
        # Also clear from context manager
        try:
            self.context_manager.delete_session_content(self.session_id)
        except Exception:
            # If context manager clear fails, continue
            pass
    
    def clear_all_memory(self):
        """Clear both ephemeral and persistent memory."""
        self.clear_session_memory()
        self.clear_persistent_memory()
    
    def save_session_memory(self, session_name: str) -> bool:
        """Save current session memory to a named session."""
        try:
            # Create a backup session with the new name
            backup_session_id = f"saved_{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            self.memory_db.create_session(backup_session_id, str(self.project_path))
            
            # Copy memory entries to the backup session
            current_entries = self.memory_db.get_memory_entries(self.session_id, limit=10000)
            
            for entry in current_entries:
                self.memory_db.add_memory_entry(
                    session_id=backup_session_id,
                    content=entry['content'],
                    content_type=entry['content_type'],
                    importance=entry['importance'],
                    tags=entry['tags'],
                    metadata=entry['metadata']
                )
            
            # Also save to context manager if available
            try:
                # Context manager automatically saves to its own DB, so we just need to ensure consistency
                pass
            except Exception:
                # If context manager save fails, continue
                pass
            
            return True
        except Exception:
            return False
    
    def load_session_memory(self, session_name: str) -> bool:
        """Load session memory from a named session."""
        try:
            # Find sessions that match the pattern for this session name
            # We'll search for saved sessions with this name
            import sqlite3
            
            with self.memory_db._get_db_connection() as conn:
                cursor = conn.execute('''
                    SELECT session_id FROM sessions 
                    WHERE session_id LIKE ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (f"saved_{session_name}_%",))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                backup_session_id = result['session_id']
                
                # First, clear current session memory
                self.clear_all_memory()
                
                # Copy from backup session to current session
                backup_entries = self.memory_db.get_memory_entries(backup_session_id, limit=10000)
                
                for entry in backup_entries:
                    self.add_to_session_memory(
                        content=entry['content'],
                        content_type=entry['content_type'],
                        importance=entry['importance'],
                        tags=entry['tags'],
                        metadata=entry['metadata']
                    )
            
            return True
        except Exception:
            return False
    
    def get_available_sessions(self) -> List[str]:
        """Get list of available saved sessions."""
        import sqlite3
        
        try:
            with self.memory_db._get_db_connection() as conn:
                # Get sessions that start with 'saved_' and extract the session name
                cursor = conn.execute('''
                    SELECT DISTINCT session_id
                    FROM sessions 
                    WHERE session_id LIKE 'saved_%'
                    ORDER BY created_at DESC
                ''')
                
                results = cursor.fetchall()
                session_names = []
                seen = set()
                
                for row in results:
                    session_id = row['session_id']
                    # Extract the session name from 'saved_{name}_{timestamp}'
                    if session_id.startswith('saved_'):
                        parts = session_id.split('_', 2)  # Split into 3 parts: 'saved', name, timestamp
                        if len(parts) >= 2:
                            name = parts[1]
                            if name not in seen:
                                seen.add(name)
                                session_names.append(name)
                
                return session_names
        except Exception:
            return []

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        summary = self.get_session_summary()
        
        # Get additional stats
        ephemeral_count = len(self.session_memory)
        
        return {
            'session_id': self.session_id,
            'ephemeral_entries': ephemeral_count,
            'persistent_entries': summary.get('total_entries', 0),
            'average_importance': summary.get('average_importance', 0.0),
            'content_type_distribution': summary.get('content_type_counts', {}),
            'last_updated': summary.get('last_updated'),
            'project_path': str(self.project_path)
        }
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get the current memory status."""
        return {
            'enabled': self.memory_enabled,
            'session_id': self.session_id,
            'ephemeral_entries': len(self.session_memory) if self.memory_enabled else 0,
            'project_path': str(self.project_path)
        }
    
    def close(self):
        """Close the memory system and database connections."""
        self.memory_db.close()


# Global memory system instance
try:
    memory_system = EnhancedMemorySystem()
except Exception as e:
    print(f"Warning: Failed to initialize memory system: {e}")
    # Provide a fallback memory system that doesn't crash the app
    class FallbackMemorySystem:
        def __init__(self):
            self.session_id = "fallback"
            self.memory_enabled = False
            
        def add_to_session_memory(self, *args, **kwargs):
            return -1
            
        def search_session_memory(self, *args, **kwargs):
            return []
            
        def get_context(self, *args, **kwargs):
            return ""
            
        def get_session_summary(self):
            return {}
            
        def clear_session_memory(self):
            pass
            
        def clear_persistent_memory(self):
            pass
            
        def clear_all_memory(self):
            pass
            
        def save_session_memory(self, *args, **kwargs):
            return False
            
        def load_session_memory(self, *args, **kwargs):
            return False
            
        def get_available_sessions(self):
            return []
            
        def get_memory_stats(self):
            return {}
            
        def get_memory_status(self):
            return {'enabled': False}
            
        def set_memory_enabled(self, enabled):
            pass
    
    memory_system = FallbackMemorySystem()