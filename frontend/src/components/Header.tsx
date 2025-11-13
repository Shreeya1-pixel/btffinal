import React from 'react';
import { Terminal, Activity, Zap, Trash2 } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

export const Header: React.FC = () => {
  const { activeModule, showTraces, toggleTraces, reset, setSessionId, setAnomalyMode, activeTab, setActiveTab } = useAppStore();

  const handleClear = async () => {
    reset();
    const { session_id } = await api.createSession();
    setSessionId(session_id);
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo-section">
          <div className="logo-icon">
            <Terminal size={24} />
          </div>
          <div className="logo-text">
            <h1 className="gradient-text">Neuroverse</h1>
            <span className="logo-subtitle">AI Agent Platform</span>
          </div>
        </div>

        <div className="header-info">
          {activeModule && (
            <div className="module-badge">
              <Zap size={14} />
              <span>{activeModule}</span>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ display: 'flex', background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)', borderRadius: 10, overflow: 'hidden' }}>
            <button onClick={() => setActiveTab('chat')} className="trace-toggle" style={{ border: 'none', borderRadius: 0, padding: '8px 12px', background: activeTab==='chat' ? 'var(--accent-primary)' : 'transparent', color: activeTab==='chat' ? '#000' : 'var(--text-secondary)' }}>Chat</button>
            <button onClick={() => { setActiveTab('anomaly'); setAnomalyMode('dataset'); }} className="trace-toggle" style={{ border: 'none', borderRadius: 0, padding: '8px 12px', background: activeTab==='anomaly' ? 'var(--accent-primary)' : 'transparent', color: activeTab==='anomaly' ? '#000' : 'var(--text-secondary)' }}>Anomaly Lab</button>
          </div>
          <button
            className={`trace-toggle ${showTraces ? 'active' : ''}`}
            onClick={toggleTraces}
            title="Toggle Agent Trace"
          >
            <Activity size={18} />
            <span>Trace</span>
          </button>
          <button
            className="trace-toggle"
            onClick={handleClear}
            title="Clear Chat"
          >
            <Trash2 size={18} />
            <span>Clear</span>
          </button>
        </div>
      </div>
    </header>
  );
};

