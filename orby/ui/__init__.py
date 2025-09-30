"""UI components for Orby with Gemini/Anthropic-like interface."""
import asyncio
from typing import List, Dict, Any, Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint
from rich.rule import Rule
from rich.spinner import Spinner
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.box import ROUNDED
import time
from datetime import datetime
from ..prompt_manager import PromptManager


class OrbyUI:
    """Main UI class for Orby with premium interface."""
    
    def __init__(self):
        self.console = Console()
        self.spinner = Spinner("dots", style="green")
        self.prompt_manager = PromptManager()
    
    def show_header(self):
        """Show the main header."""
        header_text = Text("ORBY", style="bold blue")
        header_text.append("\nLocal-first AI CLI with agentic powers", style="dim")
        
        self.console.print(Panel(
            header_text,
            border_style="blue",
            expand=False
        ))
    
    def show_status_bar(self, backend: str = "ollama", model: str = "llama3.1:latest"):
        """Show status bar with current settings."""
        status_text = f"[bold green]Connected:[/bold green] {backend} | [bold yellow]Model:[/bold yellow] {model}"
        self.console.print(Panel(status_text, style="green", border_style="green", expand=False))
    
    def show_user_message(self, content: str):
        """Display user message in a panel."""
        prefix = Text("> ", style="bold blue")
        user_text = Text(content)
        message = Group(prefix, user_text)
        
        self.console.print(Panel(
            message,
            title="[bold blue]You[/bold blue]",
            border_style="blue",
            expand=False
        ))
    
    def show_agent_message(self, content: str):
        """Display agent message in a panel."""
        prefix = Text("✦ ", style="bold green")
        agent_text = Text(content)
        message = Group(prefix, agent_text)
        
        self.console.print(Panel(
            message,
            title="[bold green]Orby[/bold green]",
            border_style="green",
            expand=False
        ))
    
    def show_tool_call(self, tool_name: str, arguments: Dict[str, Any], status: str = "executing"):
        """Display tool call in a panel."""
        status_colors = {
            "pending": "yellow",
            "executing": "cyan", 
            "success": "green",
            "error": "red"
        }
        color = status_colors.get(status, "white")
        
        args_text = "\n".join([f"  {k}: {v}" for k, v in arguments.items()])
        content = f"[bold]{tool_name}[/bold]\n{args_text}"
        
        self.console.print(Panel(
            content,
            title=f"[bold {color}]{status.title()} Tool[/bold {color}]",
            border_style=color,
            expand=False
        ))
    
    def show_tool_result(self, tool_name: str, result: Any, status: str = "success"):
        """Display tool result in a panel."""
        status_colors = {
            "success": "green",
            "error": "red"
        }
        color = status_colors.get(status, "white")
        
        title = f"[bold {color}]Tool Result ({tool_name})[/bold {color}]"
        content = str(result)
        
        self.console.print(Panel(
            content,
            title=title,
            border_style=color,
            expand=False
        ))
    
    def show_models_table(self, models_data: Dict[str, List[str]]):
        """Display available models in a table."""
        table = Table(title="Available Models", show_header=True, header_style="bold magenta")
        table.add_column("Backend", style="cyan", no_wrap=True)
        table.add_column("Models", style="white")
        
        for backend_name, models in models_data.items():
            if models:
                model_list = "\n".join([f"• {model}" for model in models])
                table.add_row(backend_name.upper(), model_list)
            else:
                table.add_row(backend_name.upper(), "[red]No models available[/red]")
        
        self.console.print(table)
    
    def show_help(self):
        """Display help information."""
        table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        
        commands = [
            ("/models", "List all available models"),
            ("/switch <model>", "Switch to a different model"),
            ("/reset", "Reset conversation history"),
            ("/save <name>", "Save current session"),
            ("/load <name>", "Load a saved session"),
            ("/exit", "Exit the chat"),
            ("/help", "Show this help message"),
            ("/auto", "Toggle auto-approve mode"),
        ]
        
        for cmd, desc in commands:
            table.add_row(cmd, desc)
        
        self.console.print(table)
    
    def get_user_input(self, prompt_text: str = "You > ") -> str:
        """Get input from user."""
        return Prompt.ask(f"[bold blue]{prompt_text}[/bold blue]")
    
    def show_confirmation(self, message: str) -> bool:
        """Show confirmation dialog."""
        return Confirm.ask(f"[bold yellow]{message}[/bold yellow]")
    
    async def show_loading(self, message: str = "Processing..."):
        """Show loading indicator."""
        with Live(self.spinner, refresh_per_second=10) as live:
            live.update(Text(message, style="bold green"))
            await asyncio.sleep(1)  # Simulate loading
    
    def show_error(self, message: str):
        """Show error message."""
        self.console.print(Panel(
            f"[bold red]✗[/bold red] {message}",
            border_style="red",
            expand=False
        ))
    
    def show_success(self, message: str):
        """Show success message."""
        self.console.print(Panel(
            f"[bold green]✓[/bold green] {message}",
            border_style="green",
            expand=False
        ))
    
    def show_session_info(self, session_data: Dict[str, Any]):
        """Show session information."""
        info_text = f"Session: {session_data.get('name', 'Untitled')}\n"
        info_text += f"Model: {session_data.get('model', 'Unknown')}\n"
        info_text += f"Created: {session_data.get('created', 'Unknown')}"
        
        self.console.print(Panel(
            info_text,
            title="[bold blue]Session Info[/bold blue]",
            border_style="blue",
            expand=False
        ))
    
    def clear_screen(self):
        """Clear the screen."""
        self.console.clear()
        self.show_header()
    
    def show_system_prompt_info(self, system_prompt: Optional[str] = None):
        """Show system prompt information."""
        if system_prompt is None:
            system_prompt = self.prompt_manager.load_system_prompt()
        
        if system_prompt:
            panel = Panel(
                f"[italic]{system_prompt}[/italic]",
                title="[bold yellow]Active System Prompt[/bold yellow]",
                border_style="yellow",
                expand=False
            )
            self.console.print(panel)
        else:
            panel = Panel(
                "[italic]No system prompt set. Using default behavior.[/italic]",
                title="[bold yellow]System Prompt[/bold yellow]",
                border_style="dim",
                expand=False
            )
            self.console.print(panel)
    
    def show_memory_info(self):
        """Show current memory state."""
        from ..memory import memory_system
        
        try:
            stats = memory_system.get_memory_stats()
            
            memory_info = f"Session ID: {stats['session_id']}\n"
            memory_info += f"Ephemeral entries: {stats['ephemeral_entries']}\n"
            memory_info += f"Persistent entries: {stats['persistent_entries']}\n"
            memory_info += f"Average importance: {stats['average_importance']:.2f}\n"
            
            if stats['content_type_distribution']:
                memory_info += "Content types:\n"
                for content_type, count in stats['content_type_distribution'].items():
                    memory_info += f"  • {content_type}: {count}\n"
            
            panel = Panel(
                f"[italic]{memory_info}[/italic]",
                title="[bold blue]Memory State[/bold blue]",
                border_style="blue",
                expand=False
            )
            self.console.print(panel)
        except Exception:
            panel = Panel(
                "[italic]Memory system not available.[/italic]",
                title="[bold blue]Memory State[/bold blue]",
                border_style="dim",
                expand=False
            )
            self.console.print(panel)