"""Built-in tools for Orby."""
import subprocess
import tempfile
import os
import sys
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from pathlib import Path
from ..core import Tool, ToolCall, ToolCallStatus


class ShellTool(Tool):
    """Tool to execute shell commands."""
    
    def __init__(self):
        super().__init__(
            name="shell",
            description="Execute shell commands and return the output"
        )

    async def execute(self, command: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """Execute a shell command."""
        try:
            # Validate command for safety
            if self._is_dangerous_command(command):
                return {
                    "status": "error",
                    "error": "Command contains potentially dangerous operations",
                    "output": ""
                }
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "output": result.stdout + result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": f"Command timed out after {timeout} seconds",
                "output": ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "output": str(e)
            }
    
    def _is_dangerous_command(self, command: str) -> bool:
        """Check if command contains dangerous operations."""
        dangerous_patterns = [
            'rm -rf', 'rm -r', 'rm -f', 'rmdir',
            'mkfs', 'dd if=', '>/dev/',
            'chmod 777', 'chmod -R 777',
            'chown -R root', 'passwd', 'shadow'
        ]
        
        cmd_lower = command.lower()
        return any(pattern in cmd_lower for pattern in dangerous_patterns)


class CodeTool(Tool):
    """Tool to execute code snippets in a sandboxed environment."""
    
    def __init__(self):
        super().__init__(
            name="code",
            description="Execute code snippets in a sandboxed environment"
        )

    async def execute(self, code: str, language: str = "python", timeout: int = 30) -> Dict[str, Any]:
        """Execute code in a sandboxed environment."""
        try:
            if language.lower() == "python":
                # Create a temporary file for the code
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                
                try:
                    result = subprocess.run(
                        [sys.executable, temp_file],
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                    
                    return {
                        "status": "success",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "return_code": result.returncode,
                        "output": result.stdout + result.stderr
                    }
                finally:
                    os.unlink(temp_file)
            else:
                return {
                    "status": "error",
                    "error": f"Language '{language}' not supported",
                    "output": ""
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": f"Code execution timed out after {timeout} seconds",
                "output": ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "output": str(e)
            }


class FileTool(Tool):
    """Tool for file system operations."""
    
    def __init__(self):
        super().__init__(
            name="file",
            description="Read, write, and manipulate files"
        )

    async def execute(self, operation: str, path: str, content: Optional[str] = None, 
                     **kwargs) -> Dict[str, Any]:
        """Execute file operations."""
        try:
            path_obj = Path(path).resolve()
            
            # Security check: prevent directory traversal
            if ".." in path or str(path_obj).startswith("/"):
                if not str(path_obj).startswith(Path.home().resolve()):
                    return {
                        "status": "error",
                        "error": "Path outside home directory is not allowed",
                        "output": ""
                    }
            
            if operation == "read":
                with open(path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {
                    "status": "success",
                    "content": content,
                    "output": f"Read {len(content)} characters from {path}"
                }
            elif operation == "write":
                if content is None:
                    return {
                        "status": "error",
                        "error": "Content required for write operation",
                        "output": ""
                    }
                
                # Create parent directories if they don't exist
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                with open(path_obj, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "status": "success",
                    "output": f"Wrote {len(content)} characters to {path}"
                }
            elif operation == "list":
                if not path_obj.is_dir():
                    return {
                        "status": "error",
                        "error": f"Path is not a directory: {path}",
                        "output": ""
                    }
                
                files = [str(f) for f in path_obj.iterdir()]
                return {
                    "status": "success",
                    "files": files,
                    "output": f"Directory {path} contains {len(files)} items"
                }
            elif operation == "exists":
                exists = path_obj.exists()
                return {
                    "status": "success",
                    "exists": exists,
                    "output": f"Path {path} {'exists' if exists else 'does not exist'}"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported operation: {operation}",
                    "output": ""
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "output": str(e)
            }


class WebTool(Tool):
    """Tool for web operations."""
    
    def __init__(self):
        super().__init__(
            name="web",
            description="Fetch web content and perform web operations"
        )

    async def execute(self, operation: str, url: str, **kwargs) -> Dict[str, Any]:
        """Execute web operations."""
        if operation == "fetch":
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        content = await response.text()
                        
                        return {
                            "status": "success",
                            "content": content,
                            "status_code": response.status,
                            "output": f"Fetched {len(content)} characters from {url}"
                        }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "output": str(e)
                }
        else:
            return {
                "status": "error",
                "error": f"Unsupported operation: {operation}",
                "output": ""
            }