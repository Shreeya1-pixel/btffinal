import React, { useEffect } from 'react';
import { Header } from './components/Header';
import { ChatPanel } from './components/ChatPanel';
import { TracePanel } from './components/TracePanel';
import { AnomalyLab } from './components/AnomalyLab';
import { RedisMonitor } from './components/RedisMonitor';
import { useAppStore } from './store/useAppStore';
import { api } from './services/api';

const App: React.FC = () => {
  const {
    sessionId,
    traces,
    showTraces,
    setSessionId,
    addMessage,
    addTraces,
    setActiveModule,
    setIsLoading,
    setModules,
    llmMode,
    setLlmMode,
    setGeoData,
  } = useAppStore();

  useEffect(() => {
    const initialize = async () => {
      try {
        const { session_id } = await api.createSession();
        setSessionId(session_id);

        const { modules } = await api.getModules();
        setModules(modules);

        const health = await api.healthCheck();
        setLlmMode(health.llm_mode as 'cloud' | 'local');
      } catch (error) {
        console.error('Failed to initialize:', error);
      }
    };

    initialize();
  }, [setSessionId, setModules]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    addMessage({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    });

    setIsLoading(true);

    try {
      const response = await api.sendQuery(message, sessionId || undefined);

      // Extract geo data for plotting when GIS module
      let geoDataForMessage = null;
      let anomaliesForMessage = null;
      
      if (response.module === 'gis-anomaly') {
        try {
          const geoTool = response.tool_results.find((t: any) => t.tool === 'fetch_geo_data');
          const anomTool = response.tool_results.find((t: any) => t.tool === 'detect_anomalies');
          
          if (geoTool) {
            geoDataForMessage = JSON.parse(geoTool.result);
            setGeoData(geoDataForMessage, null);
          }
          
          if (anomTool) {
            const anomResult = JSON.parse(anomTool.result);
            anomaliesForMessage = anomResult.anomalies;
            setGeoData(geoDataForMessage, anomaliesForMessage);
          }
        } catch (e) {
          console.error('Failed to parse geo data:', e);
        }
      }

      // Extract Python execution result if present
      let codeResult: any = null;
      const execTool = response.tool_results.find((t: any) => t.tool === 'execute_python');
      if (execTool) {
        try {
          codeResult = JSON.parse(execTool.result);
        } catch {}
      }

      addMessage({
        role: 'assistant',
        content: response.content,
        timestamp: new Date().toISOString(),
        metadata: {
          module: response.module,
          duration_ms: response.duration_ms,
          geo_data: geoDataForMessage,
          anomalies: anomaliesForMessage,
          code_output: codeResult?.stdout,
          code_error: codeResult?.stderr,
          code_exit: codeResult?.exit_code,
          code: codeResult?.code,
        },
      });

      addTraces(response.traces);
      setActiveModule(response.module);
      setSessionId(response.session_id);
    } catch (error) {
      console.error('Failed to send message:', error);
      addMessage({
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request.',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const { activeTab, updatePipelineStep, messages } = useAppStore();

  // Listen for Redis events including pipeline steps
  React.useEffect(() => {
    const eventSource = new EventSource(`${import.meta.env.VITE_API_URL}/api/events`);
    
    eventSource.addEventListener('message', (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'pipeline_step') {
          // Find the latest assistant message ID to attach steps to
          const latestAssistantMsg = messages.filter(m => m.role === 'assistant').pop();
          if (latestAssistantMsg) {
            updatePipelineStep(latestAssistantMsg.timestamp, {
              step: data.step,
              status: data.status,
              message: data.message,
              label: data.step.split('_').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
            });
          }
        }
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    });

    return () => eventSource.close();
  }, [messages, updatePipelineStep]);

  return (
    <div className="app">
      <Header />
      {llmMode === 'local' && (
        <div style={{ padding: '8px 16px', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-primary)', color: 'var(--text-tertiary)', fontSize: 12 }}>
          Parallel multi-agent execution is limited in local mode. Switch to cloud mode for full features.
        </div>
      )}
      <main className="app-main">
        <div className={`chat-container ${showTraces ? 'with-trace' : ''}`}>
          {/* Quick tab switch by tracking header state via query selector would be brittle; we keep Chat default and provide Anomaly Lab via route-like toggle using local state for now. */}
          {activeTab === 'anomaly' ? (
            <AnomalyLab />
          ) : (
            <ChatPanel onSendMessage={handleSendMessage} />
          )}
        </div>
        {showTraces && (
          <div className="trace-container">
            <TracePanel traces={traces} />
          </div>
        )}
      </main>
      <RedisMonitor />
    </div>
  );
};

export default App;

