"""Enhanced commands for Orby with new features."""
import click
import asyncio
from pathlib import Path
from typing import Dict, List
from ..model_management import model_manager, ModelInfo
from ..ui.enhanced_ui import ui
from ..utils.detection import detect_all_local_models
from ..memory import memory_system
from ..plugins import plugin_manager
from ..utils.rag import rag_system
from ..live_mode import live_mode_manager, live_suggestions
from .memory import add_memory_commands
from .prompt import prompt


@click.command()
@click.argument('model_name')
def use(model_name):
    """Switch to a different model."""
    # Refresh available models
    model_manager.refresh_models()
    
    # Try to switch to the model
    if model_manager.switch_model(model_name):
        ui.show_success(f"Switched to model: {model_name}")
    else:
        ui.show_error(f"Model '{model_name}' not found. Available models:")
        # Show available models
        for model in model_manager.available_models:
            ui.console.print(f"  • {model.name} ({model.backend})")


@click.command()
def models():
    """List all available models from local backends."""
    ui.show_header()
    ui.show_status_bar()
    
    # Detect all models
    detected_models = detect_all_local_models()
    
    # Show models in a table
    ui.show_models_table(detected_models)


@click.command()
def benchmark():
    """Benchmark available models."""
    ui.show_header()
    ui.show_status_bar()
    
    # Refresh models
    model_manager.refresh_models()
    
    # Benchmark top models
    ui.console.print("[bold blue]Benchmarking models...[/bold blue]")
    
    models_with_scores = []
    for model in model_manager.available_models[:5]:  # Top 5 models
        ui.console.print(f"Benchmarking {model.name}...")
        score = model_manager.benchmark_model(model.name)
        models_with_scores.append((model, score))
    
    # Sort by score
    models_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Show results
    ui.show_benchmark_results(models_with_scores)


@click.command()
@click.argument('query')
def search(query):
    """Search for relevant context in your project."""
    # Index the project if needed
    ui.console.print("[bold blue]Indexing project files...[/bold blue]")
    indexing_results = rag_system.index_project()
    ui.console.print(f"[green]Indexed {sum(indexing_results.values())} chunks from {len(indexing_results)} files[/green]")
    
    # Search for relevant context
    ui.console.print(f"[bold blue]Searching for: {query}[/bold blue]")
    relevant_context = rag_system.get_context_for_query(query)
    
    if relevant_context:
        ui.console.print("[bold green]Relevant context found:[/bold green]")
        ui.console.print(relevant_context)
    else:
        ui.console.print("[yellow]No relevant context found.[/yellow]")


@click.command()
def tui():
    """Launch TUI mode."""
    ui.start_tui_mode()


@click.command()
def live():
    """Start live mode to monitor file changes."""
    ui.show_header()
    ui.show_status_bar()
    
    ui.console.print("[bold blue]Starting live mode...[/bold blue]")
    ui.console.print("[yellow]Monitoring file changes in current directory.[/yellow]")
    ui.console.print("[yellow]Press Ctrl+C to stop.[/yellow]")
    
    def suggestion_callback(suggestion: str):
        ui.console.print(f"[bold green]💡 Suggestion:[/bold green] {suggestion}")
    
    # Register the suggestion callback
    live_suggestions.register_suggestion_callback(suggestion_callback)
    
    # Start monitoring
    live_mode_manager.start_monitoring()
    
    try:
        # Keep running until interrupted
        while True:
            # Check for changes periodically
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        ui.console.print("\n[bold blue]Stopping live mode...[/bold blue]")
        live_mode_manager.stop_monitoring()
        ui.console.print("[green]Live mode stopped.[/green]")


@click.command()
def plugins():
    """List available plugins."""
    ui.show_header()
    ui.show_status_bar()
    
    available_plugins = plugin_manager.list_tools()
    
    table = ui.console.table(title="Available Plugins", show_header=True, header_style="bold magenta")
    table.add_column("Plugin Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    
    for plugin_name in available_plugins:
        plugin = plugin_manager.get_tool(plugin_name)
        if plugin:
            table.add_row(plugin_name, plugin.description)
        else:
            table.add_row(plugin_name, "Built-in tool")
    
    ui.console.print(table)


@click.command()
@click.argument('plugin_file', type=click.Path(exists=True))
def install_plugin(plugin_file):
    """Install a custom plugin from a file."""
    plugin_path = Path(plugin_file)
    
    # Copy plugin to plugins directory
    plugins_dir = Path.home() / ".orby" / "plugins"
    plugins_dir.mkdir(exist_ok=True)
    
    destination = plugins_dir / plugin_path.name
    destination.write_bytes(plugin_path.read_bytes())
    
    ui.show_success(f"Plugin installed: {plugin_path.name}")
    ui.console.print("[yellow]Restart Orby to load the new plugin.[/yellow]")


@click.command()
def memory():
    """Show memory statistics."""
    ui.show_header()
    ui.show_status_bar()
    
    session_count = len(memory_system.session_memory)
    persistent_count = len(memory_system.persistent_memory)
    
    table = ui.console.table(title="Memory Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Memory Type", style="cyan", no_wrap=True)
    table.add_column("Entries", style="white")
    
    table.add_row("Session Memory", str(session_count))
    table.add_row("Persistent Memory", str(persistent_count))
    
    ui.console.print(table)


@click.command()
def clear_memory():
    """Clear all memory."""
    if ui.show_confirmation("Are you sure you want to clear all memory?"):
        memory_system.clear_session_memory()
        memory_system.clear_persistent_memory()
        ui.show_success("Memory cleared.")


@click.command()
def context():
    """Show current context."""
    ui.show_header()
    ui.show_status_bar()
    
    # Show current context from memory
    context_str = memory_system.get_context()
    
    if context_str:
        ui.console.print("[bold green]Current Context:[/bold green]")
        ui.console.print(context_str)
    else:
        ui.console.print("[yellow]No context available.[/yellow]")


# Add these commands to the main CLI
def add_enhanced_commands(cli_group):
    """Add enhanced commands to the CLI group."""
    cli_group.add_command(use)
    cli_group.add_command(models)
    cli_group.add_command(benchmark)
    cli_group.add_command(search)
    cli_group.add_command(tui)
    cli_group.add_command(live)
    cli_group.add_command(plugins)
    cli_group.add_command(install_plugin)
    # Add the prompt command group
    cli_group.add_command(prompt)
    # Add memory commands (this includes clear and context as subcommands)
    add_memory_commands(cli_group)