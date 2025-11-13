"""
Advanced CSV analysis tools for data quality, statistics, and profiling.
"""

import json
import pandas as pd
import numpy as np
from typing import Any
from io import StringIO

from backend.tools.base import ToolDefinition, ToolParameter, tool_registry
from backend.core.logger import get_logger

logger = get_logger(__name__)


async def analyze_csv_stats(csv_data: str) -> str:
    """
    Comprehensive statistical analysis of CSV data including:
    - Basic statistics (mean, median, std, min, max)
    - Data quality metrics (missing values, fill rates)
    - Data types and cardinality
    - Outlier detection
    
    Args:
        csv_data: CSV formatted string data
        
    Returns:
        JSON with comprehensive statistics and quality metrics
    """
    try:
        df = pd.read_csv(StringIO(csv_data))
        
        # Basic info
        total_rows = len(df)
        total_cols = len(df.columns)
        memory_usage = df.memory_usage(deep=True).sum() / 1024  # KB
        
        # Column-level analysis
        columns_analysis = []
        for col in df.columns:
            col_data = df[col]
            missing_count = col_data.isna().sum()
            fill_rate = ((total_rows - missing_count) / total_rows) * 100
            
            col_info = {
                "name": col,
                "dtype": str(col_data.dtype),
                "missing_count": int(missing_count),
                "fill_rate": round(fill_rate, 2),
                "unique_values": int(col_data.nunique()),
                "cardinality": "high" if col_data.nunique() > total_rows * 0.9 else "medium" if col_data.nunique() > 10 else "low",
            }
            
            # Numeric column stats
            if pd.api.types.is_numeric_dtype(col_data):
                col_info.update({
                    "mean": round(float(col_data.mean()), 2) if not col_data.isna().all() else None,
                    "median": round(float(col_data.median()), 2) if not col_data.isna().all() else None,
                    "std": round(float(col_data.std()), 2) if not col_data.isna().all() else None,
                    "min": round(float(col_data.min()), 2) if not col_data.isna().all() else None,
                    "max": round(float(col_data.max()), 2) if not col_data.isna().all() else None,
                    "q25": round(float(col_data.quantile(0.25)), 2) if not col_data.isna().all() else None,
                    "q75": round(float(col_data.quantile(0.75)), 2) if not col_data.isna().all() else None,
                })
                
                # Detect outliers using IQR method
                if not col_data.isna().all():
                    q1 = col_data.quantile(0.25)
                    q3 = col_data.quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outliers = ((col_data < lower_bound) | (col_data > upper_bound)).sum()
                    col_info["outliers_count"] = int(outliers)
                    col_info["outliers_pct"] = round((outliers / total_rows) * 100, 2)
            
            # Categorical column stats
            elif pd.api.types.is_string_dtype(col_data) or pd.api.types.is_object_dtype(col_data):
                value_counts = col_data.value_counts()
                col_info["top_values"] = [
                    {"value": str(val), "count": int(count)} 
                    for val, count in value_counts.head(5).items()
                ]
            
            columns_analysis.append(col_info)
        
        # Overall data quality score
        avg_fill_rate = sum(c["fill_rate"] for c in columns_analysis) / total_cols
        quality_score = round(avg_fill_rate, 2)
        quality_grade = "A" if quality_score >= 95 else "B" if quality_score >= 85 else "C" if quality_score >= 70 else "D"
        
        # Detect potential coordinate columns
        potential_coords = {
            "latitude": None,
            "longitude": None,
            "timestamp": None,
        }
        
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ["lat", "latitude"]) and pd.api.types.is_numeric_dtype(df[col]):
                potential_coords["latitude"] = col
            elif any(x in col_lower for x in ["lon", "lng", "longitude"]) and pd.api.types.is_numeric_dtype(df[col]):
                potential_coords["longitude"] = col
            elif any(x in col_lower for x in ["time", "date", "timestamp"]):
                potential_coords["timestamp"] = col
        
        result = {
            "summary": {
                "total_rows": total_rows,
                "total_columns": total_cols,
                "memory_kb": round(memory_usage, 2),
                "quality_score": quality_score,
                "quality_grade": quality_grade,
                "avg_fill_rate": round(avg_fill_rate, 2),
            },
            "columns": columns_analysis,
            "potential_coordinates": potential_coords,
            "sample_rows": df.head(3).to_dict(orient="records"),
        }
        
        logger.info("csv_stats_analyzed", rows=total_rows, cols=total_cols, quality=quality_grade)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error("csv_stats_failed", error=str(e))
        return json.dumps({"error": str(e)})


# Register the tool
tool_registry.register(ToolDefinition(
    name="analyze_csv_stats",
    description="Perform comprehensive statistical analysis of CSV data including data quality, fill rates, distributions, and outliers",
    parameters=[
        ToolParameter(
            name="csv_data",
            type="string",
            description="CSV formatted string data to analyze"
        )
    ],
    function=analyze_csv_stats,
    module="generic"
))

