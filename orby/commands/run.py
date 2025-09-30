"""Run command for Orby."""
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from ..config import load_config
from ..backend import BackendManager
from ..backends import OllamaBackend, LMStudioBackend


console = Console()


@click.command()
@click.argument('prompt')
@click.option('--model', '-m', default=None, help='Model to use for inference')
def run(prompt, model):
    """Run a single prompt through a local LLM."""
    config = load_config()
    
    # Initialize backend manager
    backend_manager = BackendManager()
    ollama_url = config.get('ollama_url', 'http://localhost:11434')
    lmstudio_url = config.get('lmstudio_url', 'http://localhost:1234')
    
    backend_manager.register_backend('ollama', OllamaBackend(ollama_url))
    backend_manager.register_backend('lmstudio', LMStudioBackend(lmstudio_url))
    
    # Determine which backend and model to use
    current_backend_name = config.get('default_backend', 'ollama')
    current_model = model or config.get('default_model', 'llama3.1:latest')
    
    # If a specific model is provided, try to find which backend has it
    if model:
        all_models = backend_manager.list_all_models()
        found = False
        for backend_name, models in all_models.items():
            if model in models:
                current_backend_name = backend_name
                current_model = model
                found = True
                break
        
        if not found:
            error_text = f"✗ Model '{model}' not found in any backend"
            error_panel = Panel(error_text, style="red", border_style="red", expand=False)
            console.print(error_panel)
            return
    
    # Get the backend
    backend = backend_manager.get_backend(current_backend_name)
    if not backend:
        error_text = f"✗ Backend '{current_backend_name}' not found"
        error_panel = Panel(error_text, style="red", border_style="red", expand=False)
        console.print(error_panel)
        return
    
    try:
        # Print header and input in panels
        header_text = Text("ORBY RESPONSE", style="bold blue")
        header = Panel(header_text, style="blue", border_style="blue", expand=False)
        console.print(header)
        
        # Input panel
        input_panel = Panel(
            prompt,
            title="[bold blue]Input Prompt[/bold blue]",
            border_style="blue",
            expand=False
        )
        console.print(input_panel)
        
        # Processing indicator
        console.print("[bold green]Processing...[/bold green]")
        
        # Prepare the messages
        messages = [{"role": "user", "content": prompt}]
        
        # Get the response
        response = backend.chat(messages, stream=False, model=current_model)
        
        # Output panel
        output_panel = Panel(
            response,
            title=f"[bold green]Output ({current_backend_name}/{current_model})[/bold green]",
            border_style="green",
            expand=False
        )
        console.print(output_panel)
        
    except Exception as e:
        error_text = f"✗ Error: {str(e)}"
        error_panel = Panel(error_text, style="red", border_style="red", expand=False)
        console.print(error_panel)