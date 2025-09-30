"""Enhanced UI components for Orby with ASCII art, animations, and thinking mode."""
import asyncio
import time
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
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
from ..prompt_manager import PromptManager

class EnhancedOrbyUI:
    """Enhanced UI class for Orby with premium interface and animations."""
    
    def __init__(self):
        self.console = Console()
        self.spinner = Spinner("dots", style="green")
        self.current_layout = "default"
        self.prompt_manager = PromptManager()
        
        # ASCII art for Orby
        self.orby_ascii = r"""
    ╭─────────────────╮
    │    ██████╗      │
    │   ██╔════╝      │
    │   ███████╗      │
    │   ╚════██║      │
    │   ██████╔╝      │
    │   ╚═════╝       │
    ╰─────────────────╯
        """
        
        # Thinking mode ASCII
        self.thinking_ascii = r"""
    ╭─────────────────╮
    │    🤖🧠💭      │
    │   THINKING...   │
    │    ███████      │
    │   ██     ██     │
    │   █████████     │
    │                 │
    ╰─────────────────╯
        """
    
    def show_header(self, show_system_prompt: bool = True):
        """Show the main header with enhanced ASCII art."""
        if self.current_layout == "tui":
            return  # TUI has its own header

        # Create ASCII art panel
        ascii_panel = Panel(
            self.orby_ascii,
            border_style="blue",
            expand=False,
            title="[bold blue]ORBY[/bold blue]",
            subtitle="[dim]Local-first AI CLI with agentic powers[/dim]"
        )
        
        self.console.print(ascii_panel)
        
        # Show system prompt if available
        if show_system_prompt:
            system_prompt = self.prompt_manager.load_system_prompt()
            if system_prompt:
                prompt_panel = Panel(
                    f"[italic]{system_prompt}[/italic]",
                    border_style="yellow",
                    expand=False,
                    title="[bold yellow]System Prompt[/bold yellow]",
                    subtitle="[dim]Active configuration[/dim]"
                )
                self.console.print(prompt_panel)

    def show_status_bar(self, backend: str = "ollama", model: str = "llama3.1:latest"):
        """Show status bar with current settings and enhanced design."""
        if self.current_layout == "tui":
            return  # TUI handles status differently

        status_text = (
            f"[bold green]Backend:[/bold green] {backend} | "
            f"[bold yellow]Model:[/bold yellow] {model}"
        )
        
        # Check if system prompt is active
        system_prompt = self.prompt_manager.load_system_prompt()
        if system_prompt:
            status_text += " | [bold cyan]System Prompt: Active[/bold cyan]"
        
        self.console.print(Panel(
            status_text,
            style="green",
            border_style="green",
            expand=False
        ))

    def show_thinking_animation(self, message: str = "Orby is thinking..."):
        """Show enhanced thinking animation."""
        # Display thinking ASCII
        thinking_panel = Panel(
            self.thinking_ascii,
            border_style="cyan",
            expand=False,
            title="[bold cyan]THINKING[/bold cyan]"
        )
        
        with Live(thinking_panel, refresh_per_second=10) as live:
            for i in range(3):  # Pulse animation
                live.update(Panel(
                    self.thinking_ascii,
                    border_style="cyan" if i % 2 == 0 else "magenta",
                    expand=False,
                    title=f"[bold {'cyan' if i % 2 == 0 else 'magenta'}]THINKING[/bold {'cyan' if i % 2 == 0 else 'magenta'}]"
                ))
                time.sleep(0.5)
            
            # Show final message
            self.console.print(f"[cyan]⏳ {message}[/cyan]")

    def show_user_message(self, content: str):
        """Display user message in an enhanced panel."""
        if self.current_layout == "tui":
            return  # TUI handles messages differently

        # Create user message with arrow decoration
        prefix = Text("👤 > ", style="bold blue")
        user_text = Text(content)
        message = Group(prefix, user_text)

        self.console.print(Panel(
            message,
            title="[bold blue]You[/bold blue]",
            border_style="blue",
            expand=False
        ))

    def show_agent_message(self, content: str):
        """Display agent message in an enhanced panel."""
        if self.current_layout == "tui":
            return  # TUI handles messages differently

        # Create agent message with Orby decoration
        prefix = Text("🤖 ✦ ", style="bold green")
        agent_text = Text(content)
        message = Group(prefix, agent_text)

        self.console.print(Panel(
            message,
            title="[bold green]Orby[/bold green]",
            border_style="green",
            expand=False
        ))

    def show_tool_call(self, tool_name: str, arguments: Dict[str, Any], status: str = "executing"):
        """Display tool call in a panel with enhanced styling."""
        if self.current_layout == "tui":
            return  # TUI handles tool calls differently

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
        """Display tool result in a panel with enhanced styling."""
        if self.current_layout == "tui":
            return  # TUI handles tool results differently

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
        """Display available models in a table with enhanced styling."""
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

    def show_benchmark_results(self, models_with_scores: List[tuple]):
        """Display model benchmark results with enhanced styling."""
        table = Table(title="Model Benchmark Results", show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Model", style="white")
        table.add_column("Backend", style="green")
        table.add_column("Score", style="yellow")

        for i, (model, score) in enumerate(models_with_scores, 1):
            table.add_row(
                str(i),
                model.name,
                model.backend,
                f"{score:.2f}" if score else "N/A"
            )

        self.console.print(table)

    def show_help(self):
        """Display help information with enhanced formatting."""
        table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")

        commands = [
            ("/models", "List all available models"),
            ("/switch <model>", "Switch to a different model"),
            ("/benchmark", "Benchmark available models"),
            ("/reset", "Reset conversation history"),
            ("/save <name>", "Save current session"),
            ("/load <name>", "Load a saved session"),
            ("/exit", "Exit the chat"),
            ("/help", "Show this help message"),
            ("/auto", "Toggle auto-approve mode"),
            ("/tui", "Switch to TUI mode"),
            ("/prompt set <text>", "Set system prompt"),
            ("/prompt get", "Get current system prompt"),
            ("/prompt clear", "Clear system prompt"),
            ("/profile use <name>", "Switch to profile"),
            ("/profile list", "List all profiles"),
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        self.console.print(table)

    def get_user_input(self, prompt_text: str = "You > ") -> str:
        """Get input from user with enhanced styling."""
        return Prompt.ask(f"[bold blue]{prompt_text}[/bold blue]")

    def show_confirmation(self, message: str) -> bool:
        """Show confirmation dialog with enhanced styling."""
        return Confirm.ask(f"[bold yellow]{message}[/bold yellow]")

    async def show_loading(self, message: str = "Processing..."):
        """Show loading indicator with enhanced animation."""
        with Live(self.spinner, refresh_per_second=10) as live:
            live.update(Text(message, style="bold green"))
            await asyncio.sleep(1)  # Simulate loading

    def show_error(self, message: str):
        """Show error message with enhanced styling."""
        self.console.print(Panel(
            f"[bold red]✗[/bold red] {message}",
            border_style="red",
            expand=False
        ))

    def show_success(self, message: str):
        """Show success message with enhanced styling."""
        self.console.print(Panel(
            f"[bold green]✓[/bold green] {message}",
            border_style="green",
            expand=False
        ))

    def show_session_info(self, session_data: Dict[str, Any]):
        """Show session information with enhanced styling."""
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
        """Clear the screen and show header."""
        self.console.clear()
        self.show_header()

    def start_tui_mode(self):
        """Start TUI mode."""
        self.console.print("[blue]Launching TUI mode...[/blue]")
        # In a real implementation, this would start the TUI app
        pass

    def show_system_prompt_info(self, system_prompt: Optional[str] = None):
        """Show system prompt information in a dedicated panel."""
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

    def show_profile_info(self, profile_name: Optional[str] = None):
        """Show profile information in a dedicated panel."""
        if profile_name:
            profiles = self.prompt_manager.list_profiles()
            if profile_name in profiles:
                prompt = self.prompt_manager.load_system_prompt(profile_name)
                panel_content = f"Profile: [bold]{profile_name}[/bold]\n"
                panel_content += f"System Prompt: [italic]{prompt if prompt else 'Not set'}[/italic]"
                
                panel = Panel(
                    panel_content,
                    title="[bold blue]Active Profile[/bold blue]",
                    border_style="blue",
                    expand=False
                )
                self.console.print(panel)
            else:
                self.show_error(f"Profile '{profile_name}' does not exist")
    
    def show_memory_info(self):
        """Show current memory state with enhanced styling."""
        from ..memory import memory_system
        
        try:
            stats = memory_system.get_memory_stats()
            
            memory_info = f"Session: [bold]{stats['session_id']}[/bold]\n"
            memory_info += f"Ephemeral: {stats['ephemeral_entries']} entries\n"
            memory_info += f"Persistent: {stats['persistent_entries']} entries\n"
            memory_info += f"Importance: {stats['average_importance']:.2f}\n"
            
            if stats['content_type_distribution']:
                memory_info += "\nContent Types:\n"
                for content_type, count in stats['content_type_distribution'].items():
                    memory_info += f"  • {content_type}: {count}\n"
            
            panel = Panel(
                memory_info,
                title="[bold blue]🧠 Memory State[/bold blue]",
                border_style="blue",
                expand=False,
                subtitle=f"[dim]Project: {stats['project_path']}[/dim]"
            )
            self.console.print(panel)
        except Exception as e:
            panel = Panel(
                f"[italic]Memory system error: {str(e)}[/italic]",
                title="[bold blue]🧠 Memory State[/bold blue]",
                border_style="dim",
                expand=False
            )
            self.console.print(panel)

# Global UI instance
ui = EnhancedOrbyUI()