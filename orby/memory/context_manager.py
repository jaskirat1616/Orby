"""Advanced context management with embeddings and smart chunking for Orby."""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import hashlib
import pickle
from datetime import datetime
import threading
import queue
import time
from dataclasses import dataclass, field
from contextlib import contextmanager
import sqlite3


@dataclass
class MemoryChunk:
    """Represents a chunk of memory with its embedding."""
    id: int
    content: str
    embedding: Optional[List[float]] = None
    content_type: str = "text"
    importance: float = 1.0
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""


class EmbeddingManager:
    """Manages embeddings using sentence transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()
        self._embeddings_available = self._check_embeddings_available()
    
    def _check_embeddings_available(self) -> bool:
        """Check if embeddings libraries are available."""
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            return True
        except ImportError:
            return False
    
    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None and self._embeddings_available:
            with self._lock:
                if self._model is None and self._embeddings_available:
                    try:
                        from sentence_transformers import SentenceTransformer
                        self._model = SentenceTransformer(self.model_name)
                    except Exception:
                        # Fallback to a simpler approach if sentence transformers isn't available
                        self._embeddings_available = False
                        self._model = None
        return self._model
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        if self._embeddings_available and self.model is not None:
            try:
                from sentence_transformers import SentenceTransformer
                embedding = self.model.encode([text])[0]
                return embedding.tolist()
            except Exception:
                pass
        # Fallback: return None if embedding fails
        return None
    
    def compute_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        if self._embeddings_available:
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                # Convert to numpy arrays
                arr1 = np.array(emb1).reshape(1, -1)
                arr2 = np.array(emb2).reshape(1, -1)
                similarity = cosine_similarity(arr1, arr2)[0][0]
                return float(similarity)
            except Exception:
                pass
        # Fallback: use a simple similarity measure
        return self._simple_similarity(emb1, emb2)
    
    def _simple_similarity(self, text1: List[float], text2: List[float]) -> float:
        """Simple similarity calculation when sklearn is not available."""
        # Fallback similarity calculation
        if len(text1) != len(text2):
            return 0.0
        
        # Calculate simple cosine similarity manually
        try:
            dot_product = sum(a * b for a, b in zip(text1, text2))
            magnitude1 = sum(a * a for a in text1) ** 0.5
            magnitude2 = sum(b * b for b in text2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        except:
            return 0.0


class ContextManager:
    """Advanced context manager with smart chunking, embeddings, and retrieval."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._get_default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_manager = EmbeddingManager()
        self._local = threading.local()
        self._init_database()
        
        # For performance, we'll cache recent embeddings
        self.embedding_cache = {}
        self.max_cache_size = 1000
    
    @staticmethod
    def _get_default_db_path() -> Path:
        """Get the default database path."""
        return Path.home() / ".orby" / "memory" / "context_memory.db"
    
    def _init_database(self):
        """Initialize the database with embedding support."""
        with self._get_db_connection() as conn:
            # Chunks table with embedding support
            conn.execute('''
                CREATE TABLE IF NOT EXISTS context_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    importance REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    embedding BLOB,
                    embedding_hash TEXT UNIQUE
                )
            ''')
            
            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_chunks_session ON context_chunks(session_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_chunks_type ON context_chunks(content_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_chunks_importance ON context_chunks(importance)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hash ON context_chunks(embedding_hash)')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get a database connection with thread-local storage."""
        if not hasattr(self._local, 'connection'):
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            conn.row_factory = sqlite3.Row
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
            pass  # Keep connection open for reuse in same thread
    
    def _hash_content(self, content: str) -> str:
        """Create a hash of the content for deduplication."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """Serialize embedding to bytes for storage."""
        return pickle.dumps(embedding)
    
    def _deserialize_embedding(self, embedding_bytes: bytes) -> List[float]:
        """Deserialize embedding from bytes."""
        return pickle.loads(embedding_bytes)
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
                
            # Move start forward by chunk_size - overlap
            start = end - overlap
        
        return chunks
    
    def add_content(self, session_id: str, content: str, content_type: str = "text", 
                   importance: float = 1.0, tags: List[str] = None, 
                   metadata: Dict[str, Any] = None) -> List[int]:
        """Add content, chunk it, and store with embeddings."""
        tags = tags or []
        metadata = metadata or {}
        
        # Chunk the content
        chunks = self.chunk_text(content)
        chunk_ids = []
        
        for chunk_text in chunks:
            # Generate embedding
            embedding = self.embedding_manager.embed_text(chunk_text)
            
            # Create embedding hash for deduplication
            content_hash = self._hash_content(chunk_text)
            
            with self._get_db_connection() as conn:
                try:
                    cursor = conn.execute('''
                        INSERT INTO context_chunks 
                        (session_id, content, content_type, importance, created_at, updated_at, tags, metadata, embedding, embedding_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        session_id,
                        chunk_text,
                        content_type,
                        importance,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        str(tags),
                        str(metadata),
                        self._serialize_embedding(embedding) if embedding else None,
                        content_hash
                    ))
                    chunk_ids.append(cursor.lastrowid)
                except sqlite3.IntegrityError:
                    # Content already exists, skip
                    continue
        
        return chunk_ids
    
    def search_by_similarity(self, session_id: str, query: str, top_k: int = 10, 
                           min_similarity: float = 0.3) -> List[MemoryChunk]:
        """Search for chunks similar to the query using embeddings."""
        query_embedding = self.embedding_manager.embed_text(query)
        if not query_embedding:
            # Fallback to keyword search if embedding fails
            return self._keyword_search(session_id, query, top_k)
        
        with self._get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT id, session_id, content, content_type, importance, created_at, tags, metadata
                FROM context_chunks 
                WHERE session_id = ? AND embedding IS NOT NULL
            ''', (session_id,))
            
            results = []
            for row in cursor.fetchall():
                try:
                    # Try to load the stored embedding
                    embedding_blob = conn.execute(
                        'SELECT embedding FROM context_chunks WHERE id = ?', 
                        (row['id'],)
                    ).fetchone()['embedding']
                    
                    if embedding_blob:
                        stored_embedding = self._deserialize_embedding(embedding_blob)
                        similarity = self.embedding_manager.compute_similarity(
                            query_embedding, stored_embedding
                        )
                        
                        if similarity >= min_similarity:
                            chunk = MemoryChunk(
                                id=row['id'],
                                content=row['content'],
                                content_type=row['content_type'],
                                importance=row['importance'],
                                created_at=row['created_at'],
                                tags=eval(row['tags']),  # Safe because we control the data
                                metadata=eval(row['metadata']),  # Safe because we control the data
                                session_id=row['session_id']
                            )
                            results.append((chunk, similarity))
                except Exception:
                    # If embedding comparison fails, skip this chunk
                    continue
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return [chunk for chunk, _ in results[:top_k]]
    
    def _keyword_search(self, session_id: str, query: str, top_k: int = 10) -> List[MemoryChunk]:
        """Fallback keyword search when embeddings aren't available."""
        query_lower = query.lower()
        
        with self._get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT id, session_id, content, content_type, importance, created_at, tags, metadata
                FROM context_chunks 
                WHERE session_id = ? AND LOWER(content) LIKE ?
                ORDER BY importance DESC
                LIMIT ?
            ''', (session_id, f'%{query_lower}%', top_k))
            
            results = []
            for row in cursor.fetchall():
                chunk = MemoryChunk(
                    id=row['id'],
                    content=row['content'],
                    content_type=row['content_type'],
                    importance=row['importance'],
                    created_at=row['created_at'],
                    tags=eval(row['tags']),
                    metadata=eval(row['metadata']),
                    session_id=row['session_id']
                )
                results.append(chunk)
            
            return results
    
    def get_context_for_session(self, session_id: str, max_chunks: int = 20, 
                              content_types: Optional[List[str]] = None) -> str:
        """Get relevant context for a session."""
        with self._get_db_connection() as conn:
            # Build query based on content types
            query = '''
                SELECT id, content, content_type, importance, created_at, tags, metadata
                FROM context_chunks 
                WHERE session_id = ?
            '''
            params = [session_id]
            
            if content_types:
                placeholders = ','.join(['?' for _ in content_types])
                query += f' AND content_type IN ({placeholders})'
                params.extend(content_types)
            
            query += ' ORDER BY importance DESC, created_at DESC LIMIT ?'
            params.append(max_chunks)
            
            cursor = conn.execute(query, params)
            
            context_parts = []
            for row in cursor.fetchall():
                tags_str = ', '.join(eval(row['tags']))
                tag_info = f" [Tags: {tags_str}]" if tags_str else ""
                context_parts.append(
                    f"[{row['content_type'].upper()} - {row['created_at']}{tag_info}]\n{row['content']}"
                )
            
            return '\n\n'.join(context_parts)
    
    def delete_session_content(self, session_id: str) -> bool:
        """Delete all content for a session."""
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                'DELETE FROM context_chunks WHERE session_id = ?', 
                (session_id,)
            )
            return cursor.rowcount > 0
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        with self._get_db_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_chunks,
                    AVG(importance) as avg_importance,
                    MIN(created_at) as first_created,
                    MAX(created_at) as last_updated
                FROM context_chunks 
                WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            
            # Get content type distribution
            cursor = conn.execute('''
                SELECT content_type, COUNT(*) as count
                FROM context_chunks 
                WHERE session_id = ?
                GROUP BY content_type
            ''', (session_id,))
            
            content_types = dict(cursor.fetchall())
            
            return {
                'total_chunks': row['total_chunks'] or 0,
                'average_importance': row['avg_importance'] or 0.0,
                'first_created': row['first_created'],
                'last_updated': row['last_updated'],
                'content_type_distribution': content_types
            }