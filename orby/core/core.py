"""Enhanced core Orby application logic with agentic capabilities and local AI features."""
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml
from datetime import datetime
import time


class ToolPermission(Enum):
    """Permission levels for tools."""
    DENY = "deny"
    ALLOW_ONCE = "allow_once"
    ALLOW_ALWAYS = "allow_always"


class ToolCallStatus(Enum):
    """Status of tool calls."""
    PENDING = "pending"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolCall:
    """Represents a tool call with enhanced metadata."""
    name: str
    arguments: Dict[str, Any]
    status: ToolCallStatus = ToolCallStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    call_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    """Represents a message in the conversation with enhanced metadata."""
    role: str  # 'user', 'assistant', 'tool'
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    model_info: Optional[Dict[str, str]] = None
    timing: Optional[Dict[str, float]] = None


@dataclass
class AgentThought:
    """Represents the agent's internal reasoning process."""
    reasoning_steps: List[str] = field(default_factory=list)
    tool_selection: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Tool:
    """Base class for tools that agents can use with enhanced capabilities."""
    
    def __init__(self, name: str, description: str, permissions_required: List[str] = None):
        self.name = name
        self.description = description
        self.permissions_required = permissions_required or []
        self.is_dangerous = any(perm in ["execute", "write", "delete", "network"] 
                               for perm in self.permissions_required)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given arguments."""
        # Add timing and metadata
        start_time = time.time()
        try:
            result = await self._execute_impl(**kwargs)
            end_time = time.time()
            
            # Add timing and metadata to result
            if isinstance(result, dict):
                result["timing"] = {
                    "execution_time": end_time - start_time,
                    "start_time": start_time,
                    "end_time": end_time
                }
                result["tool_info"] = {
                    "name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
        except Exception as e:
            end_time = time.time()
            return {
                "status": "error",
                "error": str(e),
                "timing": {
                    "execution_time": end_time - start_time,
                    "start_time": start_time,
                    "end_time": end_time
                },
                "tool_info": {
                    "name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _execute_impl(self, **kwargs) -> Dict[str, Any]:
        """Implementation of tool execution."""
        raise NotImplementedError
    
    def requires_confirmation(self) -> bool:
        """Check if this tool requires user confirmation."""
        return self.is_dangerous


class ToolRegistry:
    """Enhanced registry for managing tools with permissions and categories."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._tool_categories: Dict[str, List[str]] = {}
        self._permissions: Dict[str, ToolPermission] = {}
        self._load_builtin_tools()
    
    def _load_builtin_tools(self):
        """Load built-in tools."""
        builtin_tool_classes = [
            ("shell", "ShellTool", "system"),
            ("code", "CodeTool", "development"),
            ("file", "FileTool", "filesystem"),
            ("web", "WebTool", "network"),
            ("vision", "VisionTool", "multimodal"),
            ("voice", "VoiceTool", "multimodal"),
        ]
        
        for tool_name, tool_class_name, category in builtin_tool_classes:
            try:
                # Import the tool dynamically to handle potential missing dependencies
                if tool_name == "shell":
                    from ..tools.shell import ShellTool as ToolClass
                elif tool_name == "code":
                    from ..tools.code import CodeTool as ToolClass
                elif tool_name == "file":
                    from ..tools.file import FileTool as ToolClass
                elif tool_name == "web":
                    from ..tools.web import WebTool as ToolClass
                elif tool_name == "vision":
                    from ..tools.vision import VisionTool as ToolClass
                elif tool_name == "voice":
                    from ..tools.voice import VoiceTool as ToolClass
                else:
                    continue  # Unknown tool type
                
                tool = ToolClass()
                self._tools[tool.name] = tool
                
                # Categorize tool
                if category not in self._tool_categories:
                    self._tool_categories[category] = []
                self._tool_categories[category].append(tool.name)
                
            except ImportError as e:
                print(f"Warning: Could not import {tool_class_name} ({e}), skipping tool")
            except Exception as e:
                print(f"Warning: Could not initialize {tool_class_name} ({e}), skipping tool")
    
    def register_tool(self, tool: Tool, category: str = "general"):
        """Register a custom tool."""
        self._tools[tool.name] = tool
        if category not in self._tool_categories:
            self._tool_categories[category] = []
        self._tool_categories[category].append(tool.name)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self._tools.keys())
    
    def list_tools_by_category(self, category: str = None) -> List[str]:
        """List tools by category."""
        if category:
            return self._tool_categories.get(category, [])
        return list(self._tools.keys())
    
    def get_tool_categories(self) -> List[str]:
        """Get all tool categories."""
        return list(self._tool_categories.keys())
    
    def set_tool_permission(self, tool_name: str, permission: ToolPermission):
        """Set permission for a tool."""
        self._permissions[tool_name] = permission
    
    def get_tool_permission(self, tool_name: str) -> ToolPermission:
        """Get permission for a tool."""
        return self._permissions.get(tool_name, ToolPermission.DENY)
    
    def tool_requires_confirmation(self, tool_name: str) -> bool:
        """Check if a tool requires user confirmation."""
        tool = self.get_tool(tool_name)
        if tool:
            return tool.requires_confirmation()
        return False


class Agent:
    """Enhanced intelligent agent that can reason, use tools, and maintain context."""
    
    def __init__(self, model_name: str = "default", tools: Optional[ToolRegistry] = None, system_prompt: Optional[str] = None):
        self.model_name = model_name
        self.tools = tools or ToolRegistry()
        self.conversation_history: List[AgentMessage] = []
        self.thought_history: List[AgentThought] = []
        self.session_id = None
        self.context_window_size = 10  # Number of recent messages to keep in context
        
        # Add system prompt as first message if provided
        if system_prompt:
            system_msg = AgentMessage(
                role="system", 
                content=system_prompt,
                timestamp=datetime.now()
            )
            self.conversation_history.append(system_msg)
        
    async def process_message(self, user_input: str, context: Optional[str] = None) -> str:
        """Process a user message and return agent response with enhanced context."""
        try:
            # Get the system prompt from config if not already in conversation history
            from ..config import load_config
            try:
                config = load_config()
            except Exception:
                # If config loading fails, proceed without it
                config = {}
            
            # Add system prompt as first message if not already present
            if not self.conversation_history or self.conversation_history[0].role != "system":
                system_prompt = config.get('system_prompt')
                if system_prompt:
                    system_msg = AgentMessage(
                        role="system",
                        content=system_prompt,
                        timestamp=datetime.now()
                    )
                    self.conversation_history.insert(0, system_msg)
            
            # Add user message to history with timestamp
            user_msg = AgentMessage(
                role="user", 
                content=user_input,
                timestamp=datetime.now()
            )
            self.conversation_history.append(user_msg)
            
            # Trim conversation history to maintain context window
            if len(self.conversation_history) > self.context_window_size * 2:
                # Keep the system message (if exists) and last N messages
                system_msg = None
                if self.conversation_history[0].role == "system":
                    system_msg = self.conversation_history[0]
                    recent_messages = self.conversation_history[-(self.context_window_size * 2 - 1):]
                    self.conversation_history = [system_msg] + recent_messages
                else:
                    self.conversation_history = self.conversation_history[-(self.context_window_size * 2):]
            
            # Here we would call the LLM to get a response
            # For now, we'll simulate with a more sophisticated response
            agent_response = await self._get_enhanced_agent_response(user_input, context)
            
            # Add agent response to history
            agent_msg = AgentMessage(
                role="assistant", 
                content=agent_response,
                timestamp=datetime.now()
            )
            self.conversation_history.append(agent_msg)
            
            return agent_response
        except Exception as e:
            # If any processing fails, return a helpful error message
            error_msg = f"Error processing message: {str(e)}"
            import traceback
            print(f"Agent processing error: {error_msg}\n{traceback.format_exc()}")
            return f"Sorry, I encountered an error while processing your request: {str(e)}"

    async def _get_enhanced_agent_response(self, user_input: str, context: Optional[str] = None) -> str:
        """Get enhanced response from the agent with context awareness."""
        # Combine user input with context if available
        enhanced_input = user_input
        if context:
            enhanced_input = f"Context:\n{context}\n\nUser Query:\n{user_input}"
        
        # Simple example: if user asks to execute a shell command,
        # return a tool call
        if "show files" in user_input.lower() or "list directory" in user_input.lower():
            shell_tool = self.tools.get_tool("shell")
            if shell_tool:
                return f"I can help you list files in the current directory. Would you like me to run 'ls -la'?"
        
        elif "execute" in user_input.lower() and ("command" in user_input.lower() or "shell" in user_input.lower()):
            return f"I can execute shell commands for you, but I'll need your approval first for security. What command would you like to run?"
        
        elif "search" in user_input.lower() or "find" in user_input.lower():
            return f"I can search for information or files for you. Would you like me to help with a specific search?"
        
        elif "code" in user_input.lower() or "program" in user_input.lower():
            return f"I can help you with coding tasks. What programming language are you working with?"
        
        elif "explain" in user_input.lower() or "what is" in user_input.lower():
            return f"I'd be happy to help explain that. Could you provide a bit more detail about what you'd like to know?"
        
        else:
            # Default response for general queries
            return f"Orby received: {user_input}. I can help with tools, code, files, web searches, and more. What would you like assistance with?"
    
    async def process_tool_calls(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Process a list of tool calls with enhanced error handling and timing."""
        results = []
        for tool_call in tool_calls:
            tool = self.tools.get_tool(tool_call.name)
            if not tool:
                error_result = {
                    "status": "error",
                    "error": f"Tool '{tool_call.name}' not found",
                    "tool_call": tool_call.name
                }
                results.append(error_result)
                continue
            
            try:
                # Record start time
                start_time = time.time()
                tool_call.timestamp = datetime.now()
                
                # Execute tool
                result = await tool.execute(**tool_call.arguments)
                
                # Record execution time
                end_time = time.time()
                tool_call.execution_time = end_time - start_time
                tool_call.status = ToolCallStatus.SUCCESS
                tool_call.result = result
                
                # Add tool call metadata to result
                if isinstance(result, dict):
                    result["tool_call_metadata"] = {
                        "tool_name": tool_call.name,
                        "execution_time": tool_call.execution_time,
                        "timestamp": tool_call.timestamp.isoformat()
                    }
                
                results.append(result)
            except asyncio.TimeoutError:
                # Handle timeout specifically
                end_time = time.time()
                tool_call.execution_time = end_time - start_time if 'start_time' in locals() else 0
                tool_call.status = ToolCallStatus.ERROR
                tool_call.error = f"Tool '{tool_call.name}' execution timed out"
                
                timeout_result = {
                    "status": "error",
                    "error": f"Tool execution timed out after {tool_call.execution_time:.2f} seconds",
                    "tool_call": tool_call.name,
                    "tool_call_metadata": {
                        "tool_name": tool_call.name,
                        "execution_time": tool_call.execution_time,
                        "timestamp": tool_call.timestamp.isoformat() if tool_call.timestamp else None
                    }
                }
                results.append(timeout_result)
            except Exception as e:
                # Record error
                end_time = time.time()
                execution_time = end_time - start_time if 'start_time' in locals() else 0
                tool_call.execution_time = execution_time
                tool_call.status = ToolCallStatus.ERROR
                tool_call.error = str(e)
                
                error_result = {
                    "status": "error",
                    "error": str(e),
                    "tool_call": tool_call.name,
                    "tool_call_metadata": {
                        "tool_name": tool_call.name,
                        "execution_time": tool_call.execution_time,
                        "timestamp": tool_call.timestamp.isoformat() if tool_call.timestamp else None
                    }
                }
                results.append(error_result)
        
        return results
    
    def get_conversation_context(self) -> List[Dict[str, str]]:
        """Get conversation context for LLM."""
        context = []
        for msg in self.conversation_history[-self.context_window_size:]:
            context.append({
                "role": msg.role,
                "content": msg.content
            })
        return context
    
    def add_thought_process(self, thought: AgentThought):
        """Add a thought process to the agent's history."""
        self.thought_history.append(thought)
        
        # Keep only recent thoughts
        if len(self.thought_history) > 100:
            self.thought_history = self.thought_history[-100:]


class OrbyApp:
    """Enhanced main Orby application class with multi-backend support."""
    
    def __init__(self):
        self.agent: Optional[Agent] = None
        self.config = self._load_config()
        self.tools = ToolRegistry()
        self._initialize_agent()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        config_path = Path.home() / ".orby" / "config.yml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        else:
            return {
                'default_model': 'llama3.1:latest',
                'default_backend': 'ollama',
                'ollama_url': 'http://localhost:11434',
                'lmstudio_url': 'http://localhost:1234'
            }

    def _initialize_agent(self):
        """Initialize the agent."""
        model_name = self.config.get('default_model', 'llama3.1:latest')
        system_prompt = self.config.get('system_prompt')
        
        # Create the agent with tools and system prompt
        try:
            self.agent = Agent(model_name=model_name, tools=self.tools, system_prompt=system_prompt)
        except Exception as e:
            # If agent initialization fails, create with minimal configuration
            print(f"Warning: Agent initialization failed ({e}), creating with defaults")
            self.agent = Agent(model_name=model_name, tools=self.tools)

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models from all backends."""
        from ..backend import BackendManager
        backend_manager = BackendManager()
        
        # Register backends with config URLs
        if self.config.get('ollama_url'):
            from ..backends import OllamaBackend
            backend_manager.register_backend('ollama', OllamaBackend(self.config['ollama_url']))
        
        if self.config.get('lmstudio_url'):
            from ..backends import LMStudioBackend
            backend_manager.register_backend('lmstudio', LMStudioBackend(self.config['lmstudio_url']))
        
        # Return the sync version for now
        result = {}
        for name, backend in backend_manager._backends.items():
            try:
                models = backend.list_models()
                result[name] = models
            except Exception as e:
                result[name] = [f"Error: {str(e)}"]
        return result
    
    async def benchmark_models(self, test_prompt: str = "What is 2+2?") -> List[Dict[str, Any]]:
        """Benchmark all available models."""
        from ..utils.detection import detect_all_local_models
        from ..backends import EnhancedBackendManager
        
        # Detect all models
        detected_models = detect_all_local_models()
        benchmark_results = []
        
        # Create enhanced backend manager for benchmarking
        backend_manager = EnhancedBackendManager()
        
        # Benchmark each model
        for backend_name, models in detected_models.items():
            for model_info in models:
                model_name = model_info.get("name", "")
                if model_name:
                    try:
                        # Benchmark the model
                        score = backend_manager.benchmark_model(backend_name, model_name, test_prompt)
                        benchmark_results.append({
                            "model": model_name,
                            "backend": backend_name,
                            "score": score,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception:
                        # If benchmarking fails, continue with next model
                        continue
        
        # Sort by score (descending)
        benchmark_results.sort(key=lambda x: x.get("score", {}).get("tokens_per_second", 0), reverse=True)
        return benchmark_results
    
    def get_tool_recommendations(self, user_query: str) -> List[str]:
        """Get recommended tools based on user query."""
        recommendations = []
        
        query_lower = user_query.lower()
        
        # Recommend tools based on keywords
        if any(word in query_lower for word in ["shell", "command", "execute", "run"]):
            recommendations.append("shell")
        if any(word in query_lower for word in ["code", "program", "script", "python", "javascript"]):
            recommendations.append("code")
        if any(word in query_lower for word in ["file", "read", "write", "directory", "folder"]):
            recommendations.append("file")
        if any(word in query_lower for word in ["web", "search", "browse", "internet", "url"]):
            recommendations.append("web")
        if any(word in query_lower for word in ["image", "picture", "photo", "vision", "screenshot"]):
            recommendations.append("vision")
        if any(word in query_lower for word in ["audio", "voice", "speech", "sound", "record"]):
            recommendations.append("voice")
        
        return recommendations
    
    def get_context_aware_response(self, user_input: str, project_context: Optional[str] = None) -> str:
        """Get a context-aware response."""
        if self.agent:
            # Process with agent
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    self.agent.process_message(user_input, project_context)
                )
                return response
            finally:
                loop.close()
        else:
            return f"Orby received: {user_input}. I can help with tools, code, files, and more."