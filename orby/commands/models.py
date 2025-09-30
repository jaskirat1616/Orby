"""Models command for Orby."""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..config import load_config
from ..backend import BackendManager
from ..backends import OllamaBackend, LMStudioBackend


console = Console()


@click.command()
def models():
    """List all available models from local backends."""
    config = load_config()
    
    # Initialize backend manager
    backend_manager = BackendManager()
    ollama_url = config.get('ollama_url', 'http://localhost:11434')
    lmstudio_url = config.get('lmstudio_url', 'http://localhost:1234')
    
    backend_manager.register_backend('ollama', OllamaBackend(ollama_url))
    backend_manager.register_backend('lmstudio', LMStudioBackend(lmstudio_url))
    
    # Header panel
    header_text = "AVAILABLE MODELS"
    header = Panel(header_text, style="bold blue", border_style="blue", expand=False)
    console.print(header)
    
    # Get models from all backends
    all_models = backend_manager.list_all_models()
    
    if not all_models:
        error_text = "No backends are accessible. Please ensure Ollama or LM Studio is running."
        console.print(Panel(error_text, style="red", border_style="red", expand=False))
        return
    
    # Create a table to display models
    models_table = Table(title="Available Models", show_header=True, header_style="bold magenta")
    models_table.add_column("Backend", style="cyan", no_wrap=True)
    models_table.add_column("Models", style="white")
    
    for backend_name, models in all_models.items():
        if models:
            # Format models as a list with bullet points
            model_list = "\n".join([f"• {model}" for model in models])
            models_table.add_row(backend_name.upper(), model_list)
        else:
            models_table.add_row(backend_name.upper(), "[red]No models available[/red]")
    
    console.print(models_table)