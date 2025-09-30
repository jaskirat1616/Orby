#!/usr/bin/env python3
"""
Helper script for Orby CLI setup.
This script helps users configure Orby after installation.
"""

import sys
import subprocess
from pathlib import Path


def check_backends():
    """Check for available backends."""
    backends = {}
    
    # Check for Ollama
    try:
        result = subprocess.run(["ollama", "--version"], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            backends["ollama"] = result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        backends["ollama"] = None
    
    # Check for LM Studio (by checking if port 1234 is open)
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(("localhost", 1234))
        if result == 0:
            backends["lmstudio"] = "Running on localhost:1234"
        else:
            backends["lmstudio"] = None
    except Exception:
        backends["lmstudio"] = None
    finally:
        sock.close()
    
    return backends


def create_default_config():
    """Create default configuration file."""
    config_dir = Path.home() / ".orby"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "config.yml"
    if not config_file.exists():
        default_config = """
# Orby Configuration File
default_model: llama3.1:latest
default_backend: ollama
ollama_url: http://localhost:11434
lmstudio_url: http://localhost:1234

# UI Settings
ui:
  theme: default
  show_timing: true
  show_model_info: true

# Tool Settings
tools:
  shell:
    allow_dangerous_commands: false
    timeout: 30
  code:
    sandbox_enabled: true
    timeout: 60
"""
        
        with open(config_file, 'w') as f:
            f.write(default_config.strip())
        
        print(f"✅ Created default configuration at {config_file}")


def main():
    """Main setup function."""
    print("🚀 Orby Post-Installation Setup!")
    print("=" * 50)
    
    # Check backends
    print("\n🔍 Checking for available backends...")
    backends = check_backends()
    
    for backend, status in backends.items():
        if status:
            print(f"✅ {backend.capitalize()}: {status}")
        else:
            print(f"❌ {backend.capitalize()}: Not found")
            if backend == "ollama":
                print("   💡 Install Ollama from https://ollama.ai/")
            elif backend == "lmstudio":
                print("   💡 Download LM Studio from https://lmstudio.ai/")
    
    # Create default config
    create_default_config()
    
    # Show next steps
    print("\n🎉 Setup complete!")
    print("\n📝 Next steps:")
    print("   1. Pull a model (if using Ollama): ollama pull llama3.1:latest")
    print("   2. Start chatting: orby chat")
    print("   3. List models: orby models")
    print("   4. See help: orby --help")
    
    print("\n📚 Documentation: https://github.com/orby/orby")
    print("💬 Community: https://discord.gg/orby")


if __name__ == "__main__":
    main()