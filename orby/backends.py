"""Enhanced backend implementations for Orby with multiple inference engines."""
import requests
import json
import asyncio
from typing import List, Dict, Any, Optional, Generator, AsyncGenerator
from .backend import Backend, AsyncBackend
import time
from datetime import datetime


class OllamaBackend(Backend):
    """Enhanced Ollama backend implementation with streaming and benchmarking."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models from Ollama with detailed info."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("models", []):
                models.append({
                    "name": model.get("name", ""),
                    "modified_at": model.get("modified_at"),
                    "size": model.get("size", 0),
                    "digest": model.get("digest", ""),
                    "details": model.get("details", {})
                })
            return models
        except Exception as e:
            raise Exception(f"Failed to fetch models from Ollama: {str(e)}")

    def chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None, **kwargs) -> Any:
        """Chat with Ollama."""
        if not model:
            raise ValueError("Model must be specified for Ollama backend")

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        if stream:
            return self._stream_chat(payload)
        else:
            return self._non_stream_chat(payload)

    def _stream_chat(self, payload: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Stream chat response from Ollama with timing and metadata."""
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=30
            )
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("done"):
                            # Add timing information
                            data["timing"] = {
                                "total_time": time.time() - start_time,
                                "timestamp": datetime.now().isoformat()
                            }
                            yield data
                            break
                        message = data.get("message", {})
                        content = message.get("content", "")
                        if content:
                            # Add timing information to each chunk
                            data["timing"] = {
                                "elapsed_time": time.time() - start_time,
                                "timestamp": datetime.now().isoformat()
                            }
                            yield data
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            raise Exception(f"Streaming error: {str(e)}")

    def _non_stream_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Non-streaming chat response from Ollama with metadata."""
        try:
            start_time = time.time()
            # Create a copy of the payload and set stream to False explicitly
            payload_copy = payload.copy()
            payload_copy['stream'] = False

            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload_copy,
                timeout=30
            )
            response.raise_for_status()
            end_time = time.time()

            # Check if response is JSON or stream
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                data = response.json()
                # Add timing and metadata
                data["timing"] = {
                    "total_time": end_time - start_time,
                    "timestamp": datetime.now().isoformat()
                }
                data["model_info"] = {
                    "model": payload.get("model"),
                    "backend": "ollama"
                }
                return data
            else:
                # Handle case where it's still returning stream format
                lines = response.text.strip().split('\n')
                content = ""
                for line in lines:
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # Remove "data: " prefix
                            if data.get("done"):
                                break
                            message = data.get("message", {})
                            content += message.get("content", "")
                        except json.JSONDecodeError:
                            continue
                
                return {
                    "message": {"content": content, "role": "assistant"},
                    "model": payload.get("model"),
                    "done": True,
                    "timing": {
                        "total_time": end_time - start_time,
                        "timestamp": datetime.now().isoformat()
                    },
                    "model_info": {
                        "model": payload.get("model"),
                        "backend": "ollama"
                    }
                }
        except Exception as e:
            raise Exception(f"Chat error: {str(e)}")


class LMStudioBackend(Backend):
    """Enhanced LM Studio backend implementation."""
    
    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Check if LM Studio is accessible."""
        try:
            response = self.session.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models from LM Studio with detailed info."""
        try:
            response = self.session.get(f"{self.base_url}/v1/models", timeout=10)
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("data", []):
                models.append({
                    "name": model.get("id", ""),
                    "object": model.get("object", ""),
                    "created": model.get("created", 0),
                    "owned_by": model.get("owned_by", "")
                })
            return models
        except Exception as e:
            raise Exception(f"Failed to fetch models from LM Studio: {str(e)}")

    def chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None, **kwargs) -> Any:
        """Chat with LM Studio."""
        # For LM Studio, we typically use a default model if none is specified
        if not model:
            # We'll use a placeholder; in practice, LM Studio might have a default model
            # Or we can list models and pick the first one
            available_models = self.list_models()
            if available_models:
                model = available_models[0]["name"]
            else:
                raise ValueError("No model specified and no models available from LM Studio")

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        if stream:
            return self._stream_chat(payload)
        else:
            return self._non_stream_chat(payload)

    def _stream_chat(self, payload: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Stream chat response from LM Studio with timing."""
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                stream=True,
                timeout=30
            )
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        if data.get("choices"):
                            choice = data["choices"][0]
                            if choice.get("finish_reason"):
                                # Add timing information
                                data["timing"] = {
                                    "total_time": time.time() - start_time,
                                    "timestamp": datetime.now().isoformat()
                                }
                                yield data
                                break
                            content = choice.get("delta", {}).get("content", "")
                            if content:
                                # Add timing information to each chunk
                                data["timing"] = {
                                    "elapsed_time": time.time() - start_time,
                                    "timestamp": datetime.now().isoformat()
                                }
                                yield data
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            raise Exception(f"Streaming error: {str(e)}")

    def _non_stream_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Non-streaming chat response from LM Studio with metadata."""
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            end_time = time.time()
            
            # Add timing and metadata
            data["timing"] = {
                "total_time": end_time - start_time,
                "timestamp": datetime.now().isoformat()
            }
            data["model_info"] = {
                "model": payload.get("model"),
                "backend": "lmstudio"
            }
            
            return data
        except Exception as e:
            raise Exception(f"Chat error: {str(e)}")


class HuggingFaceBackend(Backend):
    """Enhanced Hugging Face backend implementation using local transformers."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.pipeline = None
        self.model_name = model_name
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize the transformers pipeline."""
        try:
            from transformers import pipeline
            # We'll create a general pipeline that can work with various models
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device_map="auto"  # Use GPU if available
            )
        except ImportError:
            raise Exception("transformers library is required for Hugging Face backend")
        except Exception as e:
            raise Exception(f"Failed to initialize Hugging Face pipeline: {str(e)}")

    def health_check(self) -> bool:
        """Check if Hugging Face backend is initialized."""
        return self.pipeline is not None

    def list_models(self) -> List[Dict[str, Any]]:
        """List models that can be used with this backend."""
        # For local transformers, return the model being used and some alternatives
        return [
            {"name": self.model_name, "type": "chat"},
            {"name": "gpt2", "type": "text-generation"},
            {"name": "distilgpt2", "type": "text-generation"},
            {"name": "microsoft/DialoGPT-medium", "type": "chat"},
            {"name": "facebook/opt-2.7b", "type": "text-generation"}
        ]

    def chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None, **kwargs) -> Any:
        """Chat using Hugging Face transformers."""
        try:
            start_time = time.time()
            
            # Use the provided model or the default one
            model_name = model or self.model_name

            if model != self.model_name:
                # Reinitialize pipeline if a different model is requested
                self.model_name = model_name
                self._initialize_pipeline()

            # Format messages for the model
            formatted_prompt = self._format_messages(messages)

            # Set generation parameters
            max_length = kwargs.get('max_length', 250)
            temperature = kwargs.get('temperature', 0.7)
            do_sample = kwargs.get('do_sample', True)

            # Generate response
            outputs = self.pipeline(
                formatted_prompt,
                max_length=max_length,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=50256,  # Common pad token id for many models
                return_full_text=False
            )
            
            end_time = time.time()

            if outputs:
                return {
                    "generated_text": outputs[0]['generated_text'],
                    "timing": {
                        "total_time": end_time - start_time,
                        "timestamp": datetime.now().isoformat()
                    },
                    "model_info": {
                        "model": self.model_name,
                        "backend": "huggingface"
                    }
                }
            return {
                "generated_text": "No response generated.",
                "timing": {
                    "total_time": end_time - start_time,
                    "timestamp": datetime.now().isoformat()
                },
                "model_info": {
                    "model": self.model_name,
                    "backend": "huggingface"
                }
            }
        except Exception as e:
            raise Exception(f"Hugging Face inference error: {str(e)}")

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Hugging Face pipeline."""
        # For chat models we need to convert the messages appropriately
        # This is a simple conversion, but different models might need different formats
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        # Join with newlines
        return "\n".join(formatted) + "\nAssistant:"


# Async versions of the backends
class AsyncOllamaBackend(OllamaBackend, AsyncBackend):
    """Async version of Ollama backend."""
    
    async def health_check(self) -> bool:
        """Async check if Ollama is accessible."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=5) as response:
                    return response.status == 200
        except Exception:
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """Async list all available models from Ollama."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

                    models = []
                    for model in data.get("models", []):
                        models.append({
                            "name": model.get("name", ""),
                            "modified_at": model.get("modified_at"),
                            "size": model.get("size", 0),
                            "digest": model.get("digest", ""),
                            "details": model.get("details", {})
                        })
                    return models
        except Exception as e:
            raise Exception(f"Failed to fetch models from Ollama: {str(e)}")

    async def chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Async chat with Ollama."""
        if not model:
            raise ValueError("Model must be specified for Ollama backend")

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        if stream:
            async for chunk in self._async_stream_chat(payload):
                yield chunk
        else:
            result = await self._async_non_stream_chat(payload)
            yield result

    async def _async_stream_chat(self, payload: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Async stream chat response from Ollama."""
        try:
            import aiohttp
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/chat", json=payload, timeout=30) as response:
                    response.raise_for_status()
                    
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line:
                            try:
                                data = json.loads(decoded_line)
                                if data.get("done"):
                                    # Add timing information
                                    data["timing"] = {
                                        "total_time": time.time() - start_time,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    yield data
                                    break
                                message = data.get("message", {})
                                content = message.get("content", "")
                                if content:
                                    # Add timing information to each chunk
                                    data["timing"] = {
                                        "elapsed_time": time.time() - start_time,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    yield data
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            raise Exception(f"Streaming error: {str(e)}")

    async def _async_non_stream_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Async non-streaming chat response from Ollama."""
        try:
            import aiohttp
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                # Create a copy of the payload and set stream to False explicitly
                payload_copy = payload.copy()
                payload_copy['stream'] = False

                async with session.post(f"{self.base_url}/api/chat", json=payload_copy, timeout=30) as response:
                    response.raise_for_status()
                    end_time = time.time()

                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        # Add timing and metadata
                        data["timing"] = {
                            "total_time": end_time - start_time,
                            "timestamp": datetime.now().isoformat()
                        }
                        data["model_info"] = {
                            "model": payload.get("model"),
                            "backend": "ollama"
                        }
                        return data
                    else:
                        # Handle case where it's still returning stream format
                        text = await response.text()
                        lines = text.strip().split('\n')
                        content = ""
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])  # Remove "data: " prefix
                                    if data.get("done"):
                                        break
                                    message = data.get("message", {})
                                    content += message.get("content", "")
                                except json.JSONDecodeError:
                                    continue
                        
                        return {
                            "message": {"content": content, "role": "assistant"},
                            "model": payload.get("model"),
                            "done": True,
                            "timing": {
                                "total_time": end_time - start_time,
                                "timestamp": datetime.now().isoformat()
                            },
                            "model_info": {
                                "model": payload.get("model"),
                                "backend": "ollama"
                            }
                        }
        except Exception as e:
            raise Exception(f"Chat error: {str(e)}")


class AsyncLMStudioBackend(LMStudioBackend, AsyncBackend):
    """Async version of LM Studio backend."""
    
    async def health_check(self) -> bool:
        """Async check if LM Studio is accessible."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/v1/models", timeout=5) as response:
                    return response.status == 200
        except Exception:
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """Async list all available models from LM Studio."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/v1/models", timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

                    models = []
                    for model in data.get("data", []):
                        models.append({
                            "name": model.get("id", ""),
                            "object": model.get("object", ""),
                            "created": model.get("created", 0),
                            "owned_by": model.get("owned_by", "")
                        })
                    return models
        except Exception as e:
            raise Exception(f"Failed to fetch models from LM Studio: {str(e)}")

    async def chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Async chat with LM Studio."""
        # For LM Studio, we typically use a default model if none is specified
        if not model:
            # We'll use a placeholder; in practice, LM Studio might have a default model
            # Or we can list models and pick the first one
            available_models = await self.list_models()
            if available_models:
                model = available_models[0]["name"]
            else:
                raise ValueError("No model specified and no models available from LM Studio")

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        if stream:
            async for chunk in self._async_stream_chat(payload):
                yield chunk
        else:
            result = await self._async_non_stream_chat(payload)
            yield result

    async def _async_stream_chat(self, payload: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Async stream chat response from LM Studio."""
        try:
            import aiohttp
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=30) as response:
                    response.raise_for_status()

                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line and decoded_line.startswith("data: "):
                            try:
                                data = json.loads(decoded_line[6:])  # Remove "data: " prefix
                                if data.get("choices"):
                                    choice = data["choices"][0]
                                    if choice.get("finish_reason"):
                                        # Add timing information
                                        data["timing"] = {
                                            "total_time": time.time() - start_time,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        yield data
                                        break
                                    content = choice.get("delta", {}).get("content", "")
                                    if content:
                                        # Add timing information to each chunk
                                        data["timing"] = {
                                            "elapsed_time": time.time() - start_time,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        yield data
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            raise Exception(f"Streaming error: {str(e)}")

    async def _async_non_stream_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Async non-streaming chat response from LM Studio."""
        try:
            import aiohttp
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=30) as response:
                    response.raise_for_status()
                    data = await response.json()
                    end_time = time.time()
                    
                    # Add timing and metadata
                    data["timing"] = {
                        "total_time": end_time - start_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    data["model_info"] = {
                        "model": payload.get("model"),
                        "backend": "lmstudio"
                    }
                    
                    return data
        except Exception as e:
            raise Exception(f"Chat error: {str(e)}")


# Enhanced backend manager with benchmarking capabilities
class EnhancedBackendManager:
    """Enhanced backend manager with model benchmarking and selection."""
    
    def __init__(self):
        self._backends = {}
        self._performance_cache = {}  # Cache for model performance data
    
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
        """Get models from all registered backends with enhanced info."""
        result = {}
        for name, backend in self._backends.items():
            try:
                if hasattr(backend, 'list_models') and asyncio.iscoroutinefunction(backend.list_models.__func__ if hasattr(backend.list_models, '__func__') else backend.list_models):
                    models = await backend.list_models()
                else:
                    models = backend.list_models()
                result[name] = models
            except Exception as e:
                result[name] = [{"name": f"Error: {str(e)}", "error": True}]
        return result
    
    def benchmark_model(self, backend_name: str, model_name: str, test_prompt: str = "What is 2+2?") -> Dict[str, Any]:
        """Benchmark a specific model."""
        try:
            backend = self._backends.get(backend_name)
            if not backend:
                return {"error": f"Backend '{backend_name}' not found"}
            
            # Create a simple test message
            messages = [{"role": "user", "content": test_prompt}]
            
            # Measure response time
            start_time = time.time()
            response = backend.chat(messages, model=model_name)
            end_time = time.time()
            
            # Calculate metrics
            response_time = end_time - start_time
            response_length = len(str(response.get("message", {}).get("content", "")))
            tokens_per_second = response_length / max(response_time, 0.001)  # Avoid division by zero
            
            benchmark_result = {
                "model": model_name,
                "backend": backend_name,
                "response_time": response_time,
                "response_length": response_length,
                "tokens_per_second": tokens_per_second,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            cache_key = f"{backend_name}:{model_name}"
            self._performance_cache[cache_key] = benchmark_result
            
            return benchmark_result
        except Exception as e:
            return {"error": str(e)}
    
    def get_cached_performance(self, backend_name: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Get cached performance data for a model."""
        cache_key = f"{backend_name}:{model_name}"
        return self._performance_cache.get(cache_key)
    
    def rank_models(self) -> List[Dict[str, Any]]:
        """Rank all available models by performance."""
        rankings = []
        
        # Collect all models with cached performance
        for cache_key, perf_data in self._performance_cache.items():
            if "error" not in perf_data:
                rankings.append(perf_data)
        
        # Sort by tokens per second (descending)
        rankings.sort(key=lambda x: x.get("tokens_per_second", 0), reverse=True)
        return rankings