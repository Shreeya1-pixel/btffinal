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
- Life-Manager: Handle personal assistant tasks - email (Gmail), messaging (WhatsApp, Instagram), scheduling events, creating reminders and tasks, managing daily apps

Analyze the user's query and determine which module should handle it. Provide clear reasoning."""
        )
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
    def _detect_module_fallback(self, query: str) -> str:
        """
        Fallback module detection using keyword matching when LLM is unavailable.
        
        Args:
            query: User query
            
        Returns:
            Module name (gis-anomaly, life-manager, or generic)
        """
        query_lower = query.lower()
        
        # Life Manager keywords
        life_manager_keywords = [
            "email", "gmail", "send email", "draft email", "mail to", "mailto",
            "schedule", "reminder", "task", "todo", "to-do", "to do",
            "whatsapp", "wa", "send whatsapp", "whatsapp message",
            "instagram", "insta", "dm", "direct message", "send instagram",
            "message", "send message", "text", "send text",
            "create event", "meeting", "appointment", "calendar", "schedule meeting",
            "life manager", "personal assistant", "manage", "organize",
            "contact", "add contact"
        ]
        
        # GIS/Anomaly keywords
        gis_keywords = [
            "anomaly", "anomalies", "abnormal", "traffic", "heat-zone", "heat zone",
            "dubai", "location", "geographic", "geospatial", "gis", "map", "latitude",
            "longitude", "coordinates", "location-based", "spatial", "geographic data",
            "traffic data", "detect anomalies", "find anomalies", "identify anomalies"
        ]
        
        # Check life manager keywords first
        for keyword in life_manager_keywords:
            if keyword in query_lower:
                logger.info("orchestrator_fallback_life_manager", keyword=keyword, query=query)
                return "life-manager"
        
        # Check GIS keywords
        for keyword in gis_keywords:
            if keyword in query_lower:
                logger.info("orchestrator_fallback_gis", keyword=keyword, query=query)
                return "gis-anomaly"
        
        return "generic"
    
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
        
        # Try keyword-based routing first to avoid unnecessary API calls
        fallback_module = self._detect_module_fallback(query)
        
        # If we detected a specific module (not generic), use it directly
        if fallback_module != "generic":
            trace.duration_ms = (time.time() - start_time) * 1000
            trace.metadata = {
                "module_selected": fallback_module,
                "query": query,
                "keyword_routing": True,
                "reason": "Direct keyword match - no LLM call needed"
            }
            
            logger.info(
                "orchestrator_keyword_routing",
                module=fallback_module,
                duration_ms=trace.duration_ms
            )
            
            return AgentResponse(
                content=f"Routing to '{fallback_module}' module based on keyword detection.",
                traces=[trace],
                metadata=trace.metadata
            )
        
        # For generic/ambiguous queries, use LLM for intelligent routing
        try:
            messages = [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": f"""Analyze this query and determine which module should handle it:

Query: {query}

Respond with:
1. Module name (Generic or GIS-Anomaly or Life-Manager)
2. Brief reasoning
3. Key entities or parameters extracted from the query"""}
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3
            )
            
            content = response.choices[0].message.content or ""
            
            trace.duration_ms = (time.time() - start_time) * 1000
            trace.metadata = {
                "module_selected": self._extract_module(content),
                "query": query,
                "llm_routing": True
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
            error_str = str(e)
            logger.warning("orchestrator_llm_failed_using_fallback", error=error_str, query=query)
            
            # Use fallback detection when LLM fails
            module = fallback_module  # We already calculated this above
            trace.duration_ms = (time.time() - start_time) * 1000
            trace.metadata = {
                "module_selected": module,
                "query": query,
                "fallback_used": True,
                "fallback_reason": f"LLM failed ({error_str[:50]}), using keyword detection"
            }
            
            logger.info(
                "orchestrator_fallback_executed",
                module=module,
                duration_ms=trace.duration_ms
            )
            
            return AgentResponse(
                content=f"Routing to '{module}' module (LLM unavailable, using keyword matching).",
                traces=[trace],
                metadata=trace.metadata
            )
            
    def _extract_module(self, content: str) -> str:
        """Extract module name from response."""
        content_lower = content.lower()
        if "gis" in content_lower or "geo" in content_lower or "anomaly" in content_lower:
            return "gis-anomaly"
        return "generic"

