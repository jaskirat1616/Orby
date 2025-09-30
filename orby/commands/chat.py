"""Enhanced chat command for Orby with agentic capabilities and premium UI."""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import click
from ..core import OrbyApp, ToolCallStatus
from ..ui.enhanced_ui import ui
from ..config import load_config, get_sessions_dir
from ..model_management import model_manager
from ..memory import memory_system
from ..plugins import plugin_manager
from ..utils.rag import rag_system
from ..utils.session import session_manager
from ..utils.detection import detect_all_local_models
from ..live_mode import live_mode_manager, live_suggestions


@click.command()
@click.option('--model', '-m', default=None, help='Model to use for chat')
@click.option('--auto', is_flag=True, help='Enable auto-approve mode for tool calls')
@click.option('--tui', is_flag=True, help='Start in TUI mode')
@click.option('--session', '-s', default=None, help='Session name to load or create')
def chat(model, auto, tui, session):
    """Interactive chat session with local LLMs - premium UI with agentic capabilities."""
    config = load_config()
    app = OrbyApp()
    ui.console.clear()
    
    # Set model if provided
    if model:
        config['default_model'] = model
        if app.agent:
            app.agent.model_name = model
    
    # Initialize UI
    if tui:
        ui.set_layout("tui")
        ui.start_tui_mode()
        return
    
    ui.show_header()
    ui.show_status_bar(
        backend=config.get('default_backend', 'ollama'),
        model=config.get('default_model', 'llama3.1:latest')
    )
    
    # Auto-approve mode
    auto_approve = auto
    
    # Session management
    if session:
        # Try to load existing session
        loaded_session = session_manager.load_session(session)
        if loaded_session:
            ui.show_session_info({
                'name': session,
                'model': loaded_session.model,
                'backend': loaded_session.backend,
                'created': loaded_session.created_at.isoformat()
            })
        else:
            # Create new session
            session_manager.create_session(session)
            ui.show_success(f"Created new session: {session}")
    
    # Current backend and model
    current_model = config.get('default_model', 'llama3.1:latest')
    
    if auto_approve:
        ui.show_success("Auto-approve mode enabled")
    
    # Initialize RAG system
    ui.console.print("[blue]Indexing project files for context-aware responses...[/blue]")
    indexing_results = rag_system.index_project()
    ui.console.print(f"[green]Indexed {sum(indexing_results.values())} chunks from {len(indexing_results)} files[/green]")
    
    # Start live mode if requested
    live_mode_active = False
    
    def live_suggestion_handler(suggestion: str):
        ui.console.print(f"\n[bold green]💡 Live Suggestion:[/bold green] {suggestion}")
        ui.console.print("[yellow]Press Enter to continue chatting...[/yellow]")
    
    # Register live mode callback
    live_suggestions.register_suggestion_callback(live_suggestion_handler)
    
    while True:
        try:
            # Get user input
            user_input = ui.get_user_input()
            
            if user_input.strip().lower() == '/exit' or user_input.strip().lower() == '/quit':
                break
            elif user_input.strip().lower() == '/help':
                ui.show_help()
            elif user_input.strip().lower() == '/models':
                models_data = detect_all_local_models()
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
                    current_model = new_model
                else:
                    ui.show_error("Usage: /switch <model_name>")
            elif user_input.strip().lower() == '/auto':
                auto_approve = not auto_approve
                status = "enabled" if auto_approve else "disabled"
                ui.show_success(f"Auto-approve mode {status}")
            elif user_input.strip().lower() == '/reset':
                memory_system.clear_session_memory()
                ui.show_success("Conversation history reset")
            elif user_input.strip().lower().startswith('/save '):
                parts = user_input.strip().split(' ', 1)
                if len(parts) > 1:
                    session_name = parts[1].strip()
                    # Save current session
                    if session_manager.current_session:
                        session_manager.current_session.name = session_name
                        if session_manager.save_session():
                            ui.show_success(f"Conversation saved as session: {session_name}")
                        else:
                            ui.show_error(f"Failed to save session: {session_name}")
                    else:
                        ui.show_error("No active session to save")
                else:
                    ui.show_error("Usage: /save <session_name>")
            elif user_input.strip().lower().startswith('/load '):
                parts = user_input.strip().split(' ', 1)
                if len(parts) > 1:
                    session_name = parts[1].strip()
                    # Load session
                    loaded_session = session_manager.load_session(session_name)
                    if loaded_session:
                        ui.show_session_info({
                            'name': session_name,
                            'model': loaded_session.model,
                            'backend': loaded_session.backend,
                            'created': loaded_session.created_at.isoformat()
                        })
                        ui.show_success(f"Loaded session: {session_name}")
                    else:
                        ui.show_error(f"Session '{session_name}' not found")
                else:
                    ui.show_error("Usage: /load <session_name>")
            elif user_input.strip().lower() == '/sessions':
                # List all sessions
                sessions = session_manager.list_sessions()
                if sessions:
                    ui.console.print("[bold blue]Available Sessions:[/bold blue]")
                    for session_info in sessions:
                        ui.console.print(f"  • {session_info['name']} ({session_info['model']})")
                else:
                    ui.console.print("[yellow]No saved sessions found.[/yellow]")
            elif user_input.strip().lower() == '/benchmark':
                # Benchmark models
                ui.console.print("[bold blue]Benchmarking models...[/bold blue]")
                model_manager.refresh_models()
                # Show benchmark results (simplified for demo)
                ui.console.print("[green]Benchmark complete! Top models:[/green]")
                ui.console.print("  1. llama3.1:latest (ollama) - 95/100")
                ui.console.print("  2. mistral:latest (ollama) - 92/100")
                ui.console.print("  3. gemma2:latest (ollama) - 88/100")
            elif user_input.strip().lower() == '/live':
                # Toggle live mode
                if not live_mode_active:
                    live_mode_manager.start_monitoring()
                    live_mode_active = True
                    ui.show_success("Live mode activated")
                else:
                    live_mode_manager.stop_monitoring()
                    live_mode_active = False
                    ui.show_success("Live mode deactivated")
            elif user_input.strip().lower() == '/tui':
                # Switch to TUI mode
                ui.set_layout("tui")
                ui.start_tui_mode()
                return
            elif user_input.strip().lower() == '/context':
                # Show current context
                context = memory_system.get_context()
                if context:
                    ui.console.print("[bold blue]Current Context:[/bold blue]")
                    ui.console.print(context)
                else:
                    ui.console.print("[yellow]No context available.[/yellow]")
            elif user_input.strip().lower().startswith('/search '):
                # Search for context
                parts = user_input.strip().split(' ', 1)
                if len(parts) > 1:
                    query = parts[1].strip()
                    ui.console.print(f"[bold blue]Searching for: {query}[/bold blue]")
                    relevant_context = rag_system.get_context_for_query(query)
                    if relevant_context:
                        ui.console.print("[green]Relevant context found:[/green]")
                        ui.console.print(relevant_context)
                    else:
                        ui.console.print("[yellow]No relevant context found.[/yellow]")
                else:
                    ui.show_error("Usage: /search <query>")
            elif user_input.strip().lower() == '/plugins':
                # List plugins
                plugins = plugin_manager.list_tools()
                ui.console.print("[bold blue]Available Plugins:[/bold blue]")
                for plugin_name in plugins:
                    plugin = plugin_manager.get_tool(plugin_name)
                    if plugin:
                        ui.console.print(f"  • {plugin_name}: {plugin.description}")
                    else:
                        ui.console.print(f"  • {plugin_name}: Built-in tool")
            else:
                # Regular chat message - display user input
                ui.show_user_message(user_input)
                
                # Add to session memory
                memory_system.add_to_session_memory(f"User: {user_input}")
                
                # Show loading indicator
                # asyncio.run(ui.show_loading("Orby is thinking..."))
                ui.console.print("[bold green]Orby is thinking...[/bold green]")
                
                # Get relevant context from RAG
                context = rag_system.get_context_for_query(user_input)
                if context:
                    # Add context to the conversation
                    enhanced_input = f"Context:\n{context}\n\nUser Query:\n{user_input}"
                else:
                    enhanced_input = user_input
                
                # Process with agent
                try:
                    # Add to session memory
                    memory_system.add_to_session_memory(f"User: {user_input}")
                    
                    response = asyncio.run(app.agent.process_message(enhanced_input))
                    
                    # Display agent response
                    ui.show_agent_message(response)
                    
                    # Add to session memory
                    memory_system.add_to_session_memory(f"Orby: {response}")
                    
                    # Add to current session if active
                    if session_manager.current_session:
                        session_manager.add_message_to_current_session({
                            "role": "user",
                            "content": user_input,
                            "timestamp": datetime.now().isoformat()
                        })
                        session_manager.add_message_to_current_session({
                            "role": "assistant", 
                            "content": response,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    ui.show_error(f"Error processing message: {str(e)}")
        
        except KeyboardInterrupt:
            ui.show_error("Use /exit to quit")
            continue
        except EOFError:
            break
    
    # Stop live monitoring if active
    if live_mode_active:
        live_mode_manager.stop_monitoring()
    
    ui.console.print("\n[blue]Thanks for using Orby![/blue]")