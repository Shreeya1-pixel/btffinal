"""
Base tool interface and registry.
"""

from typing import Any, Callable, Protocol
from dataclasses import dataclass, field

from backend.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolDefinition:
    """Tool definition for agent use."""
    name: str
    description: str
    parameters: list[ToolParameter]
    function: Callable
    module: str = "generic"
    
    def to_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function schema."""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.required:
                required.append(param.name)
                
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}
        
    def register(self, tool: ToolDefinition) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool definition to register
        """
        self.tools[tool.name] = tool
        logger.info("tool_registered", name=tool.name, module=tool.module)
        
    def get_tool(self, name: str) -> ToolDefinition:
        """
        Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool definition
        """
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")
        return self.tools[name]
        
    def get_tools_by_module(self, module: str) -> list[ToolDefinition]:
        """
        Get all tools for a specific module.
        
        Args:
            module: Module name
            
        Returns:
            List of tool definitions
        """
        return [tool for tool in self.tools.values() if tool.module == module]
        
    def get_all_schemas(self) -> list[dict[str, Any]]:
        """
        Get OpenAI function schemas for all tools.
        
        Returns:
            List of function schemas
        """
        return [tool.to_schema() for tool in self.tools.values()]


tool_registry = ToolRegistry()

