"""Robust memory database system for Orby using SQLite."""
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager
import threading


class MemoryDatabase:
    """SQLite-based memory database with thread-safe operations."""
    
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = db_path or self._get_default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_database()
    
    @staticmethod
    def _get_default_db_path() -> Path:
        """Get the default database path."""
        return Path.home() / ".orby" / "memory" / "orby_memory.db"
    
    def _init_database(self):
        """Initialize the database with all necessary tables."""
        with self._get_db_connection() as conn:
            # Sessions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    project_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            ''')
            
            # Memory entries table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    content TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    importance REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    embedding_hash TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # Memory chunks table for large content
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memory_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id INTEGER,
                    chunk_index INTEGER,
                    content TEXT NOT NULL,
                    embedding_hash TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (entry_id) REFERENCES memory_entries(id)
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memory_entries_session ON memory_entries(session_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memory_entries_importance ON memory_entries(importance)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memory_entries_created ON memory_entries(created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memory_entries_type ON memory_entries(content_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memory_chunks_entry ON memory_chunks(entry_id)')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get a database connection with thread-local storage for connection reusing."""
        if not hasattr(self._local, 'connection'):
            conn = sqlite3.connect(
                str(self.db_path), 
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            self._local.connection = conn
        else:
            conn = self._local.connection
        
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            # For now, keeping connection open for reuse in the same thread
            pass
    
    def create_session(self, session_id: str, project_path: str, metadata: Optional[Dict] = None) -> bool:
        """Create a new session."""
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO sessions (session_id, project_path, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    project_path,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps(metadata or {})
                ))
                return True
        except sqlite3.IntegrityError:
            return False  # Session already exists
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                'SELECT 1 FROM sessions WHERE session_id = ?',
                (session_id,)
            )
            return cursor.fetchone() is not None
    
    def add_memory_entry(self, session_id: str, content: str, content_type: str = 'text', 
                        importance: float = 1.0, tags: List[str] = None, 
                        metadata: Dict[str, Any] = None) -> int:
        """Add a memory entry."""
        if not self.session_exists(session_id):
            self.create_session(session_id, str(Path.cwd()), {})
        
        with self._get_db_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO memory_entries 
                (session_id, content, content_type, importance, created_at, updated_at, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                content,
                content_type,
                importance,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps(tags or []),
                json.dumps(metadata or {})
            ))
            
            entry_id = cursor.lastrowid
            
            # If content is large, also store it in chunks
            if len(content) > 1000:  # If content is larger than 1000 chars
                self._chunk_and_store_content(entry_id, content)
            
            return entry_id
    
    def _chunk_and_store_content(self, entry_id: int, content: str, chunk_size: int = 500):
        """Chunk large content and store in chunks table."""
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            chunks.append((entry_id, i // chunk_size, chunk, datetime.now().isoformat()))
        
        with self._get_db_connection() as conn:
            conn.executemany('''
                INSERT INTO memory_chunks (entry_id, chunk_index, content, created_at)
                VALUES (?, ?, ?, ?)
            ''', chunks)
    
    def get_memory_entries(self, session_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get memory entries for a session."""
        with self._get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM memory_entries 
                WHERE session_id = ? 
                ORDER BY importance DESC, created_at DESC
                LIMIT ? OFFSET ?
            ''', (session_id, limit, offset))
            
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def search_memory(self, session_id: str, query: str, content_type: Optional[str] = None, 
                     limit: int = 20) -> List[Dict]:
        """Search memory entries containing the query."""
        query_lower = query.lower()
        
        sql = '''
            SELECT * FROM memory_entries 
            WHERE session_id = ? AND (LOWER(content) LIKE ? OR LOWER(metadata) LIKE ?)
        '''
        params = [session_id, f'%{query_lower}%', f'%{query_lower}%']
        
        if content_type:
            sql += ' AND content_type = ?'
            params.append(content_type)
        
        sql += ' ORDER BY importance DESC, created_at DESC LIMIT ?'
        params.append(limit)
        
        with self._get_db_connection() as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def get_session_context(self, session_id: str, max_entries: int = 20, 
                           include_types: Optional[List[str]] = None) -> str:
        """Get formatted context from session memory."""
        entries = self.get_memory_entries(session_id, limit=max_entries)
        
        if include_types:
            entries = [e for e in entries if e.get('content_type') in include_types]
        
        context_parts = []
        for entry in entries:
            tags_str = ', '.join(entry.get('tags', []))
            tag_info = f" [Tags: {tags_str}]" if tags_str else ""
            context_parts.append(f"[{entry['content_type'].upper()} - {entry['created_at']}{tag_info}] {entry['content']}")
        
        return '\n'.join(context_parts[:max_entries])
    
    def delete_memory_entry(self, entry_id: int) -> bool:
        """Delete a memory entry."""
        with self._get_db_connection() as conn:
            cursor = conn.execute('DELETE FROM memory_entries WHERE id = ?', (entry_id,))
            return cursor.rowcount > 0
    
    def delete_session_memory(self, session_id: str) -> bool:
        """Delete all memory entries for a session."""
        with self._get_db_connection() as conn:
            cursor = conn.execute('DELETE FROM memory_entries WHERE session_id = ?', (session_id,))
            return cursor.rowcount > 0
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session."""
        with self._get_db_connection() as conn:
            # Get count of different content types
            cursor = conn.execute('''
                SELECT content_type, COUNT(*) as count
                FROM memory_entries 
                WHERE session_id = ?
                GROUP BY content_type
            ''', (session_id,))
            content_type_counts = dict(cursor.fetchall())
            
            # Get total entries and average importance
            cursor = conn.execute('''
                SELECT COUNT(*) as total, AVG(importance) as avg_importance
                FROM memory_entries 
                WHERE session_id = ?
            ''', (session_id,))
            stats = cursor.fetchone()
            
            return {
                'session_id': session_id,
                'total_entries': stats['total'] or 0,
                'average_importance': stats['avg_importance'] or 0.0,
                'content_type_counts': content_type_counts,
                'last_updated': self._get_session_last_updated(session_id)
            }
    
    def _get_session_last_updated(self, session_id: str) -> Optional[str]:
        """Get the last updated time for a session."""
        with self._get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT MAX(updated_at) as last_update
                FROM memory_entries 
                WHERE session_id = ?
            ''', (session_id,))
            result = cursor.fetchone()
            return result['last_update'] if result and result['last_update'] else None
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert a SQLite row to a dictionary."""
        data = dict(row)
        # Parse JSON fields
        data['tags'] = json.loads(data['tags']) if isinstance(data['tags'], str) else data['tags']
        data['metadata'] = json.loads(data['metadata']) if isinstance(data['metadata'], str) else data['metadata']
        return data
    
    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')