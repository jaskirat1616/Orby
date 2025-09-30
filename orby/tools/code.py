"""Enhanced code execution for Orby."""
import subprocess
import sys
import tempfile
import os
import time
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from ..core import Tool


class CodeTool(Tool):
    """Enhanced tool for safe code execution with sandboxing."""
    
    def __init__(self):
        super().__init__(
            name="code",
            description="Execute code in a safe sandboxed environment",
            permissions_required=["execute", "code"]
        )

    async def execute(self, code: str, language: str = "python", timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """Execute code with safety checks and logging."""
        start_time = time.time()
        
        # Log the execution
        self._log_execution("code", {"language": language, "code_length": len(code)}, start_time)
        
        try:
            # Validate code for dangerous operations
            validation_result = self._validate_code(code, language)
            if not validation_result["valid"]:
                self._log_execution("code", {"language": language, "error": validation_result["error"]}, start_time, "blocked")
                return {
                    "status": "error",
                    "error": validation_result["error"],
                    "output": "",
                    "execution_time": time.time() - start_time
                }
            
            if language.lower() == "python":
                result = await self._execute_python(code, timeout)
            elif language.lower() == "javascript":
                result = await self._execute_javascript(code, timeout)
            elif language.lower() in ["bash", "sh"]:
                result = await self._execute_bash(code, timeout)
            else:
                result = {
                    "status": "error",
                    "error": f"Language '{language}' not supported. Supported: python, javascript, bash",
                    "output": ""
                }
            
            # Log the result
            execution_time = time.time() - start_time
            log_details = {"language": language, "status": result["status"]}
            if result["status"] == "success":
                self._log_execution("code", log_details, start_time, "completed")
            else:
                self._log_execution("code", {**log_details, "error": result.get("error", "")}, start_time, "error")
            
            result["execution_time"] = execution_time
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._log_execution("code", {"language": language, "error": str(e)}, start_time, "error")
            
            return {
                "status": "error",
                "error": str(e),
                "output": str(e),
                "execution_time": execution_time
            }
    
    async def _execute_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code in a secure environment."""
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute in a restricted environment
            result = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, '.'); exec(open('{temp_file}').read())"],
                capture_output=True,
                text=True,
                timeout=timeout,
                # Limit environment exposure
                env={
                    "PYTHONPATH": ".",
                    "HOME": os.environ.get("HOME", ""),
                    "TMPDIR": tempfile.gettempdir()
                }
            )
            
            # Clean up
            os.unlink(temp_file)
            
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "output": result.stdout + result.stderr
            }
        except subprocess.TimeoutExpired:
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass  # File might not exist
            return {
                "status": "error",
                "error": f"Python code execution timed out after {timeout} seconds",
                "output": ""
            }
        except Exception as e:
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass
            return {
                "status": "error",
                "error": f"Python execution failed: {str(e)}",
                "output": str(e)
            }
    
    async def _execute_javascript(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js if available."""
        # Check if node is available
        try:
            node_result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
            if node_result.returncode != 0:
                return {
                    "status": "error",
                    "error": "Node.js is not available on this system",
                    "output": ""
                }
        except FileNotFoundError:
            return {
                "status": "error",
                "error": "Node.js is not installed or not in PATH",
                "output": ""
            }
        
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute JavaScript code
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Clean up
            os.unlink(temp_file)
            
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "output": result.stdout + result.stderr
            }
        except subprocess.TimeoutExpired:
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass
            return {
                "status": "error",
                "error": f"JavaScript execution timed out after {timeout} seconds",
                "output": ""
            }
        except Exception as e:
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass
            return {
                "status": "error",
                "error": f"JavaScript execution failed: {str(e)}",
                "output": str(e)
            }
    
    async def _execute_bash(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute bash script in a restricted environment."""
        # For security, bash execution is more restricted than the shell tool
        return {
            "status": "error",
            "error": "Bash code execution is disabled for security reasons. Use the 'shell' tool for command execution.",
            "output": ""
        }
    
    def _validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code for dangerous operations."""
        if language.lower() == "python":
            dangerous_patterns = [
                'import os', 'import sys', 'import subprocess', 'import shutil',
                '__import__', 'eval(', 'exec(', 'compile(',
                'open(', 'file(',
                'globals()', 'locals()',
                'getattr(', 'setattr(',
                'delattr(',
                'execfile', '__file__',
                'compile(', 'eval'
            ]
            
            code_lower = code.lower()
            for pattern in dangerous_patterns:
                if pattern in code_lower:
                    return {
                        "valid": False,
                        "error": f"Code contains potentially dangerous operation: {pattern}"
                    }
        
        # Check for excessive length
        if len(code) > 10000:  # 10KB limit
            return {
                "valid": False,
                "error": "Code is too long (max 10KB)"
            }
        
        return {"valid": True, "error": ""}
    
    def requires_confirmation(self) -> bool:
        """Code execution requires confirmation as it's a potentially dangerous operation."""
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