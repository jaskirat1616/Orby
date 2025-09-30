"""History navigation system for Orby TUI."""
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button, ListView, ListItem, Input, Label
from textual.reactive import reactive
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import json
import os


class HistoryManager:
    """Manage conversation history for Orby."""
    
    def __init__(self):
        self.history_dir = Path.home() / ".orby" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def save_conversation(self, messages: List[Dict], session_name: str = None) -> str:
        """Save a conversation to history."""
        if not session_name:
            session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add metadata
        history_entry = {
            "id": session_name,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "message_count": len(messages),
            "summary": self._generate_summary(messages)
        }
        
        # Save to file
        history_file = self.history_dir / f"{session_name}.json"
        with open(history_file, 'w') as f:
            json.dump(history_entry, f, indent=2)
        
        return session_name
    
    def load_conversation(self, session_id: str) -> Dict[str, Any]:
        """Load a conversation by ID."""
        history_file = self.history_dir / f"{session_id}.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                return json.load(f)
        return {}
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions."""
        sessions = []
        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    session_data = json.load(f)
                    sessions.append({
                        "id": session_data.get("id", file_path.stem),
                        "timestamp": session_data.get("timestamp", ""),
                        "message_count": session_data.get("message_count", 0),
                        "summary": session_data.get("summary", ""),
                        "file_path": str(file_path)
                    })
            except Exception:
                continue  # Skip malformed files
        
        # Sort by timestamp (newest first)
        sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        history_file = self.history_dir / f"{session_id}.json"
        try:
            history_file.unlink()
            return True
        except Exception:
            return False
    
    def search_sessions(self, query: str) -> List[Dict[str, Any]]:
        """Search sessions by query."""
        all_sessions = self.list_sessions()
        query_lower = query.lower()
        
        return [
            session for session in all_sessions
            if (query_lower in session["id"].lower() or
                query_lower in session["summary"].lower() or
                query_lower in session["timestamp"].lower())
        ]
    
    def _generate_summary(self, messages: List[Dict]) -> str:
        """Generate a summary of the conversation."""
        if not messages:
            return "Empty session"
        
        # Get first few non-system messages as summary
        summary_parts = []
        for msg in messages:
            if msg.get("role") != "system" and len(summary_parts) < 3:
                content = msg.get("content", "")
                # Take first 50 chars
                summary = content[:50] + "..." if len(content) > 50 else content
                summary_parts.append(summary)
        
        return " | ".join(summary_parts) if summary_parts else "Short session"


class HistoryBrowser(Static):
    """Widget to browse conversation history."""
    
    # Reactive state
    is_browsing: reactive[bool] = reactive(False)
    search_query: reactive[str] = reactive("")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history_manager = HistoryManager()
    
    def compose(self) -> ComposeResult:
        """Create history browser widgets."""
        with Vertical(classes="history-container"):
            yield Static("Conversation History", classes="history-title")
            yield Input(placeholder="Search history...", id="history-search", classes="history-search")
            yield ListView(id="history-list", classes="history-list")
            with Horizontal(classes="history-actions"):
                yield Button("Refresh", variant="default", id="refresh-btn")
                yield Button("Delete", variant="error", id="delete-btn")
                yield Button("Close", variant="primary", id="close-btn")
    
    def on_mount(self) -> None:
        """Load history when mounted."""
        self.load_history()
    
    def load_history(self):
        """Load and display history."""
        history_list = self.query_one("#history-list", ListView)
        history_list.clear()
        
        sessions = self.history_manager.list_sessions()
        
        for session in sessions:
            session_item = self._create_session_item(session)
            history_list.append(session_item)
    
    def _create_session_item(self, session: Dict[str, Any]) -> ListItem:
        """Create a list item for a session."""
        timestamp = datetime.fromisoformat(session["timestamp"]).strftime("%m/%d %H:%M") if session["timestamp"] else "Unknown"
        content = f"[b]{session['id']}[/b]\n[dim]Messages: {session['message_count']} | {timestamp}[/dim]\n[italic]{session['summary'][:60]}...[/italic]"
        
        item = ListItem(Static(content), id=f"session-{session['id']}")
        return item
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self.search_query = event.value
        self.filter_history(self.search_query)
    
    def filter_history(self, query: str):
        """Filter history based on search query."""
        history_list = self.query_one("#history-list", ListView)
        history_list.clear()
        
        if query.strip():
            sessions = self.history_manager.search_sessions(query)
        else:
            sessions = self.history_manager.list_sessions()
        
        for session in sessions:
            session_item = self._create_session_item(session)
            history_list.append(session_item)


class HistoryViewer(Static):
    """Widget to view a single conversation history."""
    
    def __init__(self, session_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = session_id
        self.history_manager = HistoryManager()
    
    def compose(self) -> ComposeResult:
        """Create history viewer widgets."""
        with Vertical(classes="viewer-container"):
            yield Static(f"Session: {self.session_id}", classes="viewer-title")
            yield ScrollableContainer(id="message-container", classes="message-container")
            with Horizontal(classes="viewer-actions"):
                yield Button("Replay", variant="primary", id="replay-btn")
                yield Button("Back to Browse", variant="default", id="back-btn")
                yield Button("Delete", variant="error", id="delete-btn")
    
    def on_mount(self) -> None:
        """Load conversation when mounted."""
        self.load_conversation(self.session_id)
    
    def load_conversation(self, session_id: str):
        """Load and display a conversation."""
        conversation_data = self.history_manager.load_conversation(session_id)
        messages = conversation_data.get("messages", [])
        
        message_container = self.query_one("#message-container", ScrollableContainer)
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # Create message widget
            if role == "user":
                message_widget = Static(f"[bold blue]USER:[/bold blue] {content}", classes="user-message")
            elif role == "assistant":
                message_widget = Static(f"[bold green]ORBY:[/bold green] {content}", classes="agent-message")
            else:
                message_widget = Static(f"[bold yellow]{role.upper()}:[/bold yellow] {content}", classes="other-message")
            
            message_container.mount(message_widget)