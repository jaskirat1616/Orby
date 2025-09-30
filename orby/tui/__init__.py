"""TUI launcher for Orby."""
import click
from .app import orby_tui


@click.command()
def tui():
    """Launch the Textual-based TUI for Orby."""
    # Run the Textual app
    orby_tui.run()