import React from 'react';
import { User, Cpu } from 'lucide-react';
import { GeoPlot } from './GeoPlot';
import { PipelineSteps } from './PipelineSteps';
import { useAppStore } from '../store/useAppStore';
import type { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const { pipelineSteps } = useAppStore();
  const steps = pipelineSteps.get(message.timestamp) || [];
  
  // Extract geo data from metadata if available
  const geoData = message.metadata?.geo_data as any;
  const anomalies = message.metadata?.anomalies as any;
  const code = (message.metadata as any)?.code as string | undefined;
  const codeOutput = (message.metadata as any)?.code_output as string | undefined;
  const codeError = (message.metadata as any)?.code_error as string | undefined;
  const codeExit = (message.metadata as any)?.code_exit as number | undefined;

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-icon">
        {isUser ? <User size={16} /> : <Cpu size={16} />}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-role">{isUser ? 'You' : 'Neuroverse'}</span>
          <span className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>
        
        {/* Show pipeline steps if they exist */}
        {!isUser && steps.length > 0 && (
          <PipelineSteps steps={steps} />
        )}
        
        <div className="message-text">{message.content}</div>
        
        {/* Render GeoPlot inline if geo data exists */}
        {geoData && (
          <div style={{ marginTop: 16 }}>
            <GeoPlot geojson={geoData} anomalies={Array.isArray(anomalies) ? anomalies : []} />
          </div>
        )}

        {code && (
          <div style={{ marginTop: 16, border: '1px solid var(--border-primary)', borderRadius: 12, overflow: 'hidden' }}>
            <div style={{ padding: '8px 12px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)', fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
              <span>Python Execution</span>
              <span style={{ color: codeExit === 0 ? 'var(--accent-primary)' : 'var(--error)' }}>exit {codeExit}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0 }}>
              <pre style={{ margin: 0, padding: 12, background: 'var(--bg-secondary)', color: 'var(--text-primary)', borderRight: '1px solid var(--border-primary)', overflowX: 'auto' }}>{code}</pre>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <pre style={{ margin: 0, padding: 12, background: 'var(--bg-secondary)', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-primary)', overflowX: 'auto' }}>{codeOutput || ''}</pre>
                {codeError && <pre style={{ margin: 0, padding: 12, background: '#2a1a1a', color: '#ff9a9a', overflowX: 'auto' }}>{codeError}</pre>}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

