"""Enhanced shell tool for Orby with sandboxing and permissions."""
import subprocess
import sys
import os
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import logging
from ..core import Tool, ToolPermission


class ShellTool(Tool):
    """Enhanced tool to execute shell commands with sandboxing and permissions."""
    
    def __init__(self):
        super().__init__(
            name="shell",
            description="Execute shell commands in a secure environment with logging",
            permissions_required=["execute", "shell"]
        )

    async def execute(self, command: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """Execute a shell command with security and logging."""
        start_time = time.time()
        
        # Log the command execution
        self._log_execution("shell", {"command": command}, start_time)
        
        try:
            # Validate command for safety
            validation_result = self._validate_command(command)
            if validation_result["blocked"]:
                self._log_execution("shell", {"command": command, "blocked": True}, start_time, "blocked")
                return {
                    "status": "error",
                    "error": validation_result["message"],
                    "output": "",
                    "security_blocked": True,
                    "execution_time": time.time() - start_time
                }
            
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                # Restrict environment variables for security
                env={k: v for k, v in os.environ.items() if k.startswith(('PATH', 'HOME', 'USER'))}
            )
            
            execution_time = time.time() - start_time
            
            # Log successful execution
            self._log_execution("shell", {
                "command": command, 
                "return_code": result.returncode,
                "execution_time": execution_time
            }, start_time, "completed")
            
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "output": result.stdout + result.stderr,
                "execution_time": execution_time
            }
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self._log_execution("shell", {"command": command, "timeout": True}, start_time, "timeout")
            
            return {
                "status": "error",
                "error": f"Command timed out after {timeout} seconds",
                "output": "",
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            self._log_execution("shell", {"command": command, "error": str(e)}, start_time, "error")
            
            return {
                "status": "error",
                "error": str(e),
                "output": str(e),
                "execution_time": execution_time
            }

    def _validate_command(self, command: str) -> Dict[str, Any]:
        """Validate command for safety."""
        dangerous_patterns = [
            'rm -rf', 'rm -r', 'rm -f', 'rmdir', '/dev/',
            'mkfs', 'dd if=', '>/dev/',
            'chmod 777', 'chmod -R 777',
            'chown -R root', 'passwd', 'shadow',
            'sudo', 'su root', 'visudo',
            'iptables', 'ufw', 'firewall',
            'mount', 'umount', 'fdisk',
            'reboot', 'shutdown', 'halt',
            'kill -9', 'pkill -f'
        ]
        
        cmd_lower = command.lower()
        
        for pattern in dangerous_patterns:
            if pattern in cmd_lower:
                return {
                    "blocked": True,
                    "message": f"Command contains potentially dangerous operation: {pattern}"
                }
        
        # Check for path traversal attempts
        if '..' in command and ('/' in command or ';' in command):
            return {
                "blocked": True,
                "message": "Command contains potential path traversal attempt"
            }
        
        return {"blocked": False, "message": ""}
    
    def requires_confirmation(self) -> bool:
        """Check if shell execution requires user confirmation (it's dangerous)."""
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