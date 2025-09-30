"""Plugin system for Orby."""
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Type, Any, Callable
from abc import ABC, abstractmethod
import asyncio


class ToolPlugin(ABC):
    """Base class for tool plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass


class PluginManager:
    """Manages plugins for Orby."""
    
    def __init__(self):
        self._tools: Dict[str, ToolPlugin] = {}
        self._load_builtin_tools()
        self._load_user_plugins()
    
    def _load_builtin_tools(self):
        """Load built-in tools."""
        from ..tools.shell import ShellTool
        from ..tools.code import CodeTool
        from ..tools.file import FileTool
        from ..tools.web import WebTool
        
        builtin_tools = [
            ShellTool(),
            CodeTool(),
            FileTool(),
            WebTool()
        ]
        
        for tool in builtin_tools:
            self._tools[tool.name] = tool
    
    def _load_user_plugins(self):
        """Load user plugins from the plugins directory."""
        plugins_dir = Path.home() / ".orby" / "plugins"
        plugins_dir.mkdir(exist_ok=True)
        
        # Look for Python files in the plugins directory
        for plugin_file in plugins_dir.glob("*.py"):
            self._load_plugin_from_file(plugin_file)
    
    def _load_plugin_from_file(self, plugin_file: Path):
        """Load a plugin from a Python file."""
        try:
            spec = importlib.util.spec_from_file_location("plugin_module", plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all ToolPlugin subclasses in the module
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    inspect.isclass(obj) and
                    issubclass(obj, ToolPlugin) and
                    obj != ToolPlugin
                ):
                    try:
                        tool_instance = obj()
                        self._tools[tool_instance.name] = tool_instance
                    except Exception:
                        # Skip tools that can't be instantiated
                        continue
        except Exception:
            # If there's an error loading the plugin, skip it
            pass
    
    def register_tool(self, tool: ToolPlugin):
        """Register a custom tool."""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> ToolPlugin:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self._tools.keys())
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return {
                "status": "error",
                "error": f"Tool '{name}' not found"
            }
        
        # Run the async execute method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(tool.execute(**kwargs))
        finally:
            loop.close()
        
        return result


class PluginAPI:
    """API for creating plugins."""
    
    @staticmethod
    def create_plugin(name: str, description: str, execute_func: Callable):
        """Create a simple plugin from a function."""
        
        class DynamicPlugin(ToolPlugin):
            @property
            def name(self) -> str:
                return name
            
            @property
            def description(self) -> str:
                return description
            
            async def execute(self, **kwargs) -> Dict[str, Any]:
                return await execute_func(**kwargs)
        
        return DynamicPlugin()


# Global plugin manager instance
plugin_manager = PluginManager()