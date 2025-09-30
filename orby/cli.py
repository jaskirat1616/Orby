"""Orby - The local-first AI CLI with agentic powers."""
import click
from .commands import chat, run, models, config
from .commands.enhanced import add_enhanced_commands


@click.group()
@click.version_option(version='0.1.0')
def main():
    """
    Orby: The local-first AI CLI with agentic powers.
    Connect Ollama, LM Studio, Hugging Face — no cloud required.
    """
    pass


main.add_command(chat)
main.add_command(run)
main.add_command(models)
main.add_command(config)

# Add enhanced commands
add_enhanced_commands(main)

# Add TUI command with lazy import to avoid import issues
try:
    from .tui import tui
    main.add_command(tui)
except ImportError:
    # If TUI dependencies aren't available, don't add the command
    pass