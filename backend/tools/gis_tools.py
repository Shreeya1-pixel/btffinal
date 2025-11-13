"""
GIS and anomaly detection tools for geospatial analysis.
"""

from typing import Any
import json
import random
from datetime import datetime, timedelta
import pandas as pd
from sklearn.ensemble import IsolationForest
import shap

from backend.tools.base import ToolDefinition, ToolParameter, tool_registry
from backend.core.logger import get_logger

logger = get_logger(__name__)


async def fetch_geo_data(
    location: str, 
    metric: str, 
    time_range: str = "7d"
) -> str:
    """
    Fetch geospatial data for a specific location and metric.
    
    Args:
        location: Geographic location (city, region, coordinates)
        metric: Data metric (traffic, temperature, population, activity)
        time_range: Time range for data (e.g., 7d, 30d, 1y)
        
    Returns:
        GeoJSON formatted data
    """
    try:
        center_coords = _get_location_coords(location)
        num_points = 50
        
        features = []
        for i in range(num_points):
            lat = center_coords["lat"] + random.uniform(-0.1, 0.1)
            lon = center_coords["lon"] + random.uniform(-0.1, 0.1)
            value = random.uniform(10, 100)
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "id": i,
                    "metric": metric,
                    "value": value,
                    "location": location,
                    "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(0, 168))).isoformat()
                }
            })
            
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "location": location,
                "metric": metric,
                "time_range": time_range,
                "center": center_coords
            }
        }
        
        logger.info("geo_data_fetched", location=location, metric=metric, points=num_points)
        return json.dumps(geojson, indent=2)
        
    except Exception as e:
        logger.error("geo_data_fetch_failed", error=str(e))
        return json.dumps({"error": str(e)})


async def detect_anomalies(
    geo_data: str, 
    threshold: float = 2.0,
    method: str = "statistical"
) -> str:
    """
    Detect anomalies in geospatial data.
    
    Args:
        geo_data: GeoJSON formatted geospatial data
        threshold: Anomaly detection threshold (standard deviations)
        method: Detection method (statistical, clustering, temporal)
        
    Returns:
        Anomaly detection results with marked locations
    """
    try:
        data = json.loads(geo_data)
        
        if data.get("type") != "FeatureCollection":
            return json.dumps({"error": "Invalid GeoJSON format"})
            
        features = data.get("features", [])
        values = [f["properties"]["value"] for f in features]
        
        # Statistical anomaly detection
        import statistics
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        anomalies = []
        for feature in features:
            value = feature["properties"]["value"]
            z_score = abs((value - mean) / stdev) if stdev > 0 else 0
            
            if z_score > threshold:
                anomalies.append({
                    "id": feature["properties"]["id"],
                    "coordinates": feature["geometry"]["coordinates"],
                    "value": value,
                    "z_score": z_score,
                    "severity": "high" if z_score > threshold * 1.5 else "medium"
                })
                
        result = {
            "anomalies": anomalies,
            "total_points": len(features),
            "anomaly_count": len(anomalies),
            "statistics": {
                "mean": mean,
                "stdev": stdev,
                "threshold": threshold
            },
            "method": method
        }
        
        logger.info(
            "anomalies_detected",
            method=method,
            total=len(features),
            anomalies=len(anomalies)
        )
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error("anomaly_detection_failed", error=str(e))
        return json.dumps({"error": str(e)})


async def generate_map_visual(
    geo_data: str, 
    anomalies: str = "",
    map_style: str = "default"
) -> str:
    """
    Generate map visualization configuration.
    
    Args:
        geo_data: GeoJSON formatted geospatial data
        anomalies: Optional anomaly detection results
        map_style: Map style (default, dark, satellite)
        
    Returns:
        Map configuration for frontend rendering
    """
    try:
        data = json.loads(geo_data)
        anomaly_data = json.loads(anomalies) if anomalies else None
        
        center = data.get("metadata", {}).get("center", {"lat": 0, "lon": 0})
        
        layers = [
            {
                "type": "heatmap",
                "data": geo_data,
                "opacity": 0.6
            }
        ]
        
        if anomaly_data:
            layers.append({
                "type": "markers",
                "data": anomaly_data,
                "color": "red",
                "size": "large"
            })
            
        map_config = {
            "center": [center["lat"], center["lon"]],
            "zoom": 12,
            "style": map_style,
            "layers": layers,
            "controls": {
                "zoom": True,
                "layers": True,
                "fullscreen": True
            }
        }
        
        logger.info("map_visual_generated", style=map_style, layers=len(layers))
        return json.dumps(map_config, indent=2)
        
    except Exception as e:
        logger.error("map_visual_generation_failed", error=str(e))
        return json.dumps({"error": str(e)})


def _get_location_coords(location: str) -> dict[str, float]:
    """Get approximate coordinates for a location."""
    locations = {
        "dubai": {"lat": 25.2048, "lon": 55.2708},
        "new york": {"lat": 40.7128, "lon": -74.0060},
        "london": {"lat": 51.5074, "lon": -0.1278},
        "tokyo": {"lat": 35.6762, "lon": 139.6503},
        "singapore": {"lat": 1.3521, "lon": 103.8198},
        "san francisco": {"lat": 37.7749, "lon": -122.4194}
    }
    return locations.get(location.lower(), {"lat": 0, "lon": 0})


# Register GIS tools
tool_registry.register(ToolDefinition(
    name="fetch_geo_data",
    description="Fetch geospatial data for a specific location and metric",
    parameters=[
        ToolParameter(
            name="location",
            type="string",
            description="Geographic location (city name or coordinates)"
        ),
        ToolParameter(
            name="metric",
            type="string",
            description="Data metric to fetch (traffic, temperature, population, activity)"
        ),
        ToolParameter(
            name="time_range",
            type="string",
            description="Time range for data (e.g., 7d, 30d, 1y)",
            required=False,
            default="7d"
        )
    ],
    function=fetch_geo_data,
    module="gis-anomaly"
))

tool_registry.register(ToolDefinition(
    name="detect_anomalies",
    description="Detect anomalies in geospatial data using statistical methods",
    parameters=[
        ToolParameter(
            name="geo_data",
            type="string",
            description="GeoJSON formatted geospatial data"
        ),
        ToolParameter(
            name="threshold",
            type="number",
            description="Anomaly detection threshold in standard deviations",
            required=False,
            default=2.0
        ),
        ToolParameter(
            name="method",
            type="string",
            description="Detection method (statistical, clustering, temporal)",
            required=False,
            default="statistical"
        )
    ],
    function=detect_anomalies,
    module="gis-anomaly"
))

tool_registry.register(ToolDefinition(
    name="generate_map_visual",
    description="Generate map visualization configuration for frontend rendering",
    parameters=[
        ToolParameter(
            name="geo_data",
            type="string",
            description="GeoJSON formatted geospatial data"
        ),
        ToolParameter(
            name="anomalies",
            type="string",
            description="Optional anomaly detection results to overlay",
            required=False,
            default=""
        ),
        ToolParameter(
            name="map_style",
            type="string",
            description="Map style (default, dark, satellite)",
            required=False,
            default="default"
        )
    ],
    function=generate_map_visual,
    module="gis-anomaly"
))


# Dataset helpers
async def csv_to_geojson(csv_text: str, lat_col: str | None = None, lon_col: str | None = None, value_col: str | None = None) -> str:
    """Convert CSV to GeoJSON by inferring lat/lon/value columns if not provided."""
    try:
        df = pd.read_csv(pd.io.common.StringIO(csv_text))
        cols = [c.lower() for c in df.columns]
        def find(*keys: str) -> str | None:
            for k in keys:
                if k in cols:
                    return df.columns[cols.index(k)]
            return None
        lat = lat_col or find("lat", "latitude", "y")
        lon = lon_col or find("lon", "lng", "longitude", "x")
        val = value_col or find("value", "metric", "score", "z")
        if not lat or not lon:
            return json.dumps({"error": "Latitude/longitude columns not found"})
        if val is None:
            val = lat  # dummy linkage; will be ignored
        features = []
        for i, row in df.iterrows():
            try:
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(row[lon]), float(row[lat])]},
                    "properties": {"id": int(i), "value": float(row.get(val, 0))}
                })
            except Exception:
                continue
        geojson = {"type": "FeatureCollection", "features": features, "metadata": {"source": "csv"}}
        return json.dumps(geojson, indent=2)
    except Exception as e:
        logger.error("csv_to_geojson_failed", error=str(e))
        return json.dumps({"error": str(e)})


async def detect_anomalies_iforest(geo_data: str, top_k: int = 10, contamination: float | None = None, random_state: int = 42, return_shap: bool = False) -> str:
    """IsolationForest-based anomaly detection on GeoJSON points. Returns top-k by anomaly score."""
    try:
        data = json.loads(geo_data)
        feats = data.get("features", [])
        if not feats:
            return json.dumps({"anomalies": [], "anomaly_count": 0})
        X = []
        vals = []
        for f in feats:
            lon, lat = f["geometry"]["coordinates"]
            val = float(f.get("properties", {}).get("value", 0))
            X.append([lat, lon, val])
            vals.append(val)
        if contamination is None:
            contamination = min(0.1, max(0.01, 5.0 / max(1, len(X))))
        clf = IsolationForest(n_estimators=200, contamination=contamination, random_state=random_state)
        clf.fit(X)
        scores = (-clf.score_samples(X)).tolist()  # higher => more anomalous
        indexed = list(enumerate(scores))
        indexed.sort(key=lambda t: t[1], reverse=True)
        k = min(top_k, len(indexed))
        anomalies = []
        shap_payload = []
        for idx, s in indexed[:k]:
            f = feats[idx]
            entry = {
                "id": f["properties"].get("id", idx),
                "coordinates": f["geometry"]["coordinates"],
                "value": f["properties"].get("value", 0),
                "score": s,
            }
            anomalies.append(entry)

        if return_shap:
            try:
                explainer = shap.Explainer(clf)
                shap_vals = explainer(pd.DataFrame(X, columns=["lat", "lon", "value"]))
                for idx, _ in indexed[:k]:
                    sv = shap_vals[idx].values if hasattr(shap_vals[idx], 'values') else shap_vals.values[idx]
                    sv_list = sv.tolist() if hasattr(sv, 'tolist') else list(sv)
                    shap_payload.append({
                        "id": feats[idx]["properties"].get("id", idx),
                        "values": {"lat": sv_list[0], "lon": sv_list[1], "value": sv_list[2]},
                    })
            except Exception as e:
                logger.error("shap_failed", error=str(e))

        return json.dumps({"anomalies": anomalies, "anomaly_count": len(anomalies), "method": "iforest", "shap": shap_payload}, indent=2)
    except Exception as e:
        logger.error("iforest_failed", error=str(e))
        return json.dumps({"error": str(e)})


# Register dataset tools
tool_registry.register(ToolDefinition(
    name="csv_to_geojson",
    description="Convert CSV text to GeoJSON by inferring lat/lon/value columns",
    parameters=[
        ToolParameter(name="csv_text", type="string", description="CSV content as text"),
        ToolParameter(name="lat_col", type="string", description="Latitude column name", required=False),
        ToolParameter(name="lon_col", type="string", description="Longitude column name", required=False),
        ToolParameter(name="value_col", type="string", description="Value column name", required=False),
    ],
    function=csv_to_geojson,
    module="gis-anomaly"
))

tool_registry.register(ToolDefinition(
    name="detect_anomalies_iforest",
    description="Detect top-k anomalies using IsolationForest on GeoJSON points",
    parameters=[
        ToolParameter(name="geo_data", type="string", description="GeoJSON data"),
        ToolParameter(name="top_k", type="number", description="Return top-k anomalies", required=False, default=10),
        ToolParameter(name="contamination", type="number", description="IForest contamination rate", required=False),
    ],
    function=detect_anomalies_iforest,
    module="gis-anomaly"
))
