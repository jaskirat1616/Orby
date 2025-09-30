"""Advanced chat command for Orby with agentic capabilities."""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import click
from ..core import OrbyApp, ToolCallStatus
from ..ui import OrbyUI
from ..config import load_config, get_sessions_dir
from .prompt import prompt


@click.command()
@click.option('--model', '-m', default=None, help='Model to use for chat')
@click.option('--auto', is_flag=True, help='Enable auto-approve mode for tool calls')
@click.option('--prompt', '-p', default=None, help='One-off system prompt for this session')
def chat(model, auto, prompt):
    """Interactive chat session with local LLMs - premium UI with agentic capabilities."""
    from ..prompt_manager import PromptManager
    prompt_manager = PromptManager()
    
    config = load_config()
    app = OrbyApp()
    ui = OrbyUI()
    
    # Set model if provided
    if model:
        app.config['default_model'] = model
        if app.agent:
            app.agent.model_name = model
    
    # Set one-off system prompt if provided
    if prompt:
        prompt_manager.save_system_prompt(prompt)
        ui.show_success(f"Using one-off system prompt: {prompt[:50]}...")
    
    # Initialize UI
    ui.show_header()
    ui.show_status_bar(
        backend=config.get('default_backend', 'ollama'),
        model=config.get('default_model', 'llama3.1:latest')
    )
    
    # Show active system prompt
    ui.show_system_prompt_info()
    
    # Show memory state
    ui.show_memory_info()
    
    # Auto-approve mode
    auto_approve = auto
    
    # Chat history
    messages = []
    
    # Current backend and model
    current_model = config.get('default_model', 'llama3.1:latest')
    
    if auto_approve:
        ui.show_success("Auto-approve mode enabled")
    
    while True:
        try:
            # Get user input
            user_input = ui.get_user_input()
            
            if user_input.strip().lower() == '/exit' or user_input.strip().lower() == '/quit':
                break
            elif user_input.strip().lower() == '/help':
                ui.show_help()
            elif user_input.strip().lower() == '/models':
                # For sync call
                models_data = app.get_available_models()
                ui.show_models_table(models_data)
            elif user_input.strip().lower().startswith('/switch '):
                parts = user_input.strip().split(' ', 1)
                if len(parts) > 1:
                    new_model = parts[1].strip()
                    # Update config and agent
                    config['default_model'] = new_model
                    if app.agent:
                        app.agent.model_name = new_model
                    ui.show_success(f"Switched to model: {new_model}")
                else:
                    ui.show_error("Usage: /switch <model_name>")
            elif user_input.strip().lower() == '/auto':
                auto_approve = not auto_approve
                status = "enabled" if auto_approve else "disabled"
                ui.show_success(f"Auto-approve mode {status}")
            elif user_input.strip().lower() == '/reset':
                messages = []
                ui.show_success("Conversation history reset")
            elif user_input.strip().lower().startswith('/save '):
                parts = user_input.strip().split(' ', 1)
                if len(parts) > 1:
                    filename = parts[1].strip()
                    sessions_dir = get_sessions_dir()
                    filepath = sessions_dir / f"{filename}.json"
                    
                    session_data = {
                        'created': datetime.now().isoformat(),
                        'model': current_model,
                        'messages': messages
                    }
                    
                    with open(filepath, 'w') as f:
                        json.dump(session_data, f, indent=2)
                    ui.show_success(f"Conversation saved to {filepath}")
                else:
                    ui.show_error("Usage: /save <session_name>")
            elif user_input.strip().lower().startswith('/load '):
                parts = user_input.strip().split(' ', 1)
                if len(parts) > 1:
                    session_name = parts[1].strip()
                    sessions_dir = get_sessions_dir()
                    filepath = sessions_dir / f"{session_name}.json"
                    
                    try:
                        with open(filepath, 'r') as f:
                            session_data = json.load(f)
                        
                        messages = session_data.get('messages', [])
                        saved_model = session_data.get('model', current_model)
                        
                        ui.show_success(f"Conversation loaded from {filepath}")
                        ui.show_session_info({
                            'name': session_name,
                            'model': saved_model,
                            'created': session_data.get('created')
                        })
                        
                    except FileNotFoundError:
                        ui.show_error(f"File {filepath} not found")
                    except json.JSONDecodeError:
                        ui.show_error(f"Invalid JSON in {filepath}")
                else:
                    ui.show_error("Usage: /load <session_name>")
            else:
                # Regular chat message - display user input
                ui.show_user_message(user_input)
                
                # Show loading indicator
                # Using sync version for now
                # asyncio.run(ui.show_loading("Orby is thinking..."))
                ui.console.print(ui.spinner, "Orby is thinking...")
                
                # Process with agent
                try:
                    # Using sync version for compatibility
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(app.agent.process_message(user_input))
                    loop.close()
                    
                    # Display agent response
                    ui.show_agent_message(response)
                    
                except Exception as e:
                    ui.show_error(f"Error processing message: {str(e)}")
        
        except KeyboardInterrupt:
            ui.show_error("Use /exit to quit")
            continue
        except EOFError:
            break
        except Exception as e:
            ui.show_error(f"Unexpected error: {str(e)}")
            import traceback
            print(f"Chat error: {traceback.format_exc()}")
            continue
    
    ui.console.print("\n[blue]Thanks for using Orby![/blue]")


@click.command()
@click.argument('prompt_arg', metavar='prompt')
@click.option('--model', '-m', default=None, help='Model to use for inference')
@click.option('--system-prompt', '-p', default=None, help='One-off system prompt for this command')
def run(prompt_arg, model, system_prompt):
    """Run a single prompt through a local LLM."""
    from ..prompt_manager import PromptManager
    prompt_manager = PromptManager()
    
    config = load_config()
    app = OrbyApp()
    ui = OrbyUI()
    
    # Set model if provided
    if model:
        config['default_model'] = model
        if app.agent:
            app.agent.model_name = model
    
    # Set one-off system prompt if provided
    if system_prompt:
        # Save temporarily and restore after execution
        old_system_prompt = prompt_manager.load_system_prompt()
        prompt_manager.save_system_prompt(system_prompt)
        ui.show_success(f"Using one-off system prompt: {system_prompt[:50]}...")
    
    # Show active system prompt
    ui.show_system_prompt_info()
    
    try:
        # Show input
        ui.show_user_message(prompt_arg)
        
        # Show loading
        # Using sync version for now
        ui.console.print(ui.spinner, "Processing...")
        
        # Process with agent using sync approach
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(app.agent.process_message(prompt_arg))
        except Exception as agent_error:
            response = f"Error processing request: {str(agent_error)}"
            import traceback
            print(f"Agent processing error: {traceback.format_exc()}")
        finally:
            loop.close()
        
        # Show response
        ui.show_agent_message(response)
        
    except Exception as e:
        ui.show_error(f"Error: {str(e)}")
        import traceback
        print(f"Run command error: {traceback.format_exc()}")
    finally:
        # Restore original system prompt if we set a temporary one
        if system_prompt and old_system_prompt is not None:
            try:
                prompt_manager.save_system_prompt(old_system_prompt)
            except Exception:
                # If restoring prompt fails, log but don't interrupt user
                pass


@click.command()
def models():
    """List all available models from local backends."""
    app = OrbyApp()
    ui = OrbyUI()
    
    try:
        # Use sync version
        models_data = app.get_available_models()
        ui.show_models_table(models_data)
    except Exception as e:
        ui.show_error(f"Error fetching models: {str(e)}")


@click.group()
def config():
    """Manage Orby configuration and profiles."""
    pass


@config.command()
def show():
    """Show current configuration."""
    from rich.table import Table
    console = OrbyUI().console
    
    config_data = load_config()
    
    table = Table(title="Current Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    for key, value in config_data.items():
        table.add_row(key, str(value))
    
    console.print(table)


@config.command()
@click.option('--ollama-url', default=None, help='Ollama server URL')
@click.option('--lmstudio-url', default=None, help='LM Studio server URL')
@click.option('--default-backend', default=None, help='Default backend (ollama, lmstudio)')
@click.option('--default-model', default=None, help='Default model')
def set(ollama_url, lmstudio_url, default_backend, default_model):
    """Set configuration values."""
    from ..config import save_config
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
    
    ui = OrbyUI()
    ui.show_success("Configuration updated")


@config.command()
@click.argument('profile_name')
@click.option('--prompt', '-p', default=None, help='System prompt for the new profile')
def create_profile(profile_name, prompt):
    """Create a new profile with optional system prompt."""
    from ..prompt_manager import PromptManager
    prompt_manager = PromptManager()
    
    try:
        prompt_manager.create_profile(profile_name, prompt)
        ui = OrbyUI()
        ui.show_success(f"Profile '{profile_name}' created")
        
        if prompt:
            ui.show_success(f"System prompt set to: {prompt[:50]}...")
    except ValueError as e:
        ui = OrbyUI()
        ui.show_error(str(e))


@config.command()
@click.argument('profile_name')
def use_profile(profile_name):
    """Switch to using a specific profile."""
    from ..prompt_manager import PromptManager
    prompt_manager = PromptManager()
    
    try:
        prompt_manager.use_profile(profile_name)
        ui = OrbyUI()
        ui.show_success(f"Switched to profile: {profile_name}")
        
        # Show the system prompt for this profile if it exists
        system_prompt = prompt_manager.load_system_prompt()
        if system_prompt:
            ui.show_system_prompt_info(system_prompt)
    except ValueError as e:
        ui = OrbyUI()
        ui.show_error(str(e))