"""Enhanced backend interface for Orby with benchmarking and performance metrics."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator, AsyncGenerator
import asyncio
from datetime import datetime


class Backend(ABC):
    """Enhanced abstract base class for backend implementations."""
    
    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models from this backend with detailed information.
        
        Returns:
            List of dictionaries containing model information:
            {
                "name": str,
                "size": int (bytes),
                "modified_at": str (ISO format),
                "parameters": str,
                "details": Dict[str, Any]
            }
        """
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None, **kwargs) -> Any:
        """
        Chat with the backend.
        
        Args:
            messages: List of message dictionaries with "role" and "content"
            stream: Whether to stream the response
            model: Model name to use
            **kwargs: Additional parameters for the model
            
        Returns:
            Response dictionary with:
            {
                "message": {"content": str, "role": str},
                "model": str,
                "done": bool,
                "timing": {"total_time": float, "timestamp": str},
                "model_info": {"model": str, "backend": str}
            }
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the backend is accessible."""
        pass


class AsyncBackend(ABC):
    """Enhanced async version of backend interface."""
    
    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models from this backend with detailed information.
        
        Returns:
            List of dictionaries containing model information.
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async chat with the backend.
        
        Yields:
            Response dictionaries with timing and metadata.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Async check if the backend is accessible."""
        pass


class BackendManager:
    """Enhanced manager for multiple backends with performance tracking."""
    
    def __init__(self):
        self._backends: Dict[str, Backend] = {}
        self._performance_metrics: Dict[str, Dict[str, Any]] = {}
        
    def register_backend(self, name: str, backend: Backend):
        """Register a backend."""
        self._backends[name] = backend
        
    def get_backend(self, name: str) -> Optional[Backend]:
        """Get a registered backend by name."""
        return self._backends.get(name)
        
    def list_backends(self) -> List[str]:
        """List all registered backend names."""
        return list(self._backends.keys())
        
    async def list_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get detailed models from all registered backends."""
        result = {}
        for name, backend in self._backends.items():
            try:
                # Check if backend has async method
                if hasattr(backend, 'list_models'):
                    if asyncio.iscoroutinefunction(getattr(backend.list_models, '__call__', backend.list_models)):
                        models = await backend.list_models()
                    else:
                        models = backend.list_models()
                else:
                    models = []
                result[name] = models
            except Exception as e:
                result[name] = [{"name": f"Error: {str(e)}", "error": True}]
        return result
    
    def record_performance_metric(self, backend_name: str, model_name: str, metric: Dict[str, Any]):
        """Record performance metrics for a model."""
        cache_key = f"{backend_name}:{model_name}"
        if cache_key not in self._performance_metrics:
            self._performance_metrics[cache_key] = []
        self._performance_metrics[cache_key].append(metric)
        
        # Keep only the last 100 metrics to prevent memory growth
        if len(self._performance_metrics[cache_key]) > 100:
            self._performance_metrics[cache_key] = self._performance_metrics[cache_key][-100:]
    
    def get_performance_metrics(self, backend_name: str, model_name: str) -> List[Dict[str, Any]]:
        """Get performance metrics for a model."""
        cache_key = f"{backend_name}:{model_name}"
        return self._performance_metrics.get(cache_key, [])
    
    def get_average_performance(self, backend_name: str, model_name: str) -> Optional[Dict[str, float]]:
        """Get average performance metrics for a model."""
        metrics = self.get_performance_metrics(backend_name, model_name)
        if not metrics:
            return None
            
        total_time = sum(m.get("response_time", 0) for m in metrics)
        total_tokens = sum(m.get("response_length", 0) for m in metrics)
        count = len(metrics)
        
        if count == 0:
            return None
            
        return {
            "avg_response_time": total_time / count,
            "avg_response_length": total_tokens / count,
            "throughput": total_tokens / max(total_time, 0.001) if total_time > 0 else 0,
            "sample_count": count
        }
    
    def rank_models_by_performance(self) -> List[Dict[str, Any]]:
        """Rank all models by their performance metrics."""
        rankings = []
        
        for cache_key in self._performance_metrics:
            if ":" in cache_key:
                backend_name, model_name = cache_key.split(":", 1)
                avg_perf = self.get_average_performance(backend_name, model_name)
                if avg_perf:
                    rankings.append({
                        "backend": backend_name,
                        "model": model_name,
                        "avg_response_time": avg_perf["avg_response_time"],
                        "throughput": avg_perf["throughput"],
                        "samples": avg_perf["sample_count"]
                    })
        
        # Sort by throughput (higher is better)
        rankings.sort(key=lambda x: x.get("throughput", 0), reverse=True)
        return rankings