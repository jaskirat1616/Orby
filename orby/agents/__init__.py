"""Agent implementations for Orby."""
import asyncio
from typing import Dict, List, Any, Optional
from ..core import Agent, AgentMessage, ToolCall, ToolCallStatus
from ..backends import BackendManager, OllamaBackend, LMStudioBackend


class ReasoningAgent(Agent):
    """Agent with enhanced reasoning capabilities."""
    
    def __init__(self, model_name: str = "default", tools=None):
        super().__init__(model_name, tools)
        self.backend_manager = self._initialize_backend_manager()

    def _initialize_backend_manager(self):
        """Initialize backend manager with default backends."""
        backend_manager = BackendManager()
        
        # Add default backends - in a real implementation, these would come from config
        backend_manager.register_backend('ollama', OllamaBackend())
        backend_manager.register_backend('lmstudio', LMStudioBackend())
        
        return backend_manager

    async def process_message(self, user_input: str) -> str:
        """Process a user message with enhanced reasoning."""
        # Add user message to history
        user_msg = AgentMessage(role="user", content=user_input)
        self.conversation_history.append(user_msg)
        
        # Get agent response with potential tool calls
        response_data = await self._get_enhanced_response(user_input)
        
        # Handle tool calls if present
        if response_data.get("tool_calls"):
            tool_results = await self.process_tool_calls(response_data["tool_calls"])
            
            # Add tool results to history
            for tool_call, result in zip(response_data["tool_calls"], tool_results):
                tool_msg = AgentMessage(
                    role="tool",
                    content=str(result),
                    tool_calls=[tool_call]
                )
                self.conversation_history.append(tool_msg)
            
            # Get final response after tool execution
            final_response = await self._get_final_response(user_input, tool_results)
        else:
            final_response = response_data.get("content", "No response generated.")
        
        # Add final response to history
        agent_msg = AgentMessage(role="assistant", content=final_response)
        self.conversation_history.append(agent_msg)
        
        return final_response

    async def _get_enhanced_response(self, user_input: str) -> Dict[str, Any]:
        """Get enhanced response from the language model."""
        # This is a simplified implementation
        # In a real implementation, we'd call the LLM and parse for tool calls
        
        # For demonstration, let's check if the input matches known patterns
        if "list files" in user_input.lower() or "show files" in user_input.lower():
            # Suggest a file tool call
            tool_call = ToolCall(
                name="file",
                arguments={"operation": "list", "path": "."}
            )
            return {
                "content": "",
                "tool_calls": [tool_call]
            }
        elif "execute shell" in user_input.lower() or "run command" in user_input.lower():
            # Suggest a shell tool call
            # Extract command from input (very basic)
            command = "ls -la"  # default command
            if "command" in user_input:
                # This is a simplified extraction
                pass
            
            tool_call = ToolCall(
                name="shell",
                arguments={"command": command}
            )
            return {
                "content": "",
                "tool_calls": [tool_call]
            }
        
        return {
            "content": f"Orby received: {user_input}. I can help with tools, code, files, web, and more.",
            "tool_calls": []
        }

    async def _get_final_response(self, original_input: str, tool_results: List[Dict[str, Any]]) -> str:
        """Get final response after tool execution."""
        # In a real implementation, we'd call the LLM again with tool results
        results_summary = []
        for result in tool_results:
            if result.get("status") == "success":
                results_summary.append(f"Success: {result.get('output', 'No output')}")
            else:
                results_summary.append(f"Error: {result.get('error', 'Unknown error')}")
        
        return f"I've processed your request. Tool results: {'; '.join(results_summary)}"


class AutoAgent(ReasoningAgent):
    """Agent that automatically chains reasoning steps."""
    
    async def process_message(self, user_input: str) -> str:
        """Process message with automatic reasoning chain."""
        # For now, this is the same as the reasoning agent
        # In a more sophisticated implementation, this would
        # automatically determine multiple steps and execute them
        return await super().process_message(user_input)