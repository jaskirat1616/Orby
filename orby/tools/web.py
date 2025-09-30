"""Enhanced web operations for Orby."""
import aiohttp
from typing import Dict, Any
from datetime import datetime
import time
import urllib.parse
from pathlib import Path
from ..core import Tool


class WebTool(Tool):
    """Enhanced tool for safe web operations with logging."""
    
    def __init__(self):
        super().__init__(
            name="web",
            description="Fetch web content and perform web operations safely",
            permissions_required=["network", "web"]
        )

    async def execute(self, operation: str, url: str, **kwargs) -> Dict[str, Any]:
        """Execute web operations with safety and logging."""
        start_time = time.time()
        
        # Log the operation
        self._log_execution("web", {"operation": operation, "url": url}, start_time)
        
        try:
            # Validate URL
            validation_result = self._validate_url(url)
            if not validation_result["valid"]:
                self._log_execution("web", {"operation": operation, "url": url, "error": validation_result["error"]}, start_time, "error")
                return {
                    "status": "error",
                    "error": validation_result["error"],
                    "output": ""
                }
            
            if operation == "fetch":
                result = await self._fetch_url(url, **kwargs)
            elif operation == "head":
                result = await self._head_request(url, **kwargs)
            else:
                result = {
                    "status": "error",
                    "error": f"Unsupported operation: {operation}",
                    "output": ""
                }
            
            # Log the result
            execution_time = time.time() - start_time
            log_details = {"operation": operation, "url": url, "status": result["status"]}
            if result["status"] == "success":
                self._log_execution("web", log_details, start_time, "completed")
            else:
                self._log_execution("web", {**log_details, "error": result.get("error", "")}, start_time, "error")
            
            result["execution_time"] = execution_time
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._log_execution("web", {"operation": operation, "url": url, "error": str(e)}, start_time, "error")
            
            return {
                "status": "error",
                "error": str(e),
                "output": str(e),
                "execution_time": execution_time
            }
    
    async def _fetch_url(self, url: str, timeout: int = 30, max_size: int = 10*1024*1024, **kwargs) -> Dict[str, Any]:
        """Fetch content from a URL with safety limits."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}: {response.reason}",
                            "status_code": response.status,
                            "output": ""
                        }
                    
                    # Read content with size limit
                    content = ""
                    size = 0
                    async for chunk in response.content.iter_chunked(8192):
                        content += chunk.decode('utf-8', errors='ignore')
                        size += len(chunk)
                        
                        if size > max_size:
                            return {
                                "status": "error",
                                "error": f"Content too large (>{max_size} bytes)",
                                "output": f"Stopped at {size} bytes due to size limit"
                            }
                    
                    return {
                        "status": "success",
                        "content": content,
                        "status_code": response.status,
                        "content_length": len(content),
                        "output": f"Fetched {len(content)} characters from {url}"
                    }
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error": f"Request timed out after {timeout} seconds",
                "output": ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to fetch URL: {str(e)}",
                "output": str(e)
            }
    
    async def _head_request(self, url: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """Make a HEAD request to get URL metadata."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.head(url) as response:
                    headers = dict(response.headers)
                    
                    return {
                        "status": "success",
                        "status_code": response.status,
                        "headers": headers,
                        "content_type": headers.get('Content-Type', ''),
                        "content_length": headers.get('Content-Length', ''),
                        "output": f"HEAD request to {url} returned {response.status}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"HEAD request failed: {str(e)}",
                "output": str(e)
            }
    
    def _validate_url(self, url: str) -> Dict[str, Any]:
        """Validate URL for safety."""
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check if it's a valid URL
            if not parsed.scheme or parsed.scheme not in ['http', 'https']:
                return {
                    "valid": False,
                    "error": "URL must use HTTP or HTTPS scheme"
                }
            
            # Check for potentially dangerous URLs
            dangerous_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
            if parsed.hostname and parsed.hostname in dangerous_hosts:
                return {
                    "valid": False,
                    "error": f"Access to {parsed.hostname} is restricted"
                }
            
            # Check for internal IP ranges (basic check)
            if parsed.hostname and parsed.hostname.startswith(('10.', '172.', '192.168.')):
                return {
                    "valid": False,
                    "error": f"Access to internal IP {parsed.hostname} is restricted"
                }
            
            return {"valid": True, "error": ""}
            
        except Exception:
            return {
                "valid": False,
                "error": "Invalid URL format"
            }
    
    def requires_confirmation(self) -> bool:
        """Web access requires confirmation as it involves network operations."""
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


# Import asyncio for timeout handling
import asyncio