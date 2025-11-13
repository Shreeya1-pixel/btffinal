"""
Team orchestrator that coordinates multiple specialized agents and tools.
Publishes detailed events to Redis for live UI trace.
"""

from typing import Any, Optional
import time
import json
import asyncio

from backend.agents.base import BaseAgent, AgentRole, AgentResponse, AgentTrace
from backend.agents.tool_executor import ToolExecutorAgent
from backend.agents.anomaly_detector import AnomalyDetectorAgent
from backend.core.logger import get_logger
from backend.core.redis_client import redis_client
from backend.tools.base import tool_registry

logger = get_logger(__name__)


class TeamOrchestrator(BaseAgent):
    """Runs a small team: anomaly detector, summarizer, and jargon translator."""

    def __init__(self) -> None:
        super().__init__(
            name="TeamOrchestrator",
            role=AgentRole.ORCHESTRATOR,
            instructions=(
                "Coordinate multi-agent execution for GIS anomaly workflows."
            ),
        )

    async def execute(self, query: str, context: Optional[dict[str, Any]] = None) -> AgentResponse:
        trace = self.create_trace()
        start = time.time()
        channel = (context or {}).get("channel", "neuroverse")

        try:
            await redis_client.publish_agent_event(channel, {"type": "team_started", "agent": self.name})

            # 1) Run anomaly pipeline (deterministic agent)
            anomaly_agent = AnomalyDetectorAgent()
            anom_resp = await anomaly_agent.execute(query=query, context={"channel": channel})

            # 2) Summarize results using generic executor (tool: generate_summary)
            generic = ToolExecutorAgent("generic")
            summary_prompt = (
                "Summarize the anomaly findings in 4-6 sentences. Include counts and next steps.\n\n"
                f"Findings JSON: {json.dumps(anom_resp.metadata.get('tool_results', []))[:4000]}"
            )
            gen_resp = await generic.execute(query=summary_prompt, context={"channel": channel})

            # 3) Jargon AI: translate for exec and ops
            jargon_tool = tool_registry.get_tool("jargon_translate")
            exec_text = await jargon_tool.function(text=gen_resp.content, audience="exec")
            ops_text = await jargon_tool.function(text=gen_resp.content, audience="ops")

            # Combine
            combined_content = (
                f"{gen_resp.content}\n\n---\nExec Briefing:\n{exec_text}\n\nOps Playbook:\n{ops_text}"
            )

            # Merge traces
            all_traces: list[AgentTrace] = [trace] + anom_resp.traces + gen_resp.traces
            trace.duration_ms = (time.time() - start) * 1000
            trace.metadata = {"team": ["anomaly_detector", "generic_summarizer", "jargon_ai"]}

            await redis_client.publish_agent_event(channel, {"type": "team_completed", "agent": self.name})

            # Aggregate tool results
            tool_results = []
            tool_results.extend(anom_resp.metadata.get("tool_results", []))
            tool_results.extend(gen_resp.metadata.get("tool_results", []))
            tool_results.append({"tool": "jargon_translate", "args": {"audience": "exec"}, "result": exec_text})
            tool_results.append({"tool": "jargon_translate", "args": {"audience": "ops"}, "result": ops_text})

            return AgentResponse(
                content=combined_content,
                traces=all_traces,
                metadata={
                    "module": "gis-anomaly",
                    "tool_results": tool_results,
                },
            )
        except Exception as e:
            logger.error("team_orchestrator_failed", error=str(e))
            raise


