"""Live mode system for Orby."""
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from datetime import datetime


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events."""
    
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        super().__init__()
    
    def on_modified(self, event):
        if not event.is_directory:
            self.callback("modified", event.src_path)
    
    def on_created(self, event):
        if not event.is_directory:
            self.callback("created", event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.callback("deleted", event.src_path)


class LiveModeManager:
    """Manages live mode for Orby."""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.observer = Observer()
        self.handler = None
        self.is_running = False
        self.callbacks: List[Callable[[str, str, str], None]] = []
        self.ignored_patterns = ['.git', '__pycache__', '.orby', '.DS_Store']
    
    def _should_ignore(self, file_path: str) -> bool:
        """Check if a file should be ignored."""
        path_obj = Path(file_path)
        
        # Check if any part of the path matches ignored patterns
        for part in path_obj.parts:
            if part in self.ignored_patterns:
                return True
        
        return False
    
    def _on_file_change(self, event_type: str, file_path: str):
        """Handle file change events."""
        if self._should_ignore(file_path):
            return
        
        # Get file extension for context
        path_obj = Path(file_path)
        file_extension = path_obj.suffix.lower()
        
        # Call all registered callbacks
        for callback in self.callbacks:
            try:
                callback(event_type, file_path, file_extension)
            except Exception:
                # Ignore exceptions in callbacks
                pass
    
    def register_callback(self, callback: Callable[[str, str, str], None]):
        """Register a callback for file changes."""
        self.callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[str, str, str], None]):
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def start_monitoring(self):
        """Start monitoring file changes."""
        if self.is_running:
            return
        
        self.handler = FileChangeHandler(self._on_file_change)
        self.observer.schedule(self.handler, str(self.project_path), recursive=True)
        self.observer.start()
        self.is_running = True
    
    def stop_monitoring(self):
        """Stop monitoring file changes."""
        if not self.is_running:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_running = False


class LiveSuggestions:
    """Provides live suggestions based on file changes."""
    
    def __init__(self, live_manager: LiveModeManager):
        self.live_manager = live_manager
        self.suggestion_callbacks: List[Callable[[str], None]] = []
        
        # Register ourselves as a callback
        self.live_manager.register_callback(self._handle_file_change)
    
    def _handle_file_change(self, event_type: str, file_path: str, file_extension: str):
        """Handle file changes and generate suggestions."""
        suggestion = self._generate_suggestion(event_type, file_path, file_extension)
        if suggestion:
            # Call all suggestion callbacks
            for callback in self.suggestion_callbacks:
                try:
                    callback(suggestion)
                except Exception:
                    # Ignore exceptions in callbacks
                    pass
    
    def _generate_suggestion(self, event_type: str, file_path: str, file_extension: str) -> Optional[str]:
        """Generate a suggestion based on file change."""
        path_obj = Path(file_path)
        file_name = path_obj.name
        
        if event_type == "created":
            if file_extension in ['.py', '.js', '.ts']:
                return f"Consider adding documentation to your new {file_extension} file: {file_name}"
            elif file_extension in ['.md']:
                return f"Review your new markdown file for clarity and completeness: {file_name}"
        elif event_type == "modified":
            if file_extension in ['.py', '.js', '.ts']:
                return f"Consider running tests for your updated {file_extension} file: {file_name}"
            elif file_extension in ['.css', '.scss']:
                return f"Check browser for styling updates in: {file_name}"
            elif file_extension in ['.html']:
                return f"Review your HTML changes in: {file_name}"
        elif event_type == "deleted":
            return f"File deleted: {file_name}. Check if references to it need updating."
        
        return None
    
    def register_suggestion_callback(self, callback: Callable[[str], None]):
        """Register a callback for suggestions."""
        self.suggestion_callbacks.append(callback)
    
    def unregister_suggestion_callback(self, callback: Callable[[str], None]):
        """Unregister a suggestion callback."""
        if callback in self.suggestion_callbacks:
            self.suggestion_callbacks.remove(callback)


# Global live mode manager instance
live_mode_manager = LiveModeManager()
live_suggestions = LiveSuggestions(live_mode_manager)