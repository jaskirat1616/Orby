"""Textual-based TUI application for Orby with world-class interface."""
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, TextArea, 
    ListView, ListItem, Label, DataTable, TabbedContent, TabPane
)
from textual.binding import Binding
from textual.reactive import reactive
from textual.css.query import DOMQuery
from textual import events
from datetime import datetime
import asyncio
from typing import Optional
from ..core import OrbyApp
from ..memory import memory_system
from ..config import load_config
from ..prompt_manager import PromptManager
from ..ui.enhanced_ui import ui as enhanced_ui
from .themes import ThemeManager
from .command_palette import CommandPalette
from .history import HistoryManager, HistoryBrowser


# Import system info - fallback if psutil is not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class OrbyTUI(App):
    """Main Textual application for Orby with enhanced TUI experience."""
    
    # CSS classes for styling
    CSS_PATH = "orby_tui.css"
    
    # Key bindings
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "command_palette", "Command Palette"),
        Binding("ctrl+t", "toggle_split", "Toggle Split View"),
        Binding("ctrl+d", "dashboard", "Dashboard"),
        Binding("ctrl+m", "toggle_memory", "Toggle Memory"),
        Binding("f1", "help", "Help"),
        Binding("f2", "themes", "Themes"),
        Binding("f3", "history", "History"),
        Binding("escape", "cancel_thinking", "Cancel"),
    ]
    
    # Reactive state variables
    current_model: reactive[str] = reactive("llama3.1:latest")
    current_profile: reactive[str] = reactive("default")
    current_prompt: reactive[str] = reactive("")
    memory_enabled: reactive[bool] = reactive(True)
    is_thinking: reactive[bool] = reactive(False)
    chat_history: reactive[list] = reactive([])
    
    def __init__(self):
        super().__init__()
        self.app_core = OrbyApp()
        self.config = load_config()
        self.prompt_manager = PromptManager()
        
        # Initialize state from config
        self.current_model = self.config.get('default_model', 'llama3.1:latest')
        self.current_profile = self.config.get('profile', 'default')
        self.current_prompt = self.prompt_manager.load_system_prompt() or ""
        
        # Initialize theme
        self.current_theme = self.config.get('tui_theme', 'default')
        self.theme_manager = ThemeManager()
        
        # Apply the initial theme
        self.apply_theme(self.current_theme)
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        with Horizontal(id="main-container"):
            yield OrbyConversationPane(id="conversation")
            yield OrbyToolsPane(id="tools")
        
        yield OrbyStatusFooter(id="footer")
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "Orby - Local AI Assistant"
        self.sub_title = "World-Class Terminal Experience"
        
        # Initialize dashboard data
        self.query_one("#dashboard", OrbyDashboard).update_dashboard()
    
    def action_command_palette(self) -> None:
        """Open command palette."""
        self.call_next(self.show_command_palette)
    
    def action_toggle_split(self) -> None:
        """Toggle between single and split view."""
        tools_pane = self.query_one("#tools", OrbyToolsPane)
        conversation = self.query_one("#conversation", OrbyConversationPane)
        
        tools_pane.visible = not tools_pane.visible
        
        if tools_pane.visible:
            # Split view - conversation on left, tools on right
            conversation.styles.width = "50%"
            tools_pane.styles.width = "50%"
        else:
            # Single view - full width for conversation
            conversation.styles.width = "100%"
            tools_pane.styles.width = "0%"
    
    def action_dashboard(self) -> None:
        """Show dashboard view."""
        pass
    
    def action_toggle_memory(self) -> None:
        """Toggle memory functionality."""
        memory_system.set_memory_enabled(not memory_system.memory_enabled)
        self.notify(f"Memory {'enabled' if memory_system.memory_enabled else 'disabled'}")
    
    def action_help(self) -> None:
        """Show help."""
        pass
    
    def action_themes(self) -> None:
        """Show theme selection."""
        pass
    
    def action_history(self) -> None:
        """Show history."""
        pass
    
    def on_resize(self, event: events.Resize) -> None:
        """Handle terminal resize events."""
        # Update UI elements based on new size
        self.update_responsive_layout(event.size.width, event.size.height)
    
    def update_responsive_layout(self, width: int, height: int) -> None:
        """Update layout based on terminal dimensions."""
        # Adjust tools panel visibility based on width
        tools_pane = self.query_one("#tools", OrbyToolsPane)
        
        if width < 80:
            # Hide tools panel on narrow terminals
            tools_pane.styles.display = "none"
        elif width < 120:
            # Make tools panel narrow on medium-width terminals
            tools_pane.styles.width = "30"
            tools_pane.styles.display = "block"
        else:
            # Show full tools panel on wide terminals
            tools_pane.styles.width = "40"
            tools_pane.styles.display = "block"
        
        # Adjust dashboard panels for different heights
        if height < 30:
            # Compact dashboard for short terminals
            dashboard = self.query_one("#dashboard", OrbyDashboard)
            dashboard.styles.height = "8"
        else:
            # Normal dashboard for taller terminals
            dashboard = self.query_one("#dashboard", OrbyDashboard)
            dashboard.styles.height = "12"

    def action_themes(self) -> None:
        """Show theme selection."""
        # Cycle through themes for now
        themes = self.theme_manager.get_available_themes()
        current_idx = themes.index(self.current_theme) if self.current_theme in themes else 0
        next_idx = (current_idx + 1) % len(themes)
        next_theme = themes[next_idx]
        
        self.apply_theme(next_theme)
        self.notify(f"Theme changed to: {next_theme}")

    def show_command_palette(self) -> None:
        """Show command palette overlay."""
        # Create and mount the command palette
        palette = CommandPalette(id="command-palette", classes="command-palette-overlay")
        self.mount(palette)
        
        # Focus the palette
        palette.focus()
    
    def apply_theme(self, theme_name: str) -> None:
        """Apply a color theme to the application."""
        success = self.theme_manager.apply_theme(self, theme_name)
        if success:
            self.current_theme = theme_name
            # Save to config
            self.config['tui_theme'] = theme_name
            # Update UI to reflect theme change
            self.refresh()


class OrbyDashboard(Static):
    """Dashboard showing session info and status."""
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("ORBY", classes="title")
        yield Static("Local-first AI CLI with agentic powers", classes="subtitle")
        
        with Horizontal(classes="dashboard-container"):
            yield OrbyStatusPanel(id="status-panel")
            yield OrbyMemoryPanel(id="memory-panel")
            yield OrbyModelPanel(id="model-panel")

    def update_dashboard(self) -> None:
        """Update dashboard information."""
        # Update each panel with current data
        status_panel = self.query_one("#status-panel", OrbyStatusPanel)
        memory_panel = self.query_one("#memory-panel", OrbyMemoryPanel)
        model_panel = self.query_one("#model-panel", OrbyModelPanel)
        
        status_panel.refresh()
        memory_panel.refresh()
        model_panel.refresh()


class OrbyStatusPanel(Static):
    """Panel showing current session status."""
    
    def __init__(self):
        super().__init__()
        self.app_core = OrbyApp()
        self.config = load_config()
        self.prompt_manager = PromptManager()
    
    def compose(self) -> ComposeResult:
        """Create status panel widgets."""
        yield Label("Session Status", classes="panel-title")
        yield Static("", id="model-status", classes="status-item")
        yield Static("", id="profile-status", classes="status-item")
        yield Static("", id="connection-status", classes="status-item")
        yield Static("", id="memory-status", classes="status-item")
        yield Static("", id="system-prompt-preview", classes="prompt-preview")
    
    def on_mount(self) -> None:
        """Update status when mounted."""
        self.update_status()
    
    def update_status(self) -> None:
        """Update all status information."""
        # Get current values
        model = self.config.get('default_model', 'llama3.1:latest')
        profile = self.config.get('profile', 'default') 
        backend = self.config.get('default_backend', 'ollama')
        memory_enabled = memory_system.memory_enabled
        system_prompt = self.prompt_manager.load_system_prompt()
        
        # Update widgets
        self.query_one("#model-status", Static).update(f"Model: [b]{model}[/b]")
        self.query_one("#profile-status", Static).update(f"Profile: [b]{profile}[/b]")
        self.query_one("#connection-status", Static).update(f"Backend: [b]{backend}[/b]")
        self.query_one("#memory-status", Static).update(f"Memory: [b]{'enabled' if memory_enabled else 'disabled'}[/b]")
        
        # Show preview of system prompt
        preview_text = system_prompt[:60] + "..." if system_prompt and len(system_prompt) > 60 else (system_prompt or "No system prompt")
        self.query_one("#system-prompt-preview", Static).update(f"Prompt: [i]{preview_text}[/i]")


class OrbyMemoryPanel(Static):
    """Panel showing memory information."""
    
    def compose(self) -> ComposeResult:
        """Create memory panel widgets."""
        yield Label("Memory Stats", classes="panel-title")
        yield Static("", id="ephemeral-count", classes="memory-stat")
        yield Static("", id="persistent-count", classes="memory-stat")
        yield Static("", id="context-size", classes="memory-stat")
        yield Static("", id="memory-usage-bar", classes="usage-bar")
        yield Static("", id="recent-entries", classes="recent-entries")
    
    def on_mount(self) -> None:
        """Update memory stats when mounted."""
        self.update_memory_stats()
    
    def update_memory_stats(self) -> None:
        """Update memory statistics."""
        try:
            stats = memory_system.get_memory_stats()
            
            ephemeral = stats.get('ephemeral_entries', 0)
            persistent = stats.get('persistent_entries', 0)
            context = memory_system.get_context(max_entries=5)  # Get last 5 entries for context preview
            
            self.query_one("#ephemeral-count", Static).update(f"Ephemeral: [b]{ephemeral}[/b] entries")
            self.query_one("#persistent-count", Static).update(f"Persistent: [b]{persistent}[/b] entries")
            self.query_one("#context-size", Static).update(f"Active Context: [b]{len(context)}[/b] items")
            
            # Show usage bar
            total_entries = ephemeral + persistent
            usage_percent = min(100, (total_entries / 100) * 100 if total_entries < 100 else 100)  # Cap at 100%
            bar_length = 20
            filled = int(bar_length * usage_percent / 100)
            bar = "[" + "█" * filled + "░" * (bar_length - filled) + f"] {usage_percent:.0f}%"
            self.query_one("#memory-usage-bar", Static).update(bar)
            
            # Show recent entries preview
            if context.strip():
                # Show first few lines as preview
                preview = context[:200] + "..." if len(context) > 200 else context
                self.query_one("#recent-entries", Static).update(f"[i]Recent context preview:[/i]\n{preview}")
            else:
                self.query_one("#recent-entries", Static).update("[i]No recent memory entries[/i]")
                
        except Exception as e:
            self.query_one("#ephemeral-count", Static).update(f"Ephemeral: [red]Error[/red]")
            self.query_one("#persistent-count", Static).update(f"Persistent: [red]Error[/red]")
            self.query_one("#context-size", Static).update(f"Context: [red]Error[/red]")


class OrbyModelPanel(Static):
    """Panel showing model information."""
    
    def __init__(self):
        super().__init__()
        self.app_core = OrbyApp()
    
    def compose(self) -> ComposeResult:
        """Create model panel widgets."""
        yield Label("Active Model", classes="panel-title")
        yield Static("", id="model-name", classes="model-info")
        yield Static("", id="model-backend", classes="model-info")
        yield Static("", id="model-status", classes="model-info")
        yield Static("", id="model-stats", classes="model-stats")
        yield Static("", id="available-models", classes="available-models")
    
    def on_mount(self) -> None:
        """Update model info when mounted."""
        self.update_model_info()
    
    def update_model_info(self) -> None:
        """Update model information."""
        try:
            config = load_config()
            model_name = config.get('default_model', 'llama3.1:latest')
            backend = config.get('default_backend', 'ollama')
            
            # Get model statistics
            # For now, just show basic info - would integrate with actual model stats
            available_models = self.app_core.get_available_models()
            
            self.query_one("#model-name", Static).update(f"Name: [b]{model_name}[/b]")
            self.query_one("#model-backend", Static).update(f"Backend: [b]{backend}[/b]")
            self.query_one("#model-status", Static).update(f"Status: [b]Ready[/b]")
            self.query_one("#model-stats", Static).update(f"Loaded: [b]Yes[/b]")
            
            # Show available models
            model_count = sum(len(models) for models in available_models.values()) if available_models else 0
            self.query_one("#available-models", Static).update(f"Available: [b]{model_count}[/b] models")
            
        except Exception as e:
            self.query_one("#model-name", Static).update(f"Name: [red]Error[/red]")
            self.query_one("#model-backend", Static).update(f"Backend: [red]Error[/red]")
            self.query_one("#model-status", Static).update(f"Status: [red]Error[/red]")


from .thinking_widget import ThinkingAnimation, ThinkingStatus


class OrbyConversationPane(Static):
    """Main conversation panel with chat interface."""
    
    def compose(self) -> ComposeResult:
        """Create conversation widgets."""
        with Vertical(classes="chat-container"):
            yield ScrollableContainer(id="chat-history", classes="chat-history")
            yield ThinkingAnimation(id="thinking-animation")
            with Horizontal(classes="input-container"):
                yield Input(placeholder="Type your message here...", id="user-input", classes="message-input")
                yield Button("Send", variant="primary", id="send-btn", classes="send-btn")

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat history and update memory."""
        chat_history = self.query_one("#chat-history", ScrollableContainer)
        message_class = "user-message" if role == "user" else "agent-message"
        
        message_widget = Static(f"[{role.upper()}] {content}", classes=message_class)
        chat_history.mount(message_widget)
        chat_history.scroll_end(animate=False)
        
        # Add to memory system
        try:
            if hasattr(memory_system, 'add_to_session_memory'):
                memory_system.add_to_session_memory(
                    content=content,
                    content_type="chat_message",
                    tags=[role],
                    importance=1.0 if role == "user" else 0.8,
                    metadata={"role": role, "timestamp": str(datetime.now())}
                )
        except Exception as e:
            # Silently fail if memory system has issues
            pass
    
    def start_thinking(self, message: str = "Orby is thinking..."):
        """Show thinking animation."""
        thinking_widget = self.query_one("#thinking-animation", ThinkingAnimation)
        thinking_widget.start_thinking(message)
    
    def stop_thinking(self):
        """Hide thinking animation."""
        thinking_widget = self.query_one("#thinking-animation", ThinkingAnimation)
        thinking_widget.stop_thinking()


class OrbyToolsPane(Static):
    """Panel showing tools and their status."""
    
    def __init__(self):
        super().__init__()
        self.app_core = OrbyApp()
        self.history_manager = HistoryManager()
    
    def compose(self) -> ComposeResult:
        """Create tools panel widgets."""
        yield Label("Tools & Context", classes="panel-title")
        
        with TabbedContent():
            with TabPane("Tools", id="tools-tab"):
                yield ListView(id="available-tools-list")
            with TabPane("Memory", id="memory-tab"):
                yield Static("Active Memory Context", classes="context-title")
                yield ScrollableContainer(id="memory-context-container", classes="memory-context")
            with TabPane("History", id="history-tab"):
                yield Static("Recent Sessions", classes="history-title")
                yield ListView(id="history-list", classes="history-list-container")
                with Horizontal(classes="history-actions"):
                    yield Button("Refresh", id="refresh-history", classes="history-btn")
            with TabPane("System", id="system-tab"):
                yield Static("System Information", classes="system-title")
                yield Static(id="system-info")
    
    def on_mount(self) -> None:
        """Populate tools and memory context when mounted."""
        self.update_tools_list()
        self.update_memory_context()
        self.update_system_info()
        self.update_history_list()
    
    def update_tools_list(self) -> None:
        """Update the list of available tools."""
        try:
            tools_list = self.query_one("#available-tools-list", ListView)
            tools_list.clear()
            
            # Get available tools from the registry
            available_tools = []
            if self.app_core.tools:
                available_tools = self.app_core.tools.list_tools()
            
            for tool_name in available_tools:
                tool_instance = self.app_core.tools.get_tool(tool_name)
                if tool_instance:
                    description = getattr(tool_instance, 'description', 'No description')
                    tools_list.append(ListItem(Static(f"🔧 {tool_name}\n[dim]{description}[/dim]", classes="tool-item")))
                else:
                    tools_list.append(ListItem(Static(f"🔧 {tool_name}", classes="tool-item")))
            
            if not available_tools:
                tools_list.append(ListItem(Static("[i]No tools available[/i]", classes="no-tools")))
                
        except Exception as e:
            tools_list = self.query_one("#available-tools-list", ListView)
            tools_list.clear()
            tools_list.append(ListItem(Static(f"[red]Error loading tools: {str(e)}[/red]", classes="error-item")))
    
    def update_memory_context(self) -> None:
        """Update the memory context display."""
        try:
            context_container = self.query_one("#memory-context-container", ScrollableContainer)
            # Clear existing widgets
            for child in context_container.children:
                child.remove()
            
            # Get recent memory entries
            context = memory_system.get_context(max_entries=10)
            
            if context.strip():
                # Split context into lines and add each as a separate widget
                lines = context.split('\n')
                for line in lines:
                    if line.strip():
                        context_container.mount(Static(f"📝 {line}", classes="context-line"))
            else:
                context_container.mount(Static("[i]No active memory context[/i]", classes="no-context"))
                
        except Exception as e:
            context_container = self.query_one("#memory-context-container", ScrollableContainer)
            context_container.mount(Static(f"[red]Error loading context: {str(e)}[/red]"))
    
    def update_system_info(self) -> None:
        """Update system information."""
        try:
            import platform
            
            if HAS_PSUTIL:
                system_info = f"""
OS: {platform.system()} {platform.release()}
Python: {platform.python_version()}
CPU: {psutil.cpu_percent()}% usage
Memory: {psutil.virtual_memory().percent}% used
Disk: {psutil.disk_usage('/').percent}% used
Orby Version: 0.1.0
                """.strip()
            else:
                # Fallback without psutil
                system_info = f"""
OS: {platform.system()} {platform.release()}
Python: {platform.python_version()}
Orby Version: 0.1.0
[bold yellow]Install psutil for full system stats[/bold yellow]
                """.strip()
            
            self.query_one("#system-info", Static).update(system_info)
            
        except Exception as e:
            self.query_one("#system-info", Static).update(f"[red]Error getting system info: {str(e)}[/red]")

    def update_history_list(self) -> None:
        """Update the history list."""
        try:
            history_list = self.query_one("#history-list", ListView)
            history_list.clear()
            
            sessions = self.history_manager.list_sessions()
            
            for i, session in enumerate(sessions[:10]):  # Show only first 10 for performance
                timestamp = datetime.fromisoformat(session["timestamp"]).strftime("%m/%d %H:%M") if session["timestamp"] else "Unknown"
                content = f"[b]{session['id']}[/b] - {session['message_count']} messages ({timestamp})"
                
                item = ListItem(Static(content), id=f"history-{i}")
                history_list.append(item)
                
        except Exception as e:
            history_list = self.query_one("#history-list", ListView)
            history_list.clear()
            history_list.append(ListItem(Static(f"[red]Error loading history: {str(e)}[/red]")))


class OrbyStatusFooter(Static):
    """Status footer showing current state."""
    
    def compose(self) -> ComposeResult:
        """Create footer widgets."""
        with Horizontal(classes="status-footer"):
            yield Static("Ready", id="status-indicator", classes="status-ready")
            yield Static("", id="current-action", classes="current-action")


# Create the main app instance
orby_tui = OrbyTUI()