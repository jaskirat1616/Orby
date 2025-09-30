"""Utility functions for detecting local AI models."""
import subprocess
import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
import platform


def detect_ollama_models() -> List[Dict[str, str]]:
    """Detect models available in Ollama."""
    models = []
    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            for model in data.get("models", []):
                models.append({
                    "name": model.get("name", ""),
                    "backend": "ollama",
                    "size": model.get("size", 0),
                    "parameters": model.get("details", {}).get("parameter_size", "Unknown")
                })
    except Exception:
        # Ollama not available
        pass
    
    return models


def detect_lmstudio_models() -> List[Dict[str, str]]:
    """Detect models available in LM Studio."""
    models = []
    try:
        # Check if LM Studio is running
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            for model in data.get("data", []):
                models.append({
                    "name": model.get("id", ""),
                    "backend": "lmstudio"
                })
    except Exception:
        # LM Studio not available
        pass
    
    return models


def detect_gpt4all_models() -> List[Dict[str, str]]:
    """Detect GPT4All models."""
    models = []
    try:
        # Common GPT4All model locations
        gpt4all_dirs = [
            Path.home() / ".cache" / "gpt4all",
            Path.home() / "gpt4all",
            Path("/usr/local/share/gpt4all"),
        ]
        
        for model_dir in gpt4all_dirs:
            if model_dir.exists():
                for model_file in model_dir.glob("*.bin"):
                    models.append({
                        "name": model_file.stem,
                        "backend": "gpt4all",
                        "path": str(model_file)
                    })
                for model_file in model_dir.glob("*.gguf"):
                    models.append({
                        "name": model_file.stem,
                        "backend": "gpt4all",
                        "path": str(model_file)
                    })
    except Exception:
        # If detection fails, return empty list
        pass
    
    return models


def detect_vllm_models() -> List[Dict[str, str]]:
    """Detect vLLM models."""
    models = []
    # vLLM typically loads models dynamically, so we check common model locations
    model_dirs = [
        Path.home() / ".cache" / "huggingface" / "hub",
        Path.home() / "models",
    ]
    
    for model_dir in model_dirs:
        if model_dir.exists():
            for model_path in model_dir.iterdir():
                if model_path.is_dir() and (model_path / "config.json").exists():
                    models.append({
                        "name": model_path.name,
                        "backend": "vllm",
                        "path": str(model_path)
                    })
    
    return models


def detect_all_local_models() -> Dict[str, List[Dict[str, str]]]:
    """Detect all available local models from all sources."""
    all_models = {
        "ollama": detect_ollama_models(),
        "lmstudio": detect_lmstudio_models(),
        "gpt4all": detect_gpt4all_models(),
        "vllm": detect_vllm_models()
    }
    
    return all_models


def get_model_details(model_name: str, backend: str) -> Optional[Dict[str, str]]:
    """Get detailed information about a specific model."""
    # This would typically query the backend for more details
    # For now, return basic info
    return {
        "name": model_name,
        "backend": backend,
        "status": "detected"
    }