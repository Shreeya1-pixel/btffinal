# CheckMate-MTC: System Architecture

## Technical Architecture Diagram

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#1e3a8a','primaryTextColor':'#fff','primaryBorderColor':'#3b82f6','lineColor':'#6366f1','secondaryColor':'#10b981','tertiaryColor':'#f59e0b','background':'#f8fafc','mainBkg':'#ffffff','secondBkg':'#f1f5f9'}}}%%

graph TB
    %% Client Layer
    Client[React Frontend<br/>TypeScript + Zustand]
    
    %% API Gateway
    API[FastAPI Gateway<br/>SSE Support]
    
    %% Redis Layer
    Redis[(Redis<br/>Event Bus + Session Store)]
    
    %% Core Orchestration
    AgentService[Agent Service<br/>Main Coordinator]
    SessionMgr[Session Manager<br/>Context + History]
    
    %% Single Agent Path
    Orchestrator[Orchestrator Agent<br/>Query Router]
    GenericExec[Generic ToolExecutor<br/>LLM + Function Calling]
    
    %% Multi-Agent Team Path
    TeamOrch[Team Orchestrator<br/>Multi-Agent Coordinator]
    AnomalyAgent[Anomaly Detector<br/>Deterministic Pipeline]
    SummarizerExec[Generic ToolExecutor<br/>Summarization]
    JargonTool[Jargon Translator<br/>Exec + Ops Briefings]
    
    %% Tool Layer
    ToolRegistry[Tool Registry<br/>Dynamic Schema Generation]
    GenericTools[Generic Tools<br/>Summary, Translation, etc]
    GISTools[GIS Tools<br/>Geo Fetch, Anomaly Detection]
    
    %% LLM Provider
    OpenAI[OpenAI API<br/>GPT-4]
    
    %% Flow Connections - Request Path
    Client -->|1. POST /chat| API
    API -->|2. Route Query| AgentService
    AgentService -->|3. Get/Create Session| SessionMgr
    SessionMgr <-->|Session Data<br/>TTL: 3600s| Redis
    
    %% Orchestration Decision
    AgentService -->|4. Analyze Query| Orchestrator
    Orchestrator -->|LLM Call| OpenAI
    Orchestrator -->|5a. Route: Generic| GenericExec
    Orchestrator -->|5b. Route: GIS-Anomaly| TeamOrch
    
    %% Single Agent Path Flow
    GenericExec -->|6a. Select Tools| ToolRegistry
    ToolRegistry -.->|Tool Schemas| GenericTools
    GenericExec -->|7a. Execute Tools| GenericTools
    GenericExec -->|LLM + Function Calling| OpenAI
    GenericExec -->|8a. Return Results| AgentService
    
    %% Multi-Agent Team Flow
    TeamOrch -->|6b. Step 1| AnomalyAgent
    AnomalyAgent -->|Fetch + Detect + Visualize| GISTools
    AnomalyAgent -->|Return Findings| TeamOrch
    
    TeamOrch -->|7b. Step 2: Summarize| SummarizerExec
    SummarizerExec -->|Call Summary Tool| GenericTools
    SummarizerExec -->|LLM Processing| OpenAI
    SummarizerExec -->|Return Summary| TeamOrch
    
    TeamOrch -->|8b. Step 3: Translate| JargonTool
    GenericTools -.->|Jargon Tool| JargonTool
    JargonTool -->|Exec + Ops Output| TeamOrch
    TeamOrch -->|9b. Merge Results| AgentService
    
    %% Response Path
    AgentService -->|10. Save to Session| SessionMgr
    AgentService -->|11. Return Response| API
    API -->|12. JSON Response| Client
    
    %% Real-time Event Stream
    GenericExec -.->|Publish Events| Redis
    TeamOrch -.->|Publish Events| Redis
    AnomalyAgent -.->|Pipeline Steps| Redis
    Redis -.->|SSE: /events/{session_id}| API
    API -.->|Live Trace Updates| Client
    
    %% Styling
    classDef frontend fill:#3b82f6,stroke:#1e3a8a,stroke-width:3px,color:#fff
    classDef api fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    classDef orchestration fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef agent fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
    classDef tools fill:#ec4899,stroke:#db2777,stroke-width:2px,color:#fff
    classDef data fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff
    classDef external fill:#64748b,stroke:#475569,stroke-width:2px,color:#fff
    
    class Client frontend
    class API api
    class AgentService,SessionMgr orchestration
    class Orchestrator,TeamOrch,AnomalyAgent,GenericExec,SummarizerExec agent
    class ToolRegistry,GenericTools,GISTools,JargonTool tools
    class Redis data
    class OpenAI external
```

## Architecture Deep Dive

### Redis Usage Pattern

**Purpose:** Event Bus + Session Persistence (NOT Agent Handoff Coordination)

#### 1. Session Management
```
Pattern: Traditional Key-Value Store
Key Format: session:{session_id}
TTL: 3600 seconds
Data: {session_id, messages[], context{}, active_module, timestamps}
```

#### 2. Real-Time Event Publishing
```
Pattern: Pub/Sub Broadcasting
Channel Format: session:{session_id}
Events:
  - agent_started
  - agent_completed
  - tool_result
  - pipeline_step
  - team_started/completed
  - query_completed
```

#### 3. Agent Handoff Mechanism
**Direct Python Async Calls** (NOT Redis-mediated):
```python
# Multi-Agent Team Flow
team_orchestrator.execute()
  ↓ (direct call)
  anomaly_agent.execute()
  ↓ (direct call)
  summarizer_executor.execute()
  ↓ (direct call)
  jargon_tool.function()
```

### Execution Modes

#### Mode 1: Single Agent (Generic Module)
```
User Query → Orchestrator → Generic ToolExecutor → Tools → Response
```
- Orchestrator routes query via LLM analysis
- ToolExecutor uses OpenAI function calling
- Tools execute, results synthesized by LLM
- Events published to Redis for UI trace

#### Mode 2: Multi-Agent Team (GIS-Anomaly Module)
```
User Query → Orchestrator → Team Orchestrator
  ├─ Step 1: Anomaly Detector (deterministic pipeline)
  │   ├─ fetch_geo_data
  │   ├─ detect_anomalies (IsolationForest)
  │   └─ generate_map_visual
  ├─ Step 2: Summarizer (LLM synthesis)
  └─ Step 3: Jargon Translator (Exec + Ops briefs)
```
- Deterministic orchestration (not LLM-driven routing)
- Each agent publishes progress events
- Results merged into single response

### Key Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **OrchestratorAgent** | Query analysis & module routing | OpenAI GPT-4 |
| **ToolExecutorAgent** | LLM-driven tool selection & execution | OpenAI Function Calling |
| **TeamOrchestrator** | Multi-agent workflow coordination | Python async |
| **AnomalyDetectorAgent** | Deterministic GIS pipeline | IsolationForest, GeoPandas |
| **SessionManager** | Conversation state & context | Redis + In-memory cache |
| **RedisClient** | Event publishing & session storage | Redis async client |
| **ToolRegistry** | Dynamic tool discovery & schema generation | Custom framework |

### Data Flow Characteristics

1. **Synchronous Execution:** Agent-to-agent handoffs are direct method calls
2. **Asynchronous Events:** Redis pub/sub for UI observability
3. **Session Persistence:** Redis stores conversation history with TTL
4. **Stateless Agents:** No shared state between agents (context passed explicitly)
5. **Trace Aggregation:** Each agent creates traces, merged at orchestration layer

### Scalability Considerations

- **Redis as bottleneck:** Currently single Redis instance for both session storage and event bus
- **Agent execution:** Synchronous chain limits parallelization
- **Session cache:** In-memory + Redis dual-layer for performance
- **Tool isolation:** Each tool is independent, enabling future parallel execution

### Event Stream Protocol

**SSE Endpoint:** `GET /events/{session_id}`

**Event Types:**
```json
{
  "type": "agent_started|agent_completed|tool_result|pipeline_step|query_completed",
  "agent": "string",
  "module": "string",
  "step": "string (for pipeline_step)",
  "status": "started|completed|failed (for pipeline_step)",
  "message": "string (human-readable)",
  "timestamp": "float"
}
```

**Frontend Integration:**
- Real-time trace panel updates
- Pipeline step visualization
- Tool execution progress
- Agent handoff tracking


