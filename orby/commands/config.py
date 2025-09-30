"""Config command for Orby."""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import os
import yaml
from pathlib import Path
from ..config import load_config, save_config


console = Console()


@click.group()
def config():
    """Manage Orby configuration and profiles."""
    pass


@config.command()
def show():
    """Show current configuration."""
    config_data = load_config()
    
    # Header panel
    header = Panel("CURRENT CONFIGURATION", style="bold blue", border_style="blue", expand=False)
    console.print(header)
    
    # Create a table to display configuration
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Key", style="cyan", no_wrap=True)
    config_table.add_column("Value", style="white")
    
    for key, value in config_data.items():
        config_table.add_row(key, str(value))
    
    console.print(config_table)


@config.command()
@click.option('--ollama-url', default=None, help='Ollama server URL')
@click.option('--lmstudio-url', default=None, help='LM Studio server URL')
@click.option('--default-backend', default=None, help='Default backend (ollama, lmstudio)')
@click.option('--default-model', default=None, help='Default model')
def set(ollama_url, lmstudio_url, default_backend, default_model):
    """Set configuration values."""
    config_data = load_config()
    
    if ollama_url:
        config_data['ollama_url'] = ollama_url
    if lmstudio_url:
        config_data['lmstudio_url'] = lmstudio_url
    if default_backend:
        config_data['default_backend'] = default_backend
    if default_model:
        config_data['default_model'] = default_model
    
    save_config(config_data)
    
    # Success panel
    success_text = Text("CONFIGURATION UPDATED", style="bold green")
    success_panel = Panel(success_text, style="green", border_style="green", expand=False)
    console.print(success_panel)
    
    # Show updated values
    updated_table = Table(title="Updated Configuration", show_header=True, header_style="bold magenta")
    updated_table.add_column("Setting", style="cyan", no_wrap=True)
    updated_table.add_column("Value", style="white")
    
    if ollama_url:
        updated_table.add_row("✓ Ollama URL", ollama_url)
    if lmstudio_url:
        updated_table.add_row("✓ LM Studio URL", lmstudio_url)
    if default_backend:
        updated_table.add_row("✓ Default backend", default_backend)
    if default_model:
        updated_table.add_row("✓ Default model", default_model)
    
    console.print(updated_table)


@config.command()
@click.argument('profile_name')
def create_profile(profile_name):
    """Create a new profile with default settings."""
    config_dir = Path.home() / '.orby'
    config_dir.mkdir(exist_ok=True)
    
    profile_path = config_dir / f'profile_{profile_name}.yml'
    
    default_config = {
        'ollama_url': 'http://localhost:11434',
        'lmstudio_url': 'http://localhost:1234',
        'default_backend': 'ollama',
        'default_model': 'llama3.1:latest'
    }
    
    with open(profile_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    # Success panel
    success_text = Text(f"PROFILE '{profile_name.upper()}' CREATED SUCCESSFULLY", style="bold green")
    success_panel = Panel(success_text, style="green", border_style="green", expand=False)
    console.print(success_panel)
    
    # Show profile info
    profile_table = Table(title="Profile Information", show_header=True, header_style="bold magenta")
    profile_table.add_column("Setting", style="cyan", no_wrap=True)
    profile_table.add_column("Value", style="white")
    
    profile_table.add_row("Profile name", profile_name)
    profile_table.add_row("Path", str(profile_path))
    profile_table.add_row("Default backend", default_config['default_backend'])
    profile_table.add_row("Default model", default_config['default_model'])
    
    console.print(profile_table)


@config.command()
@click.argument('profile_name')
def use_profile(profile_name):
    """Switch to using a specific profile."""
    config_dir = Path.home() / '.orby'
    profile_path = config_dir / f'profile_{profile_name}.yml'
    
    if not profile_path.exists():
        error_text = f"✗ Profile '{profile_name}' does not exist."
        error_panel = Panel(error_text, style="red", border_style="red", expand=False)
        console.print(error_panel)
        return
    
    # Read the profile config
    with open(profile_path, 'r') as f:
        profile_config = yaml.safe_load(f)
    
    # Save it as the main config
    main_config_path = config_dir / 'config.yml'
    with open(main_config_path, 'w') as f:
        yaml.dump(profile_config, f, default_flow_style=False)
    
    # Success panel
    success_text = Text(f"SWITCHED TO PROFILE: {profile_name.upper()}", style="bold green")
    success_panel = Panel(success_text, style="green", border_style="green", expand=False)
    console.print(success_panel)
    
    console.print(f"✓ Now using profile: [bold]{profile_name}[/bold]")