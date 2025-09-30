"""Tool registry and built-in tools for Orby."""
import subprocess
import sys
import os
import importlib.util
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path


class Tool(ABC):
    """Abstract base class for tools."""
    
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
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass


class PythonTool(Tool):
    """Tool to execute Python code."""
    
    @property
    def name(self) -> str:
        return "python"
    
    @property
    def description(self) -> str:
        return "Execute Python code and return the result"
    
    def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """Execute Python code in a safe environment."""
        try:
            # Create a restricted environment for code execution
            local_vars = {}
            global_vars = {"__builtins__": {
                "__import__": __import__,
                "abs": abs,
                "all": all,
                "any": any,
                "bool": bool,
                "chr": chr,
                "complex": complex,
                "dict": dict,
                "dir": dir,
                "divmod": divmod,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "format": format,
                "frozenset": frozenset,
                "hex": hex,
                "int": int,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "object": object,
                "oct": oct,
                "ord": ord,
                "pow": pow,
                "range": range,
                "repr": repr,
                "reversed": reversed,
                "round": round,
                "set": set,
                "slice": slice,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "type": type,
                "zip": zip,
                "print": print
            }}
            
            exec(code, global_vars, local_vars)
            
            # For now, just return the last computed value
            if local_vars:
                # Get the last assigned variable
                last_key = list(local_vars.keys())[-1]
                result = local_vars[last_key]
                return {"success": True, "result": str(result), "output": str(result)}
            else:
                return {"success": True, "result": "Code executed successfully", "output": "Code executed successfully"}
        
        except Exception as e:
            return {"success": False, "error": str(e), "output": str(e)}


class ShellTool(Tool):
    """Tool to execute shell commands."""
    
    @property
    def name(self) -> str:
        return "shell"
    
    @property
    def description(self) -> str:
        return "Execute shell commands and return the output"
    
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=kwargs.get('timeout', 30)
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {kwargs.get('timeout', 30)} seconds",
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }


class WebTool(Tool):
    """Tool to fetch web content."""
    
    @property
    def name(self) -> str:
        return "web"
    
    @property
    def description(self) -> str:
        return "Fetch content from a web URL"
    
    def execute(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetch content from a URL."""
        try:
            import requests
        except ImportError:
            return {
                "success": False,
                "error": "requests library not available",
                "content": ""
            }
        
        try:
            response = requests.get(url, timeout=kwargs.get('timeout', 10))
            response.raise_for_status()
            
            return {
                "success": True,
                "content": response.text,
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }


class FilesystemTool(Tool):
    """Tool for filesystem operations."""
    
    @property
    def name(self) -> str:
        return "filesystem"
    
    @property
    def description(self) -> str:
        return "Read, write, or list files in the filesystem"
    
    def execute(self, operation: str, path: str, **kwargs) -> Dict[str, Any]:
        """Perform filesystem operations."""
        try:
            if operation == "read":
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {
                    "success": True,
                    "operation": operation,
                    "path": path,
                    "content": content
                }
            elif operation == "list":
                if os.path.isdir(path):
                    files = os.listdir(path)
                    return {
                        "success": True,
                        "operation": operation,
                        "path": path,
                        "files": files
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Path is not a directory: {path}",
                        "operation": operation,
                        "path": path
                    }
            elif operation == "write":
                content = kwargs.get('content', '')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "success": True,
                    "operation": operation,
                    "path": path
                }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported operation: {operation}",
                    "operation": operation,
                    "path": path
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "path": path
            }


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._load_builtin_tools()
        self._load_plugin_tools()
    
    def _load_builtin_tools(self):
        """Load built-in tools."""
        builtin_tools = [
            PythonTool(),
            ShellTool(),
            WebTool(),
            FilesystemTool()
        ]
        
        for tool in builtin_tools:
            self._tools[tool.name] = tool
    
    def _load_plugin_tools(self):
        """Load tools from the plugins directory."""
        # Look for tools in ~/.orby/tools/
        tools_dir = Path.home() / ".orby" / "tools"
        
        if tools_dir.exists():
            for file_path in tools_dir.glob("*.py"):
                self._load_tools_from_file(file_path)
    
    def _load_tools_from_file(self, file_path: Path):
        """Load tools from a Python file."""
        try:
            spec = importlib.util.spec_from_file_location("tools_module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for Tool subclasses in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) and 
                    issubclass(attr, Tool) and 
                    attr != Tool
                ):
                    try:
                        tool_instance = attr()
                        self._tools[tool_instance.name] = tool_instance
                    except Exception:
                        # Skip tools that can't be instantiated
                        continue
        except Exception:
            # If there's an error loading the plugin, skip it
            pass
    
    def get_tool(self, name: str) -> Tool:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self._tools.keys())
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with given parameters."""
        tool = self.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found"}
        
        return tool.execute(**kwargs)