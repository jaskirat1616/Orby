"""Model management system for Orby."""
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    backend: str
    path: Optional[str] = None
    size: Optional[int] = None
    parameters: Optional[str] = None
    description: Optional[str] = None
    installed: bool = True
    benchmark_score: Optional[float] = None
    last_used: Optional[datetime] = None


class ModelDetector:
    """Detects available local models from various backends."""
    
    def __init__(self):
        self.models: List[ModelInfo] = []
    
    def detect_all_models(self) -> List[ModelInfo]:
        """Detect models from all available sources."""
        self.models = []
        
        # Detect Ollama models
        self.models.extend(self._detect_ollama_models())
        
        # Detect LM Studio models
        self.models.extend(self._detect_lmstudio_models())
        
        # Detect other local models
        self.models.extend(self._detect_local_models())
        
        return self.models
    
    def _detect_ollama_models(self) -> List[ModelInfo]:
        """Detect models available in Ollama."""
        models = []
        try:
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                for model_data in data.get("models", []):
                    models.append(ModelInfo(
                        name=model_data.get("name", ""),
                        backend="ollama",
                        size=model_data.get("size", 0),
                        parameters=model_data.get("details", {}).get("parameter_size", "Unknown")
                    ))
        except Exception:
            # Ollama not available
            pass
        
        return models
    
    def _detect_lmstudio_models(self) -> List[ModelInfo]:
        """Detect models available in LM Studio."""
        models = []
        try:
            # Check if LM Studio is running
            response = requests.get("http://localhost:1234/v1/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                for model_data in data.get("data", []):
                    models.append(ModelInfo(
                        name=model_data.get("id", ""),
                        backend="lmstudio"
                    ))
        except Exception:
            # LM Studio not available
            pass
        
        return models
    
    def _detect_local_models(self) -> List[ModelInfo]:
        """Detect other local models (like in model directories)."""
        models = []
        
        # Common model locations
        model_dirs = [
            Path.home() / ".ollama" / "models",
            Path.home() / ".cache" / "huggingface" / "hub",
            Path("/opt") / "models",  # Common on Linux
            Path.home() / "models",  # User models
        ]
        
        for model_dir in model_dirs:
            if model_dir.exists():
                # Look for GGUF files (common in local LLMs)
                for gguf_file in model_dir.rglob("*.gguf"):
                    model_name = gguf_file.stem
                    if not any(m.name == model_name for m in models):  # Avoid duplicates
                        models.append(ModelInfo(
                            name=model_name,
                            backend="local",
                            path=str(gguf_file)
                        ))
        
        return models


class ModelManager:
    """Manages models for Orby."""
    
    def __init__(self):
        self.detector = ModelDetector()
        self.available_models: List[ModelInfo] = []
        self.current_model: Optional[ModelInfo] = None
        self.model_history: List[Tuple[str, datetime]] = []
    
    def refresh_models(self):
        """Refresh list of available models."""
        self.available_models = self.detector.detect_all_models()
    
    def get_models_by_backend(self) -> Dict[str, List[ModelInfo]]:
        """Group models by backend."""
        result = {}
        for model in self.available_models:
            if model.backend not in result:
                result[model.backend] = []
            result[model.backend].append(model)
        return result
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a specific model by name."""
        for model in self.available_models:
            if model.name.lower() == model_name.lower():
                self.current_model = model
                self.model_history.append((model.name, datetime.now()))
                return True
        return False
    
    def benchmark_model(self, model_name: str, test_prompt: str = "What is 2+2?") -> float:
        """Perform a basic benchmark on a model."""
        # This is a simplified benchmark - in a real implementation,
        # this would run more comprehensive tests
        import time
        
        start_time = time.time()
        try:
            # For now, just return a simulated score
            # In a real implementation, this would call the model
            # and measure response time, accuracy, etc.
            score = 0.5  # Placeholder score
            
            # Update model info with benchmark score
            for model in self.available_models:
                if model.name == model_name:
                    model.benchmark_score = score
                    break
            
            return score
        except Exception:
            return 0.0
    
    def get_best_models(self, count: int = 5) -> List[ModelInfo]:
        """Get the best performing models based on benchmarks."""
        # Sort by benchmark score (descending), then by last used (descending)
        sorted_models = sorted(
            self.available_models,
            key=lambda m: (m.benchmark_score or 0, m.last_used or datetime.min),
            reverse=True
        )
        return sorted_models[:count]


# Global model manager instance
model_manager = ModelManager()