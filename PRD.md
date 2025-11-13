PRD: Neuroverse

Purpose
Neuroverse AI is a high-productivity, agent-driven platform with a clean terminal/UX aesthetic (inspired by Warp) that allows natural-language queries, multisession interaction, and tool orchestration — with a specialised add-on for GIS analytics and anomaly detection.
It delivers a generic “Jargon AI agent platform” experience, and on top of that the GIS-anomaly module brings domain value.

Scope

Front-end: React application styled like modern developer tooling (monospaced font JetBrains Mono, dark/light theme toggles, minimalist UI).

Back-end: Python (FastAPI) with the OpenAI Agents SDK driving agent workflows, tool-calling, session/memory, guardrails.

Mode switching: ENV flag MODEL_MODE = local or openai.

Generic agent platform core + plugin/submodule for GIS & anomaly detection.

Data store: in-memory DB + Redis bus for agent handoffs and state.

Containerised deployment: Docker (backend + Redis) + React front.

Functional Requirements

Mode selection

ENV MODEL_MODE selects local model vs OpenAI.

Both modes should work seamlessly; fallback capability for reliability.

Generic agent interface

Chat input: user can ask across domains (not just GIS) — e.g., “Summarise this CSV”, “Generate plan for marketing campaign”.

Agent interprets jargon, picks tools generically.

Platform shows plugin modules; the GIS-anomaly module is one plugin.

GIS-Anomaly Tool Module

Module registered in platform with tool suite: fetch_geo_data, detect_anomalies, generate_map_visual.

User enters domain-specific query: “Find abnormal traffic heat-zones in Dubai last week.”

Agent chain: QueryInterpreter → GIS-Module Agent → ExplainAgent.

Output: Map view with anomalies + list + textual rationale.

UI/UX Theming & Style

Font: JetBrains Mono across UI (inputs, outputs, code/agent trace panels).

Theme inspired by Warp: developer tooling look (modern, dark default, subtle accent colours, monospaced code-style chat).

Interface: Split screen — left chat & trace panel, right map/results or generic output panel.

Module selector: shows active plugin e.g., “GIS Module (Anomaly Detection)”.

Session & Plugin Memory

The system keeps context across follow-up queries (e.g., “Zoom into anomaly #2”, “Compare with last 14 days”).

Memory stored in Redis/in-memory; module state persists during session.

Trace & Observability

A developer view toggles “Agent Trace” showing for each user query:

Agent invoked

Tools called

Handoffs recorded

Time/stats

Helps demonstration and judging for technical depth.

Deployment & Infrastructure

Dockerfile for backend and model hosting.

Docker-Compose with backend container + Redis container.

React app served in dev mode or production build.

Configurable via .env file (MODEL_MODE, REDIS_URL, etc).

Non-Functional Requirements

Performance: Response latency ≤ 2–3s for local model in demo mode.

Reliability: Guardrails ensure valid queries (e.g., for GIS module region/metric checks).

Modular architecture: New modules (plugins) can be added easily beyond GIS.

Aesthetic: UI resides in developer tool aesthetic (monospaced, minimal distractions, code-feel).

Accessibility: While UI is developer-style, ensure readability and color contrast.

Open-source: Core platform uses open-source model locally; fallback via OpenAI optional.

Architecture Overview

Front-end (React): Chat UI + module selector + results panel + map component (for GIS).

Back-end (FastAPI):

Generic Agent Platform: receives user input → invokes Agent chain via OpenAI Agents SDK.

Plugin Modules: GIS module integrated with specialized tools & dataset.

Datastore: In-memory DB (for datasets) + Redis bus for handoffs/state.

Model Endpoint: Local (open-source) or OpenAI API depending on MODEL_MODE.

Deployment: Docker containers (backend+model) + Redis; frontend runs client.

Milestones (Approx 10 hours)

Hour 0–1: Setup repo, Dockerfiles, basic React scaffold, environment flag support.

Hour 1–2: Generic chat UI and backend endpoint /chat. Connect to local stub model or OpenAI.

Hour 2–3: Build generic agent invocation via Agents SDK (tool stubs).

Hour 3–4: Integrate GIS dataset and map UI (React + Leaflet).

Hour 4–6: Implement GIS-anomaly tools and plugin module; agent chain for GIS query.

Hour 6–7: Style UI: JetBrains Mono font, dark theme, tool selector.

Hour 7–8: Add session memory + follow-up support.

Hour 8–9: Add trace panel showing agent steps/handoffs.

Hour 9–10: Test mode switching, finalize demo scenario, prepare brief presentation & architecture slide.

Success Criteria for Judging

The generic “Emergent” platform works (chat → agent → tool → result).

GIS-Anomaly module demonstrates domain value: user queries GIS anomaly, get map + explanation.

Aesthetic and UX: Modern developer-tool feel, monospaced JetBrains Mono font, unique theme.

Technical depth: Use of OpenAI Agents SDK, multi-agent handoff, tool-calling, Redis bus, in-memory DB, Dockerised infrastructure.

Flexibility: MODE flag enabling local vs OpenAI model demonstrates maturity.

Presentation readiness: Demo flows smoothly, architecture clearly communicated, trace panel visible for judges.