"""System prompt and profile management commands for Orby."""
import click
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from rich.table import Table

from ..config import get_config_dir, load_config
from ..ui import OrbyUI


def get_prompts_dir() -> Path:
    """Get the Orby prompts directory."""
    prompts_dir = get_config_dir() / 'prompts'
    prompts_dir.mkdir(exist_ok=True)
    return prompts_dir


def load_system_prompt(profile_name: Optional[str] = None) -> Optional[str]:
    """Load the system prompt from the active profile or global config."""
    config = load_config()
    
    if profile_name:
        # Load from specific profile
        profile_path = get_config_dir() / f'profile_{profile_name}.yml'
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                profile_config = yaml.safe_load(f)
                return profile_config.get('system_prompt')
    else:
        # Load from active config
        return config.get('system_prompt')
    
    return None


def save_system_prompt(prompt: str, profile_name: Optional[str] = None):
    """Save the system prompt to the active config or specific profile."""
    if profile_name:
        # Save to specific profile
        profile_path = get_config_dir() / f'profile_{profile_name}.yml'
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                profile_config = yaml.safe_load(f)
            profile_config['system_prompt'] = prompt
            with open(profile_path, 'w') as f:
                yaml.dump(profile_config, f, default_flow_style=False)
        else:
            # Create new profile with system prompt
            default_config = {
                'ollama_url': 'http://localhost:11434',
                'lmstudio_url': 'http://localhost:1234',
                'default_backend': 'ollama',
                'default_model': 'llama3.1:latest',
                'system_prompt': prompt
            }
            with open(profile_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
    else:
        # Save to active config
        config = load_config()
        config['system_prompt'] = prompt
        
        config_path = get_config_dir() / 'config.yml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)


def list_profiles() -> List[str]:
    """List all available profiles."""
    import glob as py_glob
    config_dir = get_config_dir()
    pattern = str(config_dir / 'profile_*.yml')
    profile_file_paths = py_glob.glob(pattern)
    profile_names = []
    for path_str in profile_file_paths:
        path_obj = Path(path_str)
        name = path_obj.name.replace('profile_', '').replace('.yml', '')
        if name:  # Only add non-empty names
            profile_names.append(name)
    return profile_names


@click.group()
def prompt():
    """Manage system prompts and profiles."""
    pass


@prompt.command()
@click.argument('prompt_text', nargs=-1)
@click.option('--profile', '-p', default=None, help='Apply to specific profile')
def set(prompt_text, profile):
    """Set the system prompt for current session or a specific profile."""
    ui = OrbyUI()
    
    if not prompt_text:
        ui.show_error("Please provide a system prompt text")
        return
    
    prompt_str = ' '.join(prompt_text)
    save_system_prompt(prompt_str, profile)
    
    if profile:
        ui.show_success(f"System prompt set for profile '{profile}'")
        ui.console.print(f"Profile: [bold]{profile}[/bold]")
    else:
        ui.show_success("Global system prompt set")
    
    # Display the saved prompt
    ui.console.print("\n[bold]Current system prompt:[/bold]")
    ui.console.print(f"[italic]{prompt_str}[/italic]")


@prompt.command()
@click.option('--profile', '-p', default=None, help='View prompt from specific profile')
def get(profile):
    """Get the current system prompt."""
    ui = OrbyUI()
    
    prompt_text = load_system_prompt(profile)
    
    if prompt_text:
        if profile:
            ui.console.print(f"[bold]System prompt for profile '{profile}':[/bold]")
        else:
            ui.console.print("[bold]Current system prompt:[/bold]")
        ui.console.print(f"[italic]{prompt_text}[/italic]")
    else:
        if profile:
            ui.show_error(f"No system prompt found for profile '{profile}'")
        else:
            ui.show_error("No system prompt set")


@prompt.command()
def clear():
    """Clear the current system prompt."""
    ui = OrbyUI()
    
    config = load_config()
    if 'system_prompt' in config:
        old_prompt = config['system_prompt']
        del config['system_prompt']
        
        config_path = get_config_dir() / 'config.yml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        ui.show_success("System prompt cleared")
        ui.console.print(f"[italic]Previous prompt was: {old_prompt}[/italic]")
    else:
        ui.show_error("No system prompt to clear")


@prompt.command()
def list():
    """List all available profiles."""
    ui = OrbyUI()
    profiles = list_profiles()
    
    if profiles:
        ui.console.print("[bold]Available Profiles:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Profile Name", style="cyan", no_wrap=True)
        table.add_column("System Prompt", style="white")
        
        for profile_name in profiles:
            prompt_text = load_system_prompt(profile_name)
            prompt_display = prompt_text[:50] + "..." if prompt_text and len(prompt_text) > 50 else (prompt_text or "Not set")
            table.add_row(profile_name, prompt_display)
        
        ui.console.print(table)
    else:
        ui.show_error("No profiles found")


@prompt.command()
@click.argument('profile_name')
def use(profile_name):
    """Switch to using a specific profile."""
    ui = OrbyUI()
    config_dir = get_config_dir()
    profile_path = config_dir / f'profile_{profile_name}.yml'
    
    if not profile_path.exists():
        ui.show_error(f"Profile '{profile_name}' does not exist.")
        return
    
    # Read the profile config
    with open(profile_path, 'r') as f:
        profile_config = yaml.safe_load(f)
    
    # Save it as the main config
    main_config_path = config_dir / 'config.yml'
    with open(main_config_path, 'w') as f:
        yaml.dump(profile_config, f, default_flow_style=False)
    
    ui.show_success(f"Switched to profile: {profile_name}")
    
    # Show the system prompt for this profile if it exists
    prompt_text = load_system_prompt()
    if prompt_text:
        ui.console.print(f"[bold]Active system prompt:[/bold]")
        ui.console.print(f"[italic]{prompt_text}[/italic]")


@prompt.command()
@click.argument('profile_name')
@click.option('--prompt', '-p', default=None, help='System prompt for the new profile')
def create(profile_name, prompt):
    """Create a new profile with optional system prompt."""
    ui = OrbyUI()
    config_dir = get_config_dir()
    
    profile_path = config_dir / f'profile_{profile_name}.yml'
    
    if profile_path.exists():
        ui.show_error(f"Profile '{profile_name}' already exists.")
        return
    
    default_config = {
        'ollama_url': 'http://localhost:11434',
        'lmstudio_url': 'http://localhost:1234',
        'default_backend': 'ollama',
        'default_model': 'llama3.1:latest'
    }
    
    if prompt:
        default_config['system_prompt'] = prompt
    
    with open(profile_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    ui.show_success(f"Profile '{profile_name}' created")
    
    if prompt:
        ui.console.print(f"System prompt set to: [italic]{prompt}[/italic]")
    else:
        ui.console.print("Profile created with default settings")