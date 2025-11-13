import React from 'react';
import Plot from 'react-plotly.js';

interface ShapPlotProps {
  shap?: Array<{ id: number; values: { lat: number; lon: number; value: number } }> | null;
}

export const ShapPlot: React.FC<ShapPlotProps> = ({ shap }) => {
  if (!shap || shap.length === 0) return null;

  // Aggregate mean absolute shap across top-k anomalies
  const agg = { lat: 0, lon: 0, value: 0 } as Record<string, number>;
  shap.forEach((s) => {
    agg.lat += Math.abs(s.values.lat);
    agg.lon += Math.abs(s.values.lon);
    agg.value += Math.abs(s.values.value);
  });
  const keys = Object.keys(agg);
  const vals = keys.map((k) => agg[k] / shap.length);

  return (
    <div className="glass-effect" style={{ border: '1px solid var(--border-primary)', borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ padding: '8px 12px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)', fontSize: 12 }}>Feature importance (mean |SHAP|)</div>
      <Plot
        data={[
          {
            type: 'bar',
            orientation: 'h',
            x: vals,
            y: keys.map((k) => k.toUpperCase()),
            marker: { color: ['#00ffa3', '#00e5ff', '#a8b2c8'] },
          } as any,
        ]}
        layout={{
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          margin: { l: 60, r: 20, t: 10, b: 30 },
          showlegend: false,
        } as any}
        config={{ displayModeBar: false }}
        style={{ width: '100%', height: 240 }}
        useResizeHandler
      />
    </div>
  );
};


