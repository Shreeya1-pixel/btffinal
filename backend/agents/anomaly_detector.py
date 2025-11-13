"""
Specialized agent for GIS anomaly detection. It sequences the GIS tools
to ensure we always fetch data, detect anomalies, and generate visuals.
"""

from typing import Any, Optional
import time
import json

from backend.agents.base import BaseAgent, AgentRole, AgentResponse
from backend.tools.base import tool_registry
from backend.core.logger import get_logger
from backend.core.redis_client import redis_client

logger = get_logger(__name__)


class AnomalyDetectorAgent(BaseAgent):
    """Agent that deterministically runs the GIS anomaly pipeline."""

    def __init__(self) -> None:
        super().__init__(
            name="AnomalyDetector",
            role=AgentRole.TOOL_EXECUTOR,
            instructions=(
                "Run the GIS anomaly pipeline: 1) fetch_geo_data 2) detect_anomalies 3) generate_map_visual.\n"
                "Return concise insights and ensure results are machine-readable."
            ),
        )

    async def execute(self, query: str, context: Optional[dict[str, Any]] = None) -> AgentResponse:
        trace = self.create_trace()
        start = time.time()
        channel = context.get("channel", "neuroverse") if context else "neuroverse"

        # Default parameters (lightweight extraction; orchestration can refine)
        params = {
            "location": "Dubai",
            "metric": "traffic",
            "time_range": "last_week",
        }
        # Very light heuristics from query
        ql = (query or "").lower()
        if "temperature" in ql:
            params["metric"] = "temperature"
        if "dubai" in ql:
            params["location"] = "Dubai"
        if "last week" in ql or "previous week" in ql:
            params["time_range"] = "last_week"

        results: list[dict[str, Any]] = []
        try:
            # Step 1: Fetch geo data
            await redis_client.publish_agent_event(
                channel,
                {"type": "pipeline_step", "agent": self.name, "step": "fetch_geo_data", "status": "started", "message": f"Fetching {params['metric']} data for {params['location']}..."},
            )
            fetch_tool = tool_registry.get_tool("fetch_geo_data")
            geo_str = await fetch_tool.function(**params)
            geo_data = json.loads(geo_str)
            results.append({"tool": "fetch_geo_data", "args": params, "result": geo_str})
            trace.tools_called.append("fetch_geo_data")
            await redis_client.publish_agent_event(
                channel,
                {"type": "pipeline_step", "agent": self.name, "step": "fetch_geo_data", "status": "completed", "message": f"Fetched {len(geo_data.get('features', []))} data points"},
            )

            # Step 2: Detect anomalies
            await redis_client.publish_agent_event(
                channel,
                {"type": "pipeline_step", "agent": self.name, "step": "detect_anomalies", "status": "started", "message": "Running anomaly detection algorithm..."},
            )
            detect_tool = tool_registry.get_tool("detect_anomalies")
            anomalies_str = await detect_tool.function(geo_data=geo_str)
            anomalies_data = json.loads(anomalies_str)
            results.append({"tool": "detect_anomalies", "args": {"geo_data": "<geo_json>"}, "result": anomalies_str})
            trace.tools_called.append("detect_anomalies")
            anom_count = len(anomalies_data.get("anomalies", []))
            await redis_client.publish_agent_event(
                channel,
                {"type": "pipeline_step", "agent": self.name, "step": "detect_anomalies", "status": "completed", "message": f"Identified {anom_count} anomalies"},
            )

            # Step 3: Generate visualization
            await redis_client.publish_agent_event(
                channel,
                {"type": "pipeline_step", "agent": self.name, "step": "generate_map_visual", "status": "started", "message": "Generating map visualization..."},
            )
            vis_tool = tool_registry.get_tool("generate_map_visual")
            visual_str = await vis_tool.function(geo_data=geo_str, anomalies=anomalies_str)
            visual_data = json.loads(visual_str)
            results.append({"tool": "generate_map_visual", "args": {"geo_data": "<geo_json>", "anomalies": "<anomalies>"}, "result": visual_str})
            trace.tools_called.append("generate_map_visual")
            await redis_client.publish_agent_event(
                channel,
                {"type": "pipeline_step", "agent": self.name, "step": "generate_map_visual", "status": "completed", "message": "Visualization ready"},
            )

            # Build content with analysis
            content = f"Analysis complete for {params['location']} ({params['time_range']}).\n\n"
            content += f"📊 Data points analyzed: {len(geo_data.get('features', []))}\n"
            content += f"⚠️ Anomalies detected: {anom_count}\n"
            if anom_count > 0:
                content += f"\nKey findings: {anom_count} abnormal {params['metric']} zones identified. "
                content += f"These represent areas with significant deviation from normal patterns."

            trace.duration_ms = (time.time() - start) * 1000
            trace.metadata = {"params": params}
            
            # Return structured metadata for frontend rendering
            return AgentResponse(
                content=content,
                traces=[trace],
                metadata={
                    "tool_results": results,
                    "module": "gis-anomaly",
                    "geo_data": geo_data,
                    "anomalies": anomalies_data.get("anomalies", []),
                    "visualization": visual_data,
                },
            )
        except Exception as e:
            logger.error("anomaly_detector_failed", error=str(e))
            await redis_client.publish_agent_event(
                channel,
                {"type": "pipeline_step", "agent": self.name, "step": "error", "status": "failed", "message": f"Error: {str(e)}"},
            )
            raise


