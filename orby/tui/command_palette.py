"""Command palette widget for Orby TUI."""
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, ListView, ListItem
from textual import events
from textual.reactive import reactive
from textual.message import Message
from typing import List, Dict, Callable
from ...config import load_config, save_config


class CommandPalette(Static):
    """Command palette overlay for quick actions."""
    
    # Reactive state
    is_open: reactive[bool] = reactive(False)
    current_filter: reactive[str] = reactive("")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = self._get_available_commands()
    
    def compose(self) -> ComposeResult:
        """Create command palette widgets."""
        with Vertical(classes="palette-container"):
            yield Static("Orby Command Palette", classes="palette-title")
            yield Input(placeholder="Type command or search...", id="command-input", classes="command-input")
            yield ListView(id="command-list", classes="command-list")
    
    def _get_available_commands(self) -> List[Dict]:
        """Get list of available commands."""
        return [
            {"id": "set-model", "name": "Set Model", "description": "Change the active model", "action": self.set_model_command},
            {"id": "switch-profile", "name": "Switch Profile", "description": "Change the active profile", "action": self.switch_profile_command},
            {"id": "save-session", "name": "Save Session", "description": "Save the current session", "action": self.save_session_command},
            {"id": "load-session", "name": "Load Session", "description": "Load a saved session", "action": self.load_session_command},
            {"id": "toggle-memory", "name": "Toggle Memory", "description": "Enable/disable memory", "action": self.toggle_memory_command},
            {"id": "set-prompt", "name": "Set System Prompt", "description": "Set the system prompt", "action": self.set_prompt_command},
            {"id": "clear-chat", "name": "Clear Chat", "description": "Clear current chat history", "action": self.clear_chat_command},
            {"id": "toggle-theme", "name": "Toggle Theme", "description": "Switch between themes", "action": self.toggle_theme_command},
            {"id": "show-history", "name": "Show History", "description": "Browse conversation history", "action": self.show_history_command},
            {"id": "quit-app", "name": "Quit", "description": "Exit the application", "action": self.quit_command},
        ]
    
    def on_mount(self) -> None:
        """Set up command palette when mounted."""
        self.filter_commands("")
        
        # Focus the input field
        self.query_one("#command-input", Input).focus()
    
    def filter_commands(self, filter_text: str = ""):
        """Filter commands based on text."""
        self.current_filter = filter_text.lower()
        filtered_commands = [
            cmd for cmd in self.commands 
            if self.current_filter in cmd["name"].lower() or 
               self.current_filter in cmd["description"].lower()
        ]
        
        # Update the list
        command_list = self.query_one("#command-list", ListView)
        command_list.clear()
        
        for cmd in filtered_commands:
            item = ListItem(
                Static(f"{cmd['name']} - [dim]{cmd['description']}[/dim]", classes="command-item"),
                id=f"cmd-{cmd['id']}"
            )
            command_list.append(item)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input change to filter commands."""
        self.filter_commands(event.value)
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle command selection."""
        cmd_id = event.item.id.replace("cmd-", "")
        for cmd in self.commands:
            if cmd["id"] == cmd_id:
                cmd["action"]()
                break
        
        # Close the command palette after action
        self.is_open = False
        self.remove()
    
    def set_model_command(self) -> None:
        """Command to set model."""
        # This would open a model picker, for now just notify
        self.app.notify("Set Model command selected")
    
    def switch_profile_command(self) -> None:
        """Command to switch profile."""
        self.app.notify("Switch Profile command selected")
    
    def save_session_command(self) -> None:
        """Command to save session."""
        self.app.notify("Save Session command selected")
    
    def load_session_command(self) -> None:
        """Command to load session."""
        self.app.notify("Load Session command selected")
    
    def toggle_memory_command(self) -> None:
        """Command to toggle memory."""
        from ..memory import memory_system
        memory_system.set_memory_enabled(not memory_system.memory_enabled)
        status = "enabled" if memory_system.memory_enabled else "disabled"
        self.app.notify(f"Memory {status}")
    
    def set_prompt_command(self) -> None:
        """Command to set system prompt."""
        self.app.notify("Set System Prompt command selected")
    
    def clear_chat_command(self) -> None:
        """Command to clear chat."""
        self.app.notify("Clear Chat command selected")
    
    def toggle_theme_command(self) -> None:
        """Command to toggle theme."""
        from .themes import ThemeManager
        themes = ThemeManager.get_available_themes()
        current_idx = themes.index(self.app.current_theme) if hasattr(self.app, 'current_theme') else 0
        next_idx = (current_idx + 1) % len(themes)
        next_theme = themes[next_idx]
        
        if hasattr(self.app, 'apply_theme'):
            self.app.apply_theme(next_theme)
            self.app.notify(f"Theme changed to: {next_theme}")
    
    def show_history_command(self) -> None:
        """Command to show history."""
        self.app.notify("Show History command selected")
    
    def quit_command(self) -> None:
        """Command to quit."""
        self.app.exit()


class QuickActionCommandPalette(CommandPalette):
    """Simplified version for quick actions."""
    
    def __init__(self, quick_commands: List[Dict] = None, *args, **kwargs):
        self.quick_commands = quick_commands or []
        super().__init__(*args, **kwargs)
    
    def _get_available_commands(self) -> List[Dict]:
        """Get available commands, prioritizing quick commands."""
        base_commands = super()._get_available_commands()
        return self.quick_commands + base_commands