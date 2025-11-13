"""
Orchestrator agent that coordinates multi-agent workflows.
"""

from typing import Any, Optional
import time
from openai import AsyncOpenAI

from backend.agents.base import BaseAgent, AgentRole, AgentResponse, AgentTrace
from backend.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator agent that routes queries to appropriate specialized agents.
    """
    
    def __init__(self):
        super().__init__(
            name="Orchestrator",
            role=AgentRole.ORCHESTRATOR,
            instructions="""You are an orchestrator agent that analyzes user queries and routes them to specialized agents.
            
You have access to the following modules:
- Generic: Handle general queries, data analysis, summaries
- GIS-Anomaly: Handle geospatial queries, location-based analysis, anomaly detection in geographic data

Analyze the user's query and determine which module should handle it. Provide clear reasoning."""
        )
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
    async def execute(
        self, 
        query: str, 
        context: Optional[dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Analyze query and route to appropriate handler.
        
        Args:
            query: User query
            context: Optional context
            
        Returns:
            AgentResponse with routing decision
        """
        trace = self.create_trace()
        start_time = time.time()
        
        try:
            messages = [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": f"""Analyze this query and determine which module should handle it:

Query: {query}

Respond with:
1. Module name (Generic or GIS-Anomaly)
2. Brief reasoning
3. Key entities or parameters extracted from the query"""}
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3
            )
            
            content = response.choices[0].message.content or ""
            
            trace.duration_ms = (time.time() - start_time) * 1000
            trace.metadata = {
                "module_selected": self._extract_module(content),
                "query": query
            }
            
            logger.info(
                "orchestrator_executed",
                module=trace.metadata["module_selected"],
                duration_ms=trace.duration_ms
            )
            
            return AgentResponse(
                content=content,
                traces=[trace],
                metadata=trace.metadata
            )
            
        except Exception as e:
            logger.error("orchestrator_failed", error=str(e))
            raise
            
    def _extract_module(self, content: str) -> str:
        """Extract module name from response."""
        content_lower = content.lower()
        if "gis" in content_lower or "geo" in content_lower or "anomaly" in content_lower:
            return "gis-anomaly"
        return "generic"

