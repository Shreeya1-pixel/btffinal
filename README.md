# CheckMate-MTC

**Multi-Agent Traffic Control System with Real-Time Anomaly Detection**

A production-grade agentic AI platform for geospatial anomaly detection and intelligent data analysis, featuring custom multi-agent orchestration, real-time trace visualization, and hybrid execution modes.

---

## Overview

CheckMate-MTC (Multi-Traffic Control) is an advanced AI system that coordinates specialized agents to analyze traffic data, detect anomalies, and generate actionable insights. Built on a custom orchestration framework with OpenAI integration, Redis-backed session management, and real-time event streaming.

**Key Capabilities:**
- Intelligent query routing between generic and geospatial modules
- Multi-agent team collaboration for complex GIS workflows
- Real-time pipeline execution tracking via SSE
- Deterministic anomaly detection with ML explainability (SHAP)
- Context-aware conversation management with session persistence

---

## Architecture

### System Design

**Two Execution Modes:**

1. **Single Agent Mode** (Generic queries)
   - LLM-driven tool selection via OpenAI function calling
   - Dynamic tool orchestration based on query analysis
   - General purpose data analysis and summarization

2. **Multi-Agent Team Mode** (GIS-Anomaly queries)
   - Deterministic pipeline: Data Fetch → Anomaly Detection → Visualization
   - Automated summarization with audience-specific jargon translation
   - Coordinated execution with progress broadcasting

**Core Components:**
- **Orchestrator Agent:** Routes queries to appropriate modules via GPT-4 analysis
- **Tool Executor Agent:** Executes tools using OpenAI function calling with LLM synthesis
- **Team Orchestrator:** Coordinates multi-agent workflows for complex tasks
- **Anomaly Detector Agent:** Runs deterministic GIS pipeline (IsolationForest + SHAP)
- **Session Manager:** Maintains conversation context with Redis persistence
- **Tool Registry:** Dynamic tool discovery and schema generation

**Data Flow:**
```
User Query → API Gateway → Agent Service
    ↓
Orchestrator (GPT-4 routing)
    ↓
[Generic Module] → ToolExecutor → Tools
         OR
[GIS Module] → Team Orchestrator
    ├─ Anomaly Detector (fetch, detect, visualize)
    ├─ Summarizer (LLM synthesis)
    └─ Jargon Translator (Exec + Ops briefings)
```

**Redis Integration:**
- Session storage with 1-hour TTL
- Pub/Sub event bus for real-time trace updates
- In-memory cache layer for performance

See [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for detailed technical diagrams.

---

## Technology Stack

### Backend
- **Framework:** FastAPI (async API server)
- **LLM Integration:** OpenAI GPT-4 with function calling
- **Orchestration:** Custom multi-agent framework (not LangChain/LangGraph/CrewAI)
- **Session Management:** Redis (async client with pub/sub)
- **ML/Data Science:** 
  - scikit-learn (IsolationForest anomaly detection)
  - SHAP (explainability)
  - pandas, GeoPandas (data processing)
  - Plotly (visualization)
- **Logging:** Structured JSON logging with custom logger

### Frontend
- **Framework:** React 18 + TypeScript
- **State Management:** Zustand
- **Styling:** CSS Modules with custom design system
- **Real-time Updates:** Server-Sent Events (SSE)
- **Visualization:** react-plotly.js for maps and charts

### Infrastructure
- **Containerization:** Docker Compose (backend, frontend, Redis, nginx)
- **Reverse Proxy:** nginx (routing + static file serving)
- **Database:** Redis (session + event bus)

---

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API key

### Installation

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd CheckMate-MTC
   ```

2. **Set up environment**
   ```bash
   # Backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Frontend
   cd frontend
   npm install
   ```

3. **Configure environment**
   ```bash
   # Create .env file
   cat > .env << EOF
   OPENAI_API_KEY=your_api_key_here
   REDIS_URL=redis://localhost:6379
   SESSION_TIMEOUT=3600
   LLM_INFERENCE_MODE=openai
   EOF
   ```

4. **Run with Docker Compose** (Recommended)
   ```bash
   docker-compose up --build
   ```
   Access at: http://localhost

5. **Run locally** (Development)
   ```bash
   # Terminal 1: Redis
   redis-server

   # Terminal 2: Backend
   cd backend
   uvicorn main:app --reload --port 8000

   # Terminal 3: Frontend
   cd frontend
   npm run dev
   ```
   Access at: http://localhost:5173

---

## Usage

### API Endpoints

**Core Operations:**
- `POST /api/chat` - Process user query through agent system
- `POST /api/sessions` - Create new conversation session
- `GET /api/sessions/{id}` - Retrieve session history
- `GET /api/events/{session_id}` - SSE stream for real-time traces
- `GET /api/modules` - List available modules and tools

**Direct Analysis:**
- `POST /api/analyze-stats` - Direct CSV statistics (bypasses LLM)
- `POST /api/anomaly/upload` - Upload dataset for anomaly detection

### Example Queries

**Generic Module:**
```
"Summarize the key trends in the data"
"Translate this technical report for executive audience"
"Generate a summary of findings"
```

**GIS-Anomaly Module:**
```
"Detect anomalies in Dubai traffic data"
"Show me temperature anomalies in the last week"
"Analyze geospatial patterns for traffic incidents"
```

### Frontend Features

- **Chat Interface:** Natural language query input with session persistence
- **Trace Panel:** Real-time agent execution visualization with tool calls
- **Pipeline Steps:** Progress tracking for multi-agent workflows
- **Data Visualization:** Interactive Plotly maps and charts
- **Redis Monitor:** Live event stream inspection (dev mode)
- **SHAP Explainability:** Feature importance for anomaly predictions

---

## Project Structure

```
CheckMate-MTC/
├── backend/
│   ├── agents/                 # Agent implementations
│   │   ├── base.py            # BaseAgent, AgentTrace, AgentResponse
│   │   ├── orchestrator.py    # Query router (GPT-4)
│   │   ├── tool_executor.py   # Function calling executor
│   │   ├── team_orchestrator.py  # Multi-agent coordinator
│   │   └── anomaly_detector.py   # GIS pipeline agent
│   ├── api/                    # FastAPI routes & models
│   ├── core/                   # Core infrastructure
│   │   ├── llm_provider.py    # OpenAI client wrapper
│   │   ├── redis_client.py    # Redis async client
│   │   └── logger.py          # Structured logging
│   ├── services/               # Business logic
│   │   ├── agent_service.py   # Main orchestration service
│   │   └── session_manager.py # Session + context management
│   ├── tools/                  # Tool implementations
│   │   ├── base.py            # Tool registry system
│   │   ├── generic_tools.py   # Summary, translation, etc.
│   │   ├── gis_tools.py       # Geo fetch, anomaly detection
│   │   └── csv_analyzer.py    # Statistical analysis
│   ├── config.py               # Configuration management
│   └── main.py                 # FastAPI app entry point
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── TracePanel.tsx
│   │   │   ├── PipelineSteps.tsx
│   │   │   ├── GeoPlot.tsx
│   │   │   └── ShapPlot.tsx
│   │   ├── store/             # Zustand state management
│   │   ├── services/          # API client
│   │   └── styles/            # CSS modules
│   └── vite.config.ts
├── data/                       # Sample datasets
├── docker-compose.yml          # Container orchestration
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf                  # Reverse proxy config
└── requirements.txt            # Python dependencies
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API authentication | **Required** |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SESSION_TIMEOUT` | Session TTL in seconds | `3600` |
| `LLM_INFERENCE_MODE` | LLM provider mode | `openai` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Module Configuration

Tools are automatically registered via the Tool Registry system. Add new tools by:

1. Define function with type hints
2. Decorate with `@tool_registry.register(module="module_name")`
3. Tool automatically available for agent execution

---

## Development

### Adding a New Agent

```python
from backend.agents.base import BaseAgent, AgentRole, AgentResponse

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CustomAgent",
            role=AgentRole.TOOL_EXECUTOR,
            instructions="Agent instructions here"
        )
    
    async def execute(self, query: str, context: dict) -> AgentResponse:
        trace = self.create_trace()
        # Implementation
        return AgentResponse(content="...", traces=[trace])
```

### Adding a New Tool

```python
from backend.tools.base import tool_registry

@tool_registry.register(module="custom_module")
async def my_tool(param1: str, param2: int) -> str:
    """Tool description for LLM"""
    # Implementation
    return "result"
```

### Running Tests

```bash
# Backend tests
pytest backend/tests/

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/integration/
```

---

## Redis Architecture

**Session Storage:**
- Key pattern: `session:{session_id}`
- TTL: 3600 seconds
- Data structure: JSON with messages, context, active_module

**Event Bus:**
- Channel pattern: `session:{session_id}`
- Pub/Sub for real-time agent events
- Event types: agent_started, agent_completed, tool_result, pipeline_step

**Agent Handoff:**
- Direct Python async calls (NOT Redis-mediated)
- Synchronous execution with asynchronous event publishing
- Context passed explicitly between agents

---

## Performance

**Latency Characteristics:**
- Query routing (Orchestrator): ~500-800ms
- Tool execution (Generic): ~1-3s per tool
- GIS pipeline (Multi-agent): ~5-8s end-to-end
- Session retrieval: <10ms (with cache)

**Scalability:**
- Stateless API servers (horizontal scaling ready)
- Redis single instance (bottleneck for high concurrency)
- LLM rate limits: Configured per OpenAI tier
- Suggested improvements: Redis cluster, parallel tool execution

---

## Monitoring & Observability

**Structured Logging:**
- JSON format with correlation IDs
- Agent execution traces with timing
- Tool call tracking with parameters
- Error context with stack traces

**Real-Time Tracing:**
- SSE event stream per session
- Frontend trace panel visualization
- Pipeline step progress indicators
- Redis monitor for event inspection

**Metrics:**
- Agent execution duration
- Tool call frequency
- Session creation rate
- LLM token usage (logged)

---

## Security Considerations

- API key management via environment variables
- Session isolation per user
- Redis authentication recommended for production
- Rate limiting suggested for public deployments
- Input sanitization for tool parameters

---

## Deployment

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-Specific Configs

- Development: Hot reload, verbose logging
- Production: Optimized builds, error-only logs
- Staging: Mimics production with test data

---

## Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

**Code Style:**
- Backend: Black formatter, type hints required
- Frontend: Prettier, ESLint rules enforced
- Tests: Required for new features

---

## License

[Your License Here]

---

## Acknowledgments

- OpenAI for GPT-4 and function calling capabilities
- FastAPI for modern async Python framework
- Redis for high-performance event streaming
- Plotly for interactive visualizations
- Warp terminal for UI design inspiration

---

## Support

- Documentation: [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md), [PRD.md](PRD.md)
- Issues: GitHub Issues tracker
- Contact: [Your contact info]

---

**Version:** 0.1.0  
**Last Updated:** November 2025  
**Status:** Production-ready prototype
