import React from 'react';
import { Clock, Zap, GitBranch, Check } from 'lucide-react';
import type { TraceInfo } from '../types';

interface TracePanelProps {
  traces: TraceInfo[];
}

export const TracePanel: React.FC<TracePanelProps> = ({ traces }) => {
  if (traces.length === 0) {
    return (
      <div className="trace-panel">
        <div className="trace-empty">
          <GitBranch size={32} />
          <p>No trace data yet</p>
          <span>Agent execution traces will appear here</span>
        </div>
      </div>
    );
  }

  return (
    <div className="trace-panel">
      <div className="trace-header">
        <h3>Agent Trace</h3>
        <span className="trace-count">{traces.length} steps</span>
      </div>

      <div className="trace-list">
        {traces.map((trace, index) => (
          <div key={index} className="trace-item">
            <div className="trace-item-header">
              <div className="trace-agent">
                <Check size={14} className="trace-icon" />
                <span className="trace-name">{trace.agent_name}</span>
              </div>
              <span className="trace-role">{trace.role}</span>
            </div>

            {trace.tools_called.length > 0 && (
              <div className="trace-tools">
                <Zap size={12} />
                <span>Tools:</span>
                <div className="trace-tool-list">
                  {trace.tools_called.map((tool, i) => (
                    <span key={i} className="trace-tool-badge">
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {trace.handoffs.length > 0 && (
              <div className="trace-handoffs">
                <GitBranch size={12} />
                <span>Handoffs:</span>
                <div className="trace-handoff-list">
                  {trace.handoffs.map((handoff, i) => (
                    <span key={i}>{handoff}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="trace-footer">
              <div className="trace-time">
                <Clock size={12} />
                <span>
                  {trace.duration_ms
                    ? `${trace.duration_ms.toFixed(0)}ms`
                    : 'N/A'}
                </span>
              </div>
              <span className="trace-timestamp">
                {new Date(trace.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

