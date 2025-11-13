import React from 'react';
import Plot from 'react-plotly.js';

interface GeoPlotProps {
  geojson?: any;
  anomalies?: { id: number; coordinates: [number, number]; value: number; z_score?: number }[];
}

function extractPoints(geojson: any) {
  if (!geojson || geojson.type !== 'FeatureCollection') return { lats: [], lons: [], values: [] };
  const lats: number[] = [];
  const lons: number[] = [];
  const values: number[] = [];
  for (const f of geojson.features || []) {
    const [lon, lat] = f.geometry?.coordinates || [0, 0];
    lats.push(lat);
    lons.push(lon);
    values.push(Number(f.properties?.value ?? 0));
  }
  return { lats, lons, values };
}

export const GeoPlot: React.FC<GeoPlotProps> = ({ geojson, anomalies }) => {
  const { lats, lons, values } = extractPoints(geojson);

  if (lats.length === 0) {
    return null;
  }

  const heatmap = {
    type: 'densitymapbox' as const,
    lat: lats,
    lon: lons,
    z: values,
    colorscale: [
      [0, '#0ea5e9'],
      [0.5, '#6366f1'],
      [1, '#bd34fe'],
    ],
    radius: 20,
  };

  // If anomalies passed, plot them; otherwise, plot all points in 3D
  const anomalyData = (anomalies && anomalies.length > 0)
    ? {
        x: anomalies.map((a) => a.coordinates[0]),
        y: anomalies.map((a) => a.coordinates[1]),
        z: anomalies.map((a) => a.value || 0),
      }
    : { x: lons, y: lats, z: values.map((v) => v || 0) };

  const anomalyScatter = {
    type: 'scatter3d' as const,
    mode: 'markers' as const,
    x: anomalyData.x,
    y: anomalyData.y,
    z: anomalyData.z,
    marker: { color: '#ef4444', size: 4 },
    name: (anomalies && anomalies.length > 0) ? 'Anomalies' : 'Points',
  };

  const layout2d: any = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 20, r: 20, t: 20, b: 20 },
    mapbox: {
      style: 'carto-darkmatter',
      center: { lat: lats[0] || 0, lon: lons[0] || 0 },
      zoom: 10,
    },
    showlegend: false,
  };

  const layout3d: any = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    scene: {
      xaxis: { title: 'Longitude', color: '#a1a1aa' },
      yaxis: { title: 'Latitude', color: '#a1a1aa' },
      zaxis: { title: 'Traffic', color: '#a1a1aa' },
      bgcolor: 'rgba(0,0,0,0)'
    },
    margin: { l: 20, r: 20, t: 20, b: 20 },
    showlegend: false,
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
      <div className="glass-effect" style={{ height: 360, border: '1px solid var(--border-primary)', borderRadius: 12, overflow: 'hidden' }}>
        <Plot
          data={[heatmap] as any}
          layout={layout2d}
          config={{ displayModeBar: false, mapboxAccessToken: undefined }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
        />
      </div>
      <div className="glass-effect" style={{ height: 360, border: '1px solid var(--border-primary)', borderRadius: 12, overflow: 'hidden' }}>
        <Plot
          data={[anomalyScatter] as any}
          layout={layout3d}
          config={{ displayModeBar: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
        />
      </div>
    </div>
  );
};
