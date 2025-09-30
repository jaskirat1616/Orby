"""Configuration management for Orby."""
import os
import yaml
from pathlib import Path


def get_config_dir() -> Path:
    """Get the Orby configuration directory."""
    config_dir = Path.home() / '.orby'
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_sessions_dir() -> Path:
    """Get the Orby sessions directory."""
    sessions_dir = get_config_dir() / 'sessions'
    sessions_dir.mkdir(exist_ok=True)
    return sessions_dir


def load_config() -> dict:
    """Load the configuration from the config file."""
    config_dir = get_config_dir()  # Ensure config directory exists
    config_path = config_dir / 'config.yml'
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    else:
        # Return default configuration
        return {
            'ollama_url': 'http://localhost:11434',
            'lmstudio_url': 'http://localhost:1234',
            'default_backend': 'ollama',
            'default_model': 'llama3.1:latest'  # Updated to use a model that exists
        }


def save_config(config: dict):
    """Save the configuration to the config file."""
    config_dir = get_config_dir()  # Ensure config directory exists
    config_path = config_dir / 'config.yml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)