"""System prompt and profile management for Orby."""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging


class PromptManager:
    """Manages system prompts and profiles for Orby."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.orby'
        self.config_dir.mkdir(exist_ok=True)
        self.log_file = self.config_dir / 'prompt_log.txt'
        
    def get_prompts_dir(self) -> Path:
        """Get the Orby prompts directory."""
        prompts_dir = self.config_dir / 'prompts'
        prompts_dir.mkdir(exist_ok=True)
        return prompts_dir
    
    def get_profiles_dir(self) -> Path:
        """Get the Orby profiles directory."""
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(exist_ok=True)
        return profiles_dir
    
    def log_prompt_change(self, action: str, profile: Optional[str], prompt: Optional[str] = None):
        """Log prompt changes for security and transparency."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        profile_name = profile or "global"
        
        if action == "set":
            log_entry = f"[{timestamp}] System prompt {action} for {profile_name}: {prompt[:50]}...\n"
        else:
            log_entry = f"[{timestamp}] System prompt {action} for {profile_name}\n"
            
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
    
    def load_system_prompt(self, profile_name: Optional[str] = None) -> Optional[str]:
        """Load the system prompt from the active profile or global config."""
        from .config import load_config
        
        if profile_name:
            # Load from specific profile
            profile_path = self.config_dir / f'profile_{profile_name}.yml'
            if profile_path.exists():
                with open(profile_path, 'r') as f:
                    profile_config = yaml.safe_load(f)
                    return profile_config.get('system_prompt')
        else:
            # Load from active config
            config = load_config()
            return config.get('system_prompt')
        
        return None
    
    def save_system_prompt(self, prompt: str, profile_name: Optional[str] = None):
        """Save the system prompt to the active config or specific profile."""
        from .config import load_config
        
        if profile_name:
            # Save to specific profile
            profile_path = self.config_dir / f'profile_{profile_name}.yml'
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
            
            self.log_prompt_change("set", profile_name, prompt)
        else:
            # Save to active config
            config = load_config()
            config['system_prompt'] = prompt
            
            config_path = self.config_dir / 'config.yml'
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            self.log_prompt_change("set", None, prompt)
    
    def clear_system_prompt(self, profile_name: Optional[str] = None):
        """Clear the system prompt from the active config or specific profile."""
        from .config import load_config
        
        if profile_name:
            # Clear from specific profile
            profile_path = self.config_dir / f'profile_{profile_name}.yml'
            if profile_path.exists():
                with open(profile_path, 'r') as f:
                    profile_config = yaml.safe_load(f)
                if 'system_prompt' in profile_config:
                    del profile_config['system_prompt']
                    with open(profile_path, 'w') as f:
                        yaml.dump(profile_config, f, default_flow_style=False)
                    
                    self.log_prompt_change("clear", profile_name)
        else:
            # Clear from active config
            config = load_config()
            if 'system_prompt' in config:
                del config['system_prompt']
                
                config_path = self.config_dir / 'config.yml'
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                
                self.log_prompt_change("clear", None)
    
    def list_profiles(self) -> List[str]:
        """List all available profiles."""
        profile_files = list(self.config_dir.glob('profile_*.yml'))
        return [f.stem.replace('profile_', '') for f in profile_files]
    
    def create_profile(self, profile_name: str, system_prompt: Optional[str] = None):
        """Create a new profile with optional system prompt."""
        profile_path = self.config_dir / f'profile_{profile_name}.yml'
        
        if profile_path.exists():
            raise ValueError(f"Profile '{profile_name}' already exists.")
        
        default_config = {
            'ollama_url': 'http://localhost:11434',
            'lmstudio_url': 'http://localhost:1234',
            'default_backend': 'ollama',
            'default_model': 'llama3.1:latest'
        }
        
        if system_prompt:
            default_config['system_prompt'] = system_prompt
        
        with open(profile_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        if system_prompt:
            self.log_prompt_change("set", profile_name, system_prompt)
    
    def use_profile(self, profile_name: str):
        """Switch to using a specific profile."""
        profile_path = self.config_dir / f'profile_{profile_name}.yml'
        
        if not profile_path.exists():
            raise ValueError(f"Profile '{profile_name}' does not exist.")
        
        # Read the profile config
        with open(profile_path, 'r') as f:
            profile_config = yaml.safe_load(f)
        
        # Save it as the main config
        main_config_path = self.config_dir / 'config.yml'
        with open(main_config_path, 'w') as f:
            yaml.dump(profile_config, f, default_flow_style=False)
    
    def get_prompt_history(self) -> List[str]:
        """Get recent prompt changes from the log."""
        if not self.log_file.exists():
            return []
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
        
        # Return last 10 entries
        return lines[-10:]