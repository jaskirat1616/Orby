"""Enhanced file operations for Orby."""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import time
from ..core import Tool


class FileTool(Tool):
    """Enhanced tool for safe file operations with logging."""
    
    def __init__(self):
        super().__init__(
            name="file",
            description="Read, write, and manipulate files with safety checks",
            permissions_required=["read", "write", "file"]
        )

    async def execute(self, operation: str, path: str, content: Optional[str] = None, 
                     **kwargs) -> Dict[str, Any]:
        """Execute file operations with safety checks and logging."""
        start_time = time.time()
        
        # Log the operation
        self._log_execution("file", {"operation": operation, "path": path}, start_time)
        
        try:
            # Secure path resolution
            path_obj = self._secure_path_resolution(path)
            if not path_obj:
                self._log_execution("file", {"operation": operation, "path": path, "error": "invalid_path"}, start_time, "error")
                return {
                    "status": "error",
                    "error": f"Invalid path: {path}",
                    "output": ""
                }
            
            # Check if path is inside safe directory
            if not self._is_path_safe(path_obj):
                self._log_execution("file", {"operation": operation, "path": path, "error": "unsafe_path"}, start_time, "error")
                return {
                    "status": "error",
                    "error": f"Path outside safe directory: {path}",
                    "output": ""
                }
            
            if operation == "read":
                result = await self._read_file(path_obj)
            elif operation == "write":
                result = await self._write_file(path_obj, content)
            elif operation == "list":
                result = await self._list_directory(path_obj)
            elif operation == "delete":
                result = await self._delete_file(path_obj)
            elif operation == "info":
                result = await self._get_file_info(path_obj)
            elif operation == "exists":
                result = await self._check_exists(path_obj)
            else:
                result = {
                    "status": "error",
                    "error": f"Unsupported operation: {operation}",
                    "output": ""
                }
            
            # Log successful operation
            execution_time = time.time() - start_time
            log_details = {"operation": operation, "path": str(path_obj), "status": result["status"]}
            if result["status"] == "success":
                self._log_execution("file", log_details, start_time, "completed")
            else:
                self._log_execution("file", {**log_details, "error": result.get("error", "")}, start_time, "error")
            
            result["execution_time"] = execution_time
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._log_execution("file", {"operation": operation, "path": path, "error": str(e)}, start_time, "error")
            
            return {
                "status": "error",
                "error": str(e),
                "output": str(e),
                "execution_time": execution_time
            }
    
    def _secure_path_resolution(self, path: str) -> Optional[Path]:
        """Resolve path securely, preventing directory traversal."""
        try:
            # Prevent common traversal attempts
            if '..' in path.replace('\\', '/').replace('//', '/').split('/'):
                # If there are traversal attempts, resolve relative to current or home directory
                path = Path.cwd() / path.lstrip('./')
            
            path_obj = Path(path).resolve()
            return path_obj
        except Exception:
            return None
    
    def _is_path_safe(self, path_obj: Path) -> bool:
        """Check if path is in a safe location."""
        home_path = Path.home()
        
        # Check if path is within home directory or current working directory
        try:
            path_obj.relative_to(home_path)
            return True
        except ValueError:
            pass
        
        try:
            path_obj.relative_to(Path.cwd())
            return True
        except ValueError:
            pass
        
        # Only allow specific safe system paths
        safe_system_paths = ["/tmp", "/var/tmp"]
        for safe_path in safe_system_paths:
            try:
                path_obj.relative_to(Path(safe_path))
                return True
            except ValueError:
                pass
        
        return False
    
    async def _read_file(self, path_obj: Path) -> Dict[str, Any]:
        """Read a file."""
        if not path_obj.exists():
            return {
                "status": "error",
                "error": f"File does not exist: {path_obj}",
                "output": ""
            }
        
        if not path_obj.is_file():
            return {
                "status": "error",
                "error": f"Path is not a file: {path_obj}",
                "output": ""
            }
        
        try:
            # Check file size to prevent reading huge files
            if path_obj.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                return {
                    "status": "error",
                    "error": f"File too large to read (>{10*1024*1024} bytes): {path_obj}",
                    "output": ""
                }
            
            with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return {
                "status": "success",
                "content": content,
                "size": len(content),
                "output": f"Read {len(content)} characters from {path_obj}"
            }
        except PermissionError:
            return {
                "status": "error",
                "error": f"Permission denied reading file: {path_obj}",
                "output": ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Could not read file {path_obj}: {str(e)}",
                "output": str(e)
            }
    
    async def _write_file(self, path_obj: Path, content: Optional[str]) -> Dict[str, Any]:
        """Write to a file."""
        if content is None:
            return {
                "status": "error",
                "error": "Content required for write operation",
                "output": ""
            }
        
        try:
            # Create parent directories if they don't exist
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path_obj, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "status": "success",
                "output": f"Wrote {len(content)} characters to {path_obj}"
            }
        except PermissionError:
            return {
                "status": "error",
                "error": f"Permission denied writing to file: {path_obj}",
                "output": ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Could not write to file {path_obj}: {str(e)}",
                "output": str(e)
            }
    
    async def _list_directory(self, path_obj: Path) -> Dict[str, Any]:
        """List directory contents."""
        if not path_obj.exists():
            return {
                "status": "error",
                "error": f"Path does not exist: {path_obj}",
                "output": ""
            }
        
        if not path_obj.is_dir():
            return {
                "status": "error",
                "error": f"Path is not a directory: {path_obj}",
                "output": ""
            }
        
        try:
            files = []
            for item in path_obj.iterdir():
                # Skip hidden files by default for security/safety
                if item.name.startswith('.'):
                    continue
                    
                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": item.stat().st_mtime
                }
                files.append(item_info)
            
            return {
                "status": "success",
                "files": files,
                "count": len(files),
                "output": f"Directory {path_obj} contains {len(files)} visible items"
            }
        except PermissionError:
            return {
                "status": "error",
                "error": f"Permission denied listing directory: {path_obj}",
                "output": ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Could not list directory {path_obj}: {str(e)}",
                "output": str(e)
            }
    
    async def _delete_file(self, path_obj: Path) -> Dict[str, Any]:
        """Delete a file."""
        if not path_obj.exists():
            return {
                "status": "error",
                "error": f"File does not exist: {path_obj}",
                "output": ""
            }
        
        if path_obj.is_dir():
            return {
                "status": "error",
                "error": f"Path is a directory, not a file: {path_obj}",
                "output": ""
            }
        
        try:
            path_obj.unlink()
            return {
                "status": "success",
                "output": f"Deleted file: {path_obj}"
            }
        except PermissionError:
            return {
                "status": "error",
                "error": f"Permission denied deleting file: {path_obj}",
                "output": ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Could not delete file {path_obj}: {str(e)}",
                "output": str(e)
            }
    
    async def _get_file_info(self, path_obj: Path) -> Dict[str, Any]:
        """Get file information."""
        if not path_obj.exists():
            return {
                "status": "error",
                "error": f"Path does not exist: {path_obj}",
                "output": ""
            }
        
        try:
            stat = path_obj.stat()
            info = {
                "path": str(path_obj),
                "exists": True,
                "is_file": path_obj.is_file(),
                "is_dir": path_obj.is_dir(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            return {
                "status": "success",
                "info": info,
                "output": f"Info for {path_obj}"
            }
        except PermissionError:
            return {
                "status": "error",
                "error": f"Permission denied accessing file: {path_obj}",
                "output": ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Could not get info for {path_obj}: {str(e)}",
                "output": str(e)
            }
    
    async def _check_exists(self, path_obj: Path) -> Dict[str, Any]:
        """Check if path exists."""
        exists = path_obj.exists()
        return {
            "status": "success",
            "exists": exists,
            "output": f"Path {path_obj} {'exists' if exists else 'does not exist'}",
            "is_file": path_obj.is_file() if exists else False,
            "is_dir": path_obj.is_dir() if exists else False
        }
    
    def requires_confirmation(self) -> bool:
        """Check if file operations require confirmation."""
        # Operations that modify or delete files should require confirmation
        # This is handled by checking the specific operation during execution
        return True
    
    def _log_execution(self, tool_name: str, details: Dict[str, Any], start_time: float, status: str = "started"):
        """Log tool execution to file for transparency."""
        log_dir = Path.home() / ".orby" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"tool_execution_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        try:
            with open(log_file, 'a') as f:
                timestamp = datetime.now().isoformat()
                log_entry = f"[{timestamp}] {status.upper()} - {tool_name}: {details}\n"
                f.write(log_entry)
        except Exception:
            # If logging fails, continue execution
            pass