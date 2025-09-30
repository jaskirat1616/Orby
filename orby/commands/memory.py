"""Memory management commands for Orby."""
import click
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.table import Table
from rich.panel import Panel
from ..memory import memory_system
from ..ui import OrbyUI


@click.group()
def memory():
    """Manage Orby's memory system."""
    pass


@memory.command()
def stats():
    """Show memory statistics."""
    ui = OrbyUI()
    ui.show_header()
    ui.show_status_bar()
    
    stats = memory_system.get_memory_stats()
    
    table = Table(title="Memory Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    table.add_row("Session ID", stats['session_id'])
    table.add_row("Ephemeral Entries", str(stats['ephemeral_entries']))
    table.add_row("Persistent Entries", str(stats['persistent_entries']))
    table.add_row("Average Importance", f"{stats['average_importance']:.2f}")
    table.add_row("Project Path", stats['project_path'])
    
    ui.console.print(table)
    
    if stats['content_type_distribution']:
        # Show content type distribution
        type_table = Table(title="Content Type Distribution", show_header=True, header_style="bold magenta")
        type_table.add_column("Type", style="cyan", no_wrap=True)
        type_table.add_column("Count", style="white")
        
        for content_type, count in stats['content_type_distribution'].items():
            type_table.add_row(content_type, str(count))
        
        ui.console.print(type_table)


@memory.command()
@click.argument('query', nargs=-1)
def search(query):
    """Search in memory."""
    ui = OrbyUI()
    ui.show_header()
    ui.show_status_bar()
    
    query_str = ' '.join(query) if query else ""
    
    if not query_str.strip():
        ui.show_error("Please provide a search query")
        return
    
    results = memory_system.search_session_memory(query_str)
    
    if results:
        ui.console.print(f"[bold green]Found {len(results)} results for: {query_str}[/bold green]")
        
        for i, entry in enumerate(results, 1):
            ui.console.print(f"\n[bold]{i}. {entry.content_type.upper()}[/bold] - [dim]{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
            ui.console.print(f"[italic]{entry.content[:200]}{'...' if len(entry.content) > 200 else ''}[/italic]")
            
            if entry.tags:
                ui.console.print(f"[yellow]Tags:[/yellow] {', '.join(entry.tags)}")
    else:
        ui.console.print(f"[yellow]No results found for: {query_str}[/yellow]")


@memory.command()
def list():
    """List recent memory entries."""
    ui = OrbyUI()
    ui.show_header()
    ui.show_status_bar()
    
    # Get the context which includes recent entries
    context = memory_system.get_context(max_entries=20)
    
    if context.strip():
        ui.console.print("[bold green]Recent Memory Entries:[/bold green]")
        ui.console.print(context)
    else:
        ui.console.print("[yellow]No memory entries found.[/yellow]")


@memory.command()
def clear():
    """Clear all memory."""
    ui = OrbyUI()
    
    if ui.show_confirmation("Are you sure you want to clear all memory? This cannot be undone."):
        memory_system.clear_all_memory()
        ui.show_success("Memory cleared.")


@memory.command()
@click.argument('session_name')
def save(session_name):
    """Save current memory session."""
    ui = OrbyUI()
    
    success = memory_system.save_session_memory(session_name)
    if success:
        ui.show_success(f"Memory session saved as: {session_name}")
    else:
        ui.show_error(f"Failed to save memory session: {session_name}")


@memory.command()
@click.argument('session_name')
def load(session_name):
    """Load a saved memory session."""
    ui = OrbyUI()
    
    success = memory_system.load_session_memory(session_name)
    if success:
        ui.show_success(f"Memory session loaded: {session_name}")
    else:
        ui.show_error(f"Failed to load memory session: {session_name}")


@memory.command()
def available():
    """List available saved sessions."""
    ui = OrbyUI()
    ui.show_header()
    ui.show_status_bar()
    
    sessions = memory_system.get_available_sessions()
    
    if sessions:
        ui.console.print("[bold green]Available Saved Sessions:[/bold green]")
        for session in sessions:
            ui.console.print(f"• {session}")
    else:
        ui.console.print("[yellow]No saved sessions available.[/yellow]")


@memory.command()
def context():
    """Show current memory context that will be provided to the model."""
    ui = OrbyUI()
    ui.show_header()
    ui.show_status_bar()
    
    context = memory_system.get_context()
    
    if context.strip():
        panel = Panel(
            f"[italic]{context}[/italic]",
            title="[bold yellow]Current Memory Context[/bold yellow]",
            border_style="yellow",
            expand=False
        )
        ui.console.print(panel)
    else:
        panel = Panel(
            "[italic]No memory context available.[/italic]",
            title="[bold yellow]Current Memory Context[/bold yellow]",
            border_style="dim",
            expand=False
        )
        ui.console.print(panel)


# Add this command to enhance the enhanced commands
def add_memory_commands(cli_group):
    """Add memory commands to the CLI group."""
    cli_group.add_command(memory)