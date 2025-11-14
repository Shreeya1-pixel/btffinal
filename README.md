# Neuroverse AI Agent Platform

**Multi-Agent AI Platform with Life Manager & Geospatial Intelligence**

A production-grade agentic AI platform featuring intelligent query routing, real-time trace visualization, personal life management (Gmail, WhatsApp, Instagram), and geospatial anomaly detection. Built with custom multi-agent orchestration, hybrid execution modes, and zero-LLM routing for instant responses.

---

## Overview

Neuroverse is an advanced AI system that coordinates specialized agents to handle diverse tasks from personal communication management to complex geospatial analysis. The platform features intelligent keyword-based routing for zero-cost execution of simple commands and LLM-powered orchestration for complex queries.

**Key Capabilities:**
- **Life Manager**: Personal assistant for Gmail, WhatsApp, Instagram with contact resolution
- **Zero-LLM Routing**: Instant execution (< 2ms) for simple commands without API calls
- **Intelligent Query Routing**: Automatic module selection (Generic, GIS-Anomaly, Life-Manager)
- **Multi-Agent Team Collaboration**: Coordinated workflows for complex GIS analysis
- **Real-Time Pipeline Execution**: Live trace visualization via Server-Sent Events
- **Contact Intelligence**: Natural name-to-identifier resolution across all channels

---

## Architecture

### System Design

**Three Execution Modes:**

1. **Zero-LLM Mode** (Simple Life Manager commands)
   - Keyword-based routing (< 1ms)
   - Direct tool execution without API calls
   - Contact name resolution
   - Example: "send hi to mom on whatsapp" → ~2ms, $0.00

2. **Single Agent Mode** (Generic queries)
   - LLM-driven tool selection via OpenAI function calling
   - Dynamic tool orchestration based on query analysis
   - General purpose data analysis and summarization

3. **Multi-Agent Team Mode** (GIS-Anomaly queries)
   - Deterministic pipeline: Data Fetch → Anomaly Detection → Visualization
   - Automated summarization with audience-specific jargon translation
   - Coordinated execution with progress broadcasting

**Core Components:**
- **Orchestrator Agent:** Routes queries via keyword detection (zero-LLM) or GPT-4 analysis
- **Tool Executor Agent:** Executes tools with intelligent pattern matching or LLM function calling
- **Life Manager Module:** Gmail, WhatsApp, Instagram communication with contact resolution
- **Contact Manager:** Maps contact names to email, phone, Instagram handles
- **Team Orchestrator:** Coordinates multi-agent workflows for complex tasks
- **Anomaly Detector Agent:** Runs deterministic GIS pipeline (IsolationForest + SHAP)
- **Session Manager:** Maintains conversation context with Redis persistence
- **Tool Registry:** Dynamic tool discovery and schema generation

**Data Flow:**
```
User Query → API Gateway → Agent Service
    ↓
Orchestrator (Keyword Detection OR GPT-4 routing)
    ↓
[Life-Manager Module] → Contact Resolution → Direct Tool Execution (< 2ms)
         OR
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
- **LLM Integration:** OpenAI GPT-4o with function calling
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
- **UI Components:** App sidebar with communication app icons

### Infrastructure
- **Containerization:** Docker Compose (backend, frontend, Redis, nginx)
- **Reverse Proxy:** nginx (routing + static file serving)
- **Database:** Redis (session + event bus)

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API key (optional for simple Life Manager commands)

### Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/Shreeya1-pixel/btffinal.git
   cd checkmate-agentic-psg
   ```

2. **Set up environment**
   ```bash
   # Create .env file
   cat > .env << EOF
   OPENAI_API_KEY=your_api_key_here
   REDIS_HOST=redis
   REDIS_PORT=6379
   SESSION_TIMEOUT=3600
   LLM_INFERENCE_MODE=cloud
   EOF
   ```

3. **Run with Docker Compose** (Recommended)
   ```bash
   docker-compose up --build
   ```
   Access at: **http://localhost:80**

4. **Run locally** (Development)
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

### Life Manager - Personal Assistant

**Zero-LLM Commands** (No API key needed):
```
✓ "send hi to mom on whatsapp"
✓ "email boss about the meeting"
✓ "dm dad on instagram saying hello"
✓ "send hello to mom on gmail"
```

**Draft Mode** (Uses AI for content generation):
```
✓ "draft an email to mom about the party"
✓ "draft a whatsapp message to boss"
```

**Contact Management:**
```
✓ "add contact john with email john@example.com and phone +1234567899"
```

**Default Contacts:**
- **Mom**: mom@example.com, +1234567890, @mom_instagram
- **Dad**: dad@example.com, +1234567891, @dad_instagram
- **Boss**: boss@company.com, +1234567892, @boss_instagram

See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for more examples.

### API Endpoints

**Core Operations:**
- `POST /api/chat` - Process user query through agent system
- `POST /api/sessions` - Create new conversation session
- `GET /api/sessions/{id}` - Retrieve session history
- `GET /api/events/{session_id}` - SSE stream for real-time traces
- `GET /api/modules` - List available modules and tools

**Life Manager:**
- `POST /life-manager/email/send` - Send Gmail (generates mailto link)
- `POST /life-manager/whatsapp/send` - Send WhatsApp (generates wa.me link)
- `POST /life-manager/schedule` - Schedule event
- `POST /life-manager/task` - Create task

**Direct Analysis:**
- `POST /api/analyze-stats` - Direct CSV statistics (bypasses LLM)
- `POST /api/anomaly/upload` - Upload dataset for anomaly detection

### Example Queries

**Life Manager Module:**
```
"send hi to mom on whatsapp"
"email boss about the project deadline"
"dm dad on instagram"
"draft an email to mom"
"schedule a meeting with boss tomorrow"
```

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
- **App Sidebar:** Quick access to Gmail, WhatsApp, Instagram, and custom apps
- **Trace Panel:** Real-time agent execution visualization with tool calls
- **Pipeline Steps:** Progress tracking for multi-agent workflows
- **Data Visualization:** Interactive Plotly maps and charts
- **Approval Workflow:** Draft messages with approve/edit/cancel options
- **Redis Monitor:** Live event stream inspection (dev mode)
- **SHAP Explainability:** Feature importance for anomaly predictions

---

## Project Structure

```
checkmate-agentic-psg/
├── backend/
│   ├── agents/                 # Agent implementations
│   │   ├── base.py            # BaseAgent, AgentTrace, AgentResponse
│   │   ├── orchestrator.py    # Query router (keyword + GPT-4)
│   │   ├── tool_executor.py   # Function calling executor with pattern matching
│   │   ├── team_orchestrator.py  # Multi-agent coordinator
│   │   └── anomaly_detector.py   # GIS pipeline agent
│   ├── api/                    # FastAPI routes & models
│   ├── core/                   # Core infrastructure
│   │   ├── llm_provider.py    # OpenAI client wrapper
│   │   ├── redis_client.py    # Redis async client
│   │   └── logger.py          # Structured logging
│   ├── services/               # Business logic
│   │   ├── agent_service.py   # Main orchestration service
│   │   ├── session_manager.py # Session + context management
│   │   └── contact_manager.py # Contact resolution system
│   ├── tools/                  # Tool implementations
│   │   ├── base.py            # Tool registry system
│   │   ├── generic_tools.py   # Summary, translation, etc.
│   │   ├── gis_tools.py       # Geo fetch, anomaly detection
│   │   ├── life_manager_tools.py  # Gmail, WhatsApp, Instagram
│   │   └── csv_analyzer.py    # Statistical analysis
│   ├── config.py               # Configuration management
│   └── main.py                 # FastAPI app entry point
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── AppSidebar.tsx  # App sidebar with icons
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
├── requirements.txt            # Python dependencies
├── LIFE_MANAGER_README.md      # Life Manager documentation
├── QUICK_START_GUIDE.md        # Quick start guide
└── IMPLEMENTATION_SUMMARY.md   # Technical implementation details
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API authentication | **Required for LLM features** |
| `REDIS_HOST` | Redis host | `redis` (Docker) / `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `SESSION_TIMEOUT` | Session TTL in seconds | `3600` |
| `LLM_INFERENCE_MODE` | LLM provider mode | `cloud` |

**Note:** Simple Life Manager commands work without `OPENAI_API_KEY` using zero-LLM routing.

### Module Configuration

Tools are automatically registered via the Tool Registry system. Add new tools by:

1. Define function with type hints
2. Register with `tool_registry.register(ToolDefinition(...))`
3. Tool automatically available for agent execution

---

## Performance

**Latency Characteristics:**
- **Zero-LLM Life Manager**: ~2ms (keyword routing + contact resolution)
- **Query routing (Orchestrator)**: ~500-800ms (with LLM) or < 1ms (keyword)
- **Tool execution (Generic)**: ~1-3s per tool
- **GIS pipeline (Multi-agent)**: ~5-8s end-to-end
- **Session retrieval**: <10ms (with cache)

**Cost Optimization:**
- Zero-LLM routing saves API costs for simple commands
- Contact resolution: O(1) dictionary lookup
- Pattern matching: No API calls for direct sends

**Scalability:**
- Stateless API servers (horizontal scaling ready)
- Redis single instance (bottleneck for high concurrency)
- LLM rate limits: Configured per OpenAI tier
- Suggested improvements: Redis cluster, parallel tool execution

---

## Development

### Adding a New Communication Channel

See [LIFE_MANAGER_README.md](LIFE_MANAGER_README.md) for detailed instructions. Quick example:

```python
# 1. Add to Contact Manager
class Contact:
    def __init__(self, ..., slack: Optional[str] = None):
        self.slack = slack

# 2. Create tool
async def send_slack(to: str, message: str) -> str:
    resolved = contact_manager.get_slack(to) or to
    # Implementation
    return json.dumps(result)

# 3. Register tool
tool_registry.register(ToolDefinition(
    name="send_slack",
    description="Send Slack message",
    parameters=[...],
    function=send_slack,
    module="life-manager"
))

# 4. Update routing keywords
# orchestrator.py: Add "slack" to life_manager_keywords
# tool_executor.py: Add slack detection logic
```

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

## Documentation

- **[LIFE_MANAGER_README.md](LIFE_MANAGER_README.md)** - Complete Life Manager documentation
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Quick start guide with examples
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - System architecture diagrams

---

## Security Considerations

- API key management via environment variables
- Session isolation per user
- Contact data: Currently in-memory (encrypt in production)
- Redis authentication recommended for production
- Rate limiting suggested for public deployments
- Input sanitization for tool parameters
- OAuth2 integration points marked for Gmail/Instagram APIs

---

## Deployment

### Docker Production

```bash
docker-compose up --build -d
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
- Backend: Type hints required, Google-style docstrings
- Frontend: Prettier, ESLint rules enforced
- Tests: Required for new features

---

## License

MIT License

---

## Acknowledgments

- OpenAI for GPT-4o and function calling capabilities
- FastAPI for modern async Python framework
- Redis for high-performance event streaming
- Plotly for interactive visualizations
- React & TypeScript community

---

## Support

- **Documentation**: See [LIFE_MANAGER_README.md](LIFE_MANAGER_README.md), [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)
- **Issues**: GitHub Issues tracker
- **Repository**: https://github.com/Shreeya1-pixel/btffinal

---

**Version:** 0.2.0  
**Last Updated:** November 2025  
**Status:** Production-ready with Life Manager features
