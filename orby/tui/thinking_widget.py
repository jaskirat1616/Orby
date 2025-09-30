"""Thinking mode animation widget for Orby TUI."""
from textual.widget import Widget
from textual.reactive import reactive
from textual import events
from textual.geometry import Size
from rich.text import Text
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.align import Align
from rich.color import Color
import time
import math
from typing import Optional


class ThinkingAnimation(Widget):
    """Animated thinking display for Orby."""
    
    # Reactive state
    is_thinking: reactive[bool] = reactive(False)
    animation_frame: reactive[int] = reactive(0)
    message: reactive[str] = reactive("Orby is thinking...")
    
    def __init__(self, message: str = "Orby is thinking...", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
        self.console = Console()
        self.animation_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.color_cycle = [
            "blue", "cyan", "magenta", "yellow", "green", 
            "bright_blue", "bright_cyan", "bright_magenta", 
            "bright_yellow", "bright_green"
        ]
    
    def on_mount(self) -> None:
        """Start animation when mounted."""
        self.set_interval(0.1, self._animate)
    
    def _animate(self) -> None:
        """Update animation frame."""
        if self.is_thinking:
            self.animation_frame += 1
        else:
            self.animation_frame = 0
    
    def render(self) -> RenderableType:
        """Render the thinking animation."""
        if not self.is_thinking:
            return ""
        
        # Calculate animation state
        frame_idx = self.animation_frame % len(self.animation_chars)
        color_idx = (self.animation_frame // 3) % len(self.color_cycle)  # Change color every 3 frames
        
        spinner_char = self.animation_chars[frame_idx]
        color = self.color_cycle[color_idx]
        
        # Create ASCII art for thinking mode
        thinking_art = f"""
    ╔══════════════════════╗
    ║      🤖🧠💭         ║
    ║   {spinner_char} THINKING {spinner_char}    ║
    ║      ████████        ║
    ║     ██      ██       ║
    ║     ██████████       ║
    ║                      ║
    ╚══════════════════════╝
        """
        
        # Create the text with the message
        text_content = Text(f"\n{thinking_art}\n{self.message}\n", justify="center")
        text_content.stylize(color, 0, len(text_content.plain))
        
        # Create a panel with the thinking animation
        panel = Panel(
            Align.center(text_content),
            title="[bold blue]ORBY THINKING[/bold blue]",
            border_style=color,
            expand=False,
            width=min(60, self.size.width - 4) if hasattr(self, 'size') else 60
        )
        
        return panel
    
    def start_thinking(self, message: str = None):
        """Start the thinking animation."""
        if message:
            self.message = message
        self.is_thinking = True
    
    def stop_thinking(self):
        """Stop the thinking animation."""
        self.is_thinking = False
        self.animation_frame = 0


class ThinkingStatus(Widget):
    """Simple thinking status indicator."""
    
    is_thinking: reactive[bool] = reactive(False)
    message: reactive[str] = reactive("Processing...")
    
    def render(self) -> RenderableType:
        """Render simple thinking status."""
        if not self.is_thinking:
            return ""
        
        # Create a simple animated status
        dots = "." * ((self.app.time % 4) + 1)  # Cycle through 1-4 dots
        status_text = f"[bold yellow]⏳ {self.message}{dots}[/bold yellow]"
        
        return Panel(
            Align.center(Text(status_text)),
            border_style="yellow",
            expand=False
        )