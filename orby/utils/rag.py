"""RAG (Retrieval-Augmented Generation) system for Orby."""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib
from datetime import datetime
import PyPDF2
import docx
from bs4 import BeautifulSoup


@dataclass
class DocumentChunk:
    """A chunk of a document."""
    content: str
    document_id: str
    chunk_index: int
    metadata: Dict[str, str] = None
    embedding: Optional[List[float]] = None


class RAGSystem:
    """RAG system for local documents."""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.chunks: List[DocumentChunk] = []
        self.document_metadata: Dict[str, Dict] = {}
        self.index_path = Path.home() / ".orby" / "rag_index"
        self.index_path.mkdir(parents=True, exist_ok=True)
        self._load_index()
    
    def _load_index(self):
        """Load existing document chunks from index."""
        index_file = self.index_path / "chunks.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chunk_data in data:
                        chunk = DocumentChunk(
                            content=chunk_data['content'],
                            document_id=chunk_data['document_id'],
                            chunk_index=chunk_data['chunk_index'],
                            metadata=chunk_data.get('metadata', {}),
                            embedding=chunk_data.get('embedding')
                        )
                        self.chunks.append(chunk)
            except Exception:
                # If loading fails, start with empty index
                pass
    
    def _save_index(self):
        """Save document chunks to index."""
        try:
            index_file = self.index_path / "chunks.json"
            data = []
            for chunk in self.chunks:
                chunk_data = {
                    'content': chunk.content,
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index,
                    'metadata': chunk.metadata or {},
                    'embedding': chunk.embedding
                }
                data.append(chunk_data)
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            # If saving fails, ignore (but in production you might want to log)
            pass
    
    def _get_document_id(self, file_path: Path) -> str:
        """Generate a unique ID for a document."""
        return hashlib.md5(str(file_path).encode()).hexdigest()
    
    def _extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from various file types."""
        try:
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path.suffix.lower() == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path.suffix.lower() == '.pdf':
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text
            elif file_path.suffix.lower() == '.docx':
                doc = docx.Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            elif file_path.suffix.lower() == '.html':
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    return soup.get_text()
            else:
                # For code files and others, read as plain text
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            # If extraction fails, return empty string
            return ""
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            if chunk_words:  # Skip empty chunks
                chunk = ' '.join(chunk_words)
                chunks.append(chunk)
                if len(chunk_words) < chunk_size:
                    break  # Last chunk if shorter
        return chunks
    
    def index_file(self, file_path: Path) -> int:
        """Index a file and return number of chunks created."""
        if not file_path.exists():
            return 0
        
        document_id = self._get_document_id(file_path)
        text = self._extract_text_from_file(file_path)
        
        if not text.strip():
            return 0
        
        # Split into chunks
        chunks = self._chunk_text(text)
        
        # Remove existing chunks for this document
        self.chunks = [chunk for chunk in self.chunks if chunk.document_id != document_id]
        
        # Add new chunks
        for i, chunk_text in enumerate(chunks):
            chunk = DocumentChunk(
                content=chunk_text,
                document_id=document_id,
                chunk_index=i,
                metadata={
                    'file_path': str(file_path.relative_to(self.project_path)),
                    'file_name': file_path.name,
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            )
            self.chunks.append(chunk)
        
        # Update metadata
        self.document_metadata[document_id] = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'chunk_count': len(chunks),
            'indexed_at': datetime.now().isoformat()
        }
        
        self._save_index()
        return len(chunks)
    
    def index_project(self, file_patterns: List[str] = None) -> Dict[str, int]:
        """Index all relevant files in the project."""
        if file_patterns is None:
            file_patterns = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.java', '*.cpp', '*.h', '*.md', '*.txt', '*.html']
        
        results = {}
        for pattern in file_patterns:
            for file_path in self.project_path.rglob(pattern):
                # Skip hidden directories and files
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                
                # Skip the .orby directory itself
                if '.orby' in file_path.parts:
                    continue
                
                chunks_created = self.index_file(file_path)
                if chunks_created > 0:
                    results[str(file_path)] = chunks_created
        
        return results
    
    def search(self, query: str, max_results: int = 5) -> List[DocumentChunk]:
        """Search for relevant chunks based on a query."""
        # Simple keyword-based search for now
        # In a real implementation, this would use embeddings
        
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for chunk in self.chunks:
            # Calculate relevance score based on keyword matches
            chunk_lower = chunk.content.lower()
            chunk_words = set(chunk_lower.split())
            
            # Jaccard similarity (intersection over union)
            intersection = len(query_words.intersection(chunk_words))
            union = len(query_words.union(chunk_words))
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0:  # Only include if there's some match
                    results.append((similarity, chunk))
        
        # Sort by relevance
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Return just the chunks
        return [chunk for _, chunk in results[:max_results]]
    
    def get_context_for_query(self, query: str, max_chunks: int = 3) -> str:
        """Get relevant context for a query."""
        relevant_chunks = self.search(query, max_chunks)
        
        if not relevant_chunks:
            return ""
        
        context_parts = []
        for chunk in relevant_chunks:
            file_path = chunk.metadata.get('file_path', 'Unknown file')
            context_parts.append(f"[{file_path}] {chunk.content}")
        
        return "\n\n".join(context_parts)


# Global RAG system instance
rag_system = RAGSystem()