"""
Generic tools for data analysis and processing.
"""

from typing import Any
import pandas as pd
import json
import subprocess
import tempfile
import textwrap
import time
import re
import requests
from bs4 import BeautifulSoup

from backend.tools.base import ToolDefinition, ToolParameter, tool_registry
from backend.core.logger import get_logger
from backend.core.llm_provider import get_llm_provider

logger = get_logger(__name__)


async def analyze_data(data: str, analysis_type: str = "summary") -> str:
    """
    Analyze structured data.
    
    Args:
        data: JSON or CSV formatted data
        analysis_type: Type of analysis (summary, statistics, trends)
        
    Returns:
        Analysis results as string
    """
    try:
        # Parse data
        try:
            data_dict = json.loads(data)
            df = pd.DataFrame(data_dict)
        except:
            from io import StringIO
            df = pd.read_csv(StringIO(data))
            
        if analysis_type == "summary":
            result = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "sample": df.head(3).to_dict(orient="records")
            }
        elif analysis_type == "statistics":
            result = df.describe().to_dict()
        else:
            result = {"error": f"Unknown analysis type: {analysis_type}"}
            
        logger.info("data_analyzed", analysis_type=analysis_type, rows=len(df))
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error("data_analysis_failed", error=str(e))
        return json.dumps({"error": str(e)})


async def generate_summary(text: str, max_length: int = 200) -> str:
    """
    Generate a summary of text content.
    
    Args:
        text: Text to summarize
        max_length: Maximum length of summary
        
    Returns:
        Summary text
    """
    # Simple extractive summary (first sentences up to max_length)
    sentences = text.split(". ")
    summary = ""
    
    for sentence in sentences:
        if len(summary) + len(sentence) <= max_length:
            summary += sentence + ". "
        else:
            break
            
    logger.info("summary_generated", original_length=len(text), summary_length=len(summary))
    return summary.strip()


async def calculate_metrics(data: str, metric_type: str) -> str:
    """
    Calculate specific metrics from data.
    
    Args:
        data: JSON formatted data
        metric_type: Type of metric (average, total, count, max, min)
        
    Returns:
        Calculated metric as string
    """
    try:
        data_dict = json.loads(data)
        df = pd.DataFrame(data_dict)
        
        numeric_cols = df.select_dtypes(include=["number"]).columns
        results = {}
        
        for col in numeric_cols:
            if metric_type == "average":
                results[col] = float(df[col].mean())
            elif metric_type == "total":
                results[col] = float(df[col].sum())
            elif metric_type == "count":
                results[col] = int(df[col].count())
            elif metric_type == "max":
                results[col] = float(df[col].max())
            elif metric_type == "min":
                results[col] = float(df[col].min())
                
        logger.info("metrics_calculated", metric_type=metric_type, columns=len(results))
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error("metric_calculation_failed", error=str(e))
        return json.dumps({"error": str(e)})


async def execute_python(code: str, timeout_seconds: int = 5) -> str:
    """
    Execute a small Python snippet in a constrained subprocess.
    Returns stdout/stderr, exit code and duration as JSON string.

    Guardrails:
    - Blocks dangerous imports and builtins via regex screening
    - Timeouts after `timeout_seconds`
    - Output is truncated to 16KB
    """
    start = time.time()
    banned_patterns = [
        r"\bimport\s+os\b",
        r"\bimport\s+sys\b",
        r"\bimport\s+subprocess\b",
        r"\bimport\s+socket\b",
        r"\bfrom\s+os\b",
        r"\bfrom\s+sys\b",
        r"\bopen\(",
        r"__import__\(",
        r"eval\(",
        r"exec\(",
    ]
    for pat in banned_patterns:
        if re.search(pat, code):
            logger.warning("python_exec_blocked", pattern=pat)
            return json.dumps({
                "error": "Blocked unsafe code (restricted import or builtin)",
                "pattern": pat
            })

    # Normalize indentation/newlines
    normalized_code = textwrap.dedent(code).strip()
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as fp:
            fp.write(normalized_code)
            fp.flush()
            file_path = fp.name

        completed = subprocess.run(
            ["python", file_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""

        # Truncate overly large output
        def truncate(s: str) -> str:
            return s if len(s) <= 16384 else s[:16384] + "\n...[truncated]"

        result = {
            "stdout": truncate(stdout),
            "stderr": truncate(stderr),
            "exit_code": completed.returncode,
            "duration_ms": (time.time() - start) * 1000,
            "code": normalized_code,
        }
        logger.info("python_exec_completed", exit_code=completed.returncode)
        return json.dumps(result, indent=2)
    except subprocess.TimeoutExpired:
        logger.error("python_exec_timeout")
        return json.dumps({
            "error": "Execution timed out",
            "duration_ms": (time.time() - start) * 1000,
        })
    except Exception as e:
        logger.error("python_exec_failed", error=str(e))
        return json.dumps({"error": str(e)})


async def jargon_translate(text: str, audience: str = "exec") -> str:
    """
    Rewrite text for a target audience using the configured LLM provider.
    Audiences: exec, analyst, ops, public.
    """
    provider = get_llm_provider()
    system = (
        "You are Jargon AI. Rewrite the user's content for the target audience with the right\n"
        "level of detail, tone, and terminology. Avoid hype; be precise and concise.\n"
        "- exec: 3 bullet points, impact, risk, decision ask.\n"
        "- analyst: methods, metrics, caveats.\n"
        "- ops: clear steps, thresholds, alerts.\n"
        "- public: non-technical, plain language.\n"
    )
    content = await provider.create_completion([
        {"role": "system", "content": system},
        {"role": "user", "content": f"Audience: {audience}\n\nText:\n{text}"},
    ], temperature=0.2)
    logger.info("jargon_translated", audience=audience)
    return content


async def web_search(query: str, max_results: int = 5) -> str:
    """
    Lightweight web search (DuckDuckGo HTML) that returns a list of {title,url,snippet}.
    """
    try:
        url = "https://duckduckgo.com/html/"
        resp = requests.get(url, params={"q": query}, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for a in soup.select("a.result__a")[: max_results]:
            title = a.get_text(strip=True)
            href = a.get("href")
            snippet_el = a.find_parent("div", class_="result__body").select_one("a.result__snippet") if a.find_parent("div", class_="result__body") else None
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append({"title": title, "url": href, "snippet": snippet})
        logger.info("web_search_completed", query=query, results=len(results))
        return json.dumps({"query": query, "results": results}, indent=2)
    except Exception as e:
        logger.error("web_search_failed", error=str(e))
        return json.dumps({"error": str(e)})


async def list_open_datasets() -> str:
    """Return a curated catalog of open datasets with curl examples and categories."""
    catalog = {
        "tabular": [
            {
                "name": "UCI Iris",
                "description": "Classic iris flower dataset (CSV)",
                "url": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
                "curl": "curl -L -o data/iris.csv https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
            },
            {
                "name": "Wine Quality (Red)",
                "description": "UCI wine quality (red) CSV",
                "url": "https://raw.githubusercontent.com/ageron/data/main/winequality-red.csv",
                "curl": "curl -L -o data/winequality-red.csv https://raw.githubusercontent.com/ageron/data/main/winequality-red.csv",
            },
            {
                "name": "USGS Earthquakes (30 days)",
                "description": "Recent earthquakes worldwide (CSV)",
                "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv",
                "curl": "curl -L -o data/usgs_quakes_month.csv https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv",
            },
        ],
        "geo": [
            {
                "name": "Natural Earth - Populated Places (10m)",
                "description": "Small global cities dataset (ZIP with shapefile)",
                "url": "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_populated_places_simple.zip",
                "curl": "curl -L -o data/ne_10m_populated_places_simple.zip https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_populated_places_simple.zip",
            },
            {
                "name": "NYC 311 Service Requests (sample)",
                "description": "Open 311 requests (CSV sample via Socrata)",
                "url": "https://data.cityofnewyork.us/resource/erm2-nwe9.csv?$limit=50000",
                "curl": "curl -L -o data/nyc_311_sample.csv \"https://data.cityofnewyork.us/resource/erm2-nwe9.csv?$limit=50000\"",
            },
        ],
        "time_series": [
            {
                "name": "OpenAQ City Measurements (sample)",
                "description": "Air quality measurements (JSON sample)",
                "url": "https://api.openaq.org/v2/measurements?limit=1000",
                "curl": "curl -L -o data/openaq_sample.json \"https://api.openaq.org/v2/measurements?limit=1000\"",
            }
        ],
        "how_to_use": "Create a data/ directory, then run the curl commands. Use csv_to_geojson for CSV with lat/lon to plot, then detect_anomalies_iforest with top_k.",
    }
    return json.dumps(catalog, indent=2)


# Register generic tools
tool_registry.register(ToolDefinition(
    name="analyze_data",
    description="Analyze structured data (JSON or CSV format) and provide summaries or statistics",
    parameters=[
        ToolParameter(
            name="data",
            type="string",
            description="The data to analyze in JSON or CSV format"
        ),
        ToolParameter(
            name="analysis_type",
            type="string",
            description="Type of analysis: summary, statistics, or trends",
            required=False,
            default="summary"
        )
    ],
    function=analyze_data,
    module="generic"
))

tool_registry.register(ToolDefinition(
    name="generate_summary",
    description="Generate a concise summary of text content",
    parameters=[
        ToolParameter(
            name="text",
            type="string",
            description="The text to summarize"
        ),
        ToolParameter(
            name="max_length",
            type="number",
            description="Maximum length of the summary in characters",
            required=False,
            default=200
        )
    ],
    function=generate_summary,
    module="generic"
))

tool_registry.register(ToolDefinition(
    name="calculate_metrics",
    description="Calculate specific metrics from numerical data",
    parameters=[
        ToolParameter(
            name="data",
            type="string",
            description="JSON formatted data with numerical fields"
        ),
        ToolParameter(
            name="metric_type",
            type="string",
            description="Type of metric: average, total, count, max, or min"
        )
    ],
    function=calculate_metrics,
    module="generic"
))

# Execute Python (guarded)
tool_registry.register(ToolDefinition(
    name="execute_python",
    description="Execute a small Python snippet safely. Returns stdout/stderr and exit code.",
    parameters=[
        ToolParameter(
            name="code",
            type="string",
            description="Python code to execute"
        ),
        ToolParameter(
            name="timeout_seconds",
            type="number",
            description="Max seconds to run before timing out",
            required=False,
            default=5
        ),
    ],
    function=execute_python,
    module="generic"
))

# Jargon AI translator
tool_registry.register(ToolDefinition(
    name="jargon_translate",
    description="Rewrite text for a target audience: exec, analyst, ops, or public.",
    parameters=[
        ToolParameter(
            name="text",
            type="string",
            description="Text to rewrite"
        ),
        ToolParameter(
            name="audience",
            type="string",
            description="Target audience",
            required=False,
            default="exec"
        ),
    ],
    function=jargon_translate,
    module="generic"
))

# Web search
tool_registry.register(ToolDefinition(
    name="web_search",
    description="Search the web and return top results (title, url, snippet)",
    parameters=[
        ToolParameter(name="query", type="string", description="Search query"),
        ToolParameter(name="max_results", type="number", description="Max results", required=False, default=5),
    ],
    function=web_search,
    module="generic"
))

# Datasets catalog
tool_registry.register(ToolDefinition(
    name="list_open_datasets",
    description="List curated open datasets with categories and curl examples",
    parameters=[],
    function=list_open_datasets,
    module="generic"
))

