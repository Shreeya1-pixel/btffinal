import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Upload, Database } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const { sessionId, anomalyMode, setIsLoading, setGeoData, addMessage, setAnomalyMode } = useAppStore();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="chat-input-container" onSubmit={handleSubmit}>
      <div className="chat-input-wrapper">
        {/* Mode toggle */}
        <button
          type="button"
          onClick={() => setAnomalyMode(anomalyMode === 'live' ? 'dataset' : 'live')}
          className="mode-toggle"
          style={{ marginRight: 8 }}
          title={`Anomaly mode: ${anomalyMode}`}
        >
          <Database size={16} color={anomalyMode === 'dataset' ? 'var(--accent-primary)' : 'var(--text-tertiary)'} />
        </button>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything... (Shift+Enter for new line)"
          disabled={disabled}
          rows={1}
          className="chat-input"
        />
        {/* Upload */}
        <input ref={fileRef} type="file" accept=".csv,text/csv" style={{ display: 'none' }} onChange={async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          setIsLoading(true);
          try {
            const res = await api.uploadAnomalyDataset({ file, sessionId: sessionId || undefined, topK: 10 });
            const geo = JSON.parse(res.geojson);
            const anom = JSON.parse(res.anomalies).anomalies;
            setGeoData(geo, anom);
            addMessage({ role: 'assistant', content: 'Uploaded dataset processed. Showing anomalies (IsolationForest).', timestamp: new Date().toISOString(), metadata: { module: 'gis-anomaly', geo_data: geo, anomalies: anom } });
          } catch (err) {
            addMessage({ role: 'assistant', content: 'Failed to process dataset.', timestamp: new Date().toISOString() });
          } finally {
            setIsLoading(false);
            if (fileRef.current) fileRef.current.value = '';
          }
        }} />
        <button type="button" onClick={() => fileRef.current?.click()} className="send-button" title="Upload CSV for anomaly detection" style={{ marginRight: 8 }}>
          <Upload size={18} />
        </button>
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="send-button"
        >
          {disabled ? (
            <Loader2 size={20} className="spinner" />
          ) : (
            <Send size={20} />
          )}
        </button>
      </div>
    </form>
  );
};

