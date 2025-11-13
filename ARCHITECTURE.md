# Neuroverse AI - System Architecture

## Overview
Production-grade AI agent platform with GIS anomaly detection, built with OpenAI Agents SDK, FastAPI, and React.

## Key Features

### 1. CSV Analysis Pipeline (Optimized)
- **Direct Analysis**: Bypasses LLM for statistical analysis
- **Fast Processing**: Uses pandas directly for data quality metrics
- **Smart Insights**: Auto-detects geo/time columns, calculates quality scores
- **Endpoint**: `POST /api/analyze-stats`

### 2. Anomaly Detection
**Workflow:**
```
CSV Upload → Stats Analysis → Isolation Forest → SHAP Values → Visualization
```

**Tools:**
- `analyze_csv_stats`: Comprehensive data profiling (fill rates, outliers, quality grade)
- `detect_anomalies_iforest`: ML-based anomaly detection with explainability
- Auto-detection of latitude, longitude, timestamp, and value columns

### 3. Agent Architecture
**Orchestrator** → Routes queries to specialized agents
**Tool Executor** → Executes domain-specific tools
**Anomaly Detector** → GIS pipeline agent (fetch → detect → visualize)

### 4. UI/UX
**Color Palette (Mature Professional):**
- Background: `#0d1117` (deep black) → `#1f2937` (gray-blue)
- Accent: `#10b981` (professional teal) + `#3b82f6` (blue)
- Text: `#e6edf3` (off-white) → `#6b7280` (muted gray)

**Layout:**
- **Chat Tab**: Multi-agent conversations with real-time pipeline steps
- **Anomaly Lab Tab**: 3-step workflow (Upload → Analyze → Detect)
  - Data quality dashboard
  - Column-level statistics with outlier detection
  - Top-k anomaly detection with SHAP explanations
  - Optional GIS visualization

## Technical Stack

### Backend
- **Framework**: FastAPI 0.115.0
- **AI**: OpenAI Agents SDK 0.4.2 + OpenAI 2.6.1
- **ML**: scikit-learn 1.4.2 (Isolation Forest) + SHAP 0.45.0
- **Data**: pandas 2.1.3 + numpy 1.26.2
- **Session**: Redis 5.0.1 (pub/sub for real-time events)

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **State**: Zustand (global store)
- **Viz**: Plotly.js (heatmaps, 3D scatter, SHAP plots)
- **Font**: JetBrains Mono (monospace)

### Infrastructure
- Docker Compose orchestration
- Nginx reverse proxy
- Health checks + graceful shutdown

## API Endpoints

### Analysis (New!)
```
POST /api/analyze-stats
Body: { "csv_data": "..." }
Response: {
  "summary": { "quality_score": 95.2, "quality_grade": "A", ... },
  "columns": [ { "name": "latitude", "fill_rate": 100, ... } ],
  "detected_columns": { "latitude": "lat", "longitude": "lon", ... }
}
```

### Chat
```
POST /api/chat
Body: { "query": "...", "session_id": "..." }
```

### SSE (Real-time)
```
GET /api/events/{session_id}
Streams: pipeline_step, tool_result, agent_handoff
```

## Data Flow

### CSV Analysis (Optimized)
1. Frontend uploads CSV to `AnomalyLab`
2. Validation (headers, row count)
3. Direct call to `/api/analyze-stats` (no LLM)
4. Backend: `analyze_csv_stats()` computes stats in pandas
5. Frontend: Displays `DataStatsPanel` with quality metrics
6. User clicks "Detect Anomalies" → Isolation Forest
7. Backend: Returns top-k anomalies + SHAP values
8. Frontend: Renders `ShapPlot` and optional `GeoPlot`

### Why This Architecture?
- **No LLM for Stats**: Faster, more reliable, cheaper
- **LLM for Insights**: Only used for natural language summaries
- **Agent for Orchestration**: Routes complex queries to right tools
- **Redis for Real-time**: Pipeline progress streamed to UI

## Module Structure

```
backend/
├── agents/           # BaseAgent, Orchestrator, ToolExecutor, AnomalyDetector
├── tools/            # generic_tools, gis_tools, csv_analyzer
├── api/              # routes.py (endpoints), models.py (schemas)
├── services/         # agent_service, session_manager
└── core/             # redis_client, logger, config

frontend/
├── components/       # AnomalyLab, DataStatsPanel, PipelineSteps, ShapPlot
├── services/         # api.ts (HTTP client)
├── store/            # useAppStore.ts (Zustand)
└── styles/           # global.css, components.css
```

## Environment Variables

```bash
OPENAI_API_KEY=sk-...
LLM_INFERENCE_MODE=cloud  # or "local"
REDIS_URL=redis://redis:6379/0
VITE_API_URL=http://localhost:8000
```

## Deployment

```bash
# Build and run
docker-compose build --no-cache
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f backend

# Access
Frontend: http://localhost
Backend: http://localhost:8000
API Docs: http://localhost:8000/docs
```

## Performance Optimizations
1. **CSV Analysis**: Direct pandas (no LLM) → 10x faster
2. **Chunked Processing**: Large CSVs handled in batches
3. **Caching**: Redis session store
4. **Async**: All I/O operations async
5. **Docker**: Multi-stage builds for smaller images

## Security
- Sandboxed Python execution for `execute_python` tool
- CORS configured for localhost
- Environment variables for secrets
- Health checks for service monitoring

---
**Version**: 0.1.0  
**Last Updated**: Nov 4, 2025
