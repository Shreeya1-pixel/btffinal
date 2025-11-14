import React, { useEffect } from 'react';
import { Header } from './components/Header';
import { ChatPanel } from './components/ChatPanel';
import { TracePanel } from './components/TracePanel';
import { AnomalyLab } from './components/AnomalyLab';
import { RedisMonitor } from './components/RedisMonitor';
import { AppSidebar } from './components/AppSidebar';
import { useAppStore } from './store/useAppStore';
import { api } from './services/api';

import './components/AppSidebar.css';

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
    } catch (error: any) {
      console.error('Failed to send message:', error);
      
      // Extract error message from API response
      let errorMessage = 'Sorry, I encountered an error processing your request.';
      
      if (error?.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (detail.includes('quota') || detail.includes('429')) {
          errorMessage = '⚠️ API Quota Exceeded: Your OpenAI API key has exceeded its quota. Please check your billing and add credits at https://platform.openai.com/account/billing';
        } else if (detail.includes('401') || detail.includes('Invalid API key')) {
          errorMessage = '⚠️ Invalid API Key: Please check your OpenAI API key configuration.';
        } else if (detail.includes('model')) {
          errorMessage = `⚠️ Model Error: ${detail}`;
        } else {
          errorMessage = `⚠️ Error: ${detail}`;
        }
      } else if (error?.message) {
        errorMessage = `⚠️ Error: ${error.message}`;
      }
      
      addMessage({
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproval = async (action: string, data: any) => {
    try {
      setIsLoading(true);

      if (action === 'send_whatsapp') {
        const result = await api.sendWhatsAppMessage({
          phone_number: data.phone_number,
          message: data.message,
        });

        if (result.status === 'link_generated' && result.whatsapp_url) {
          addMessage({
            role: 'assistant',
            content: `✓ Opening WhatsApp to send message to ${data.to_name || data.phone_number}...`,
            timestamp: new Date().toISOString(),
            metadata: { final_status: result },
          });
          window.open(result.whatsapp_url, '_blank');
        } else {
          throw new Error(result.message || 'Failed to generate WhatsApp link.');
        }
      } else if (action === 'send_gmail') {
        // Gmail uses mailto link
        const mailto_link = `mailto:${data.to}?subject=${encodeURIComponent(data.subject)}&body=${encodeURIComponent(data.body)}`;
        
        addMessage({
          role: 'assistant',
          content: `✓ Opening your email client to send to ${data.to_name || data.to}...`,
          timestamp: new Date().toISOString(),
        });
        window.open(mailto_link, '_blank');
      } else if (action === 'send_instagram') {
        // Instagram opens the DM conversation
        const instagram_url = `https://www.instagram.com/direct/t/${data.instagram_handle?.replace('@', '')}`;
        
        addMessage({
          role: 'assistant',
          content: `✓ Opening Instagram to send message to ${data.to_name || data.instagram_handle}...<br><br>Please manually send: "${data.message}"`,
          timestamp: new Date().toISOString(),
        });
        window.open(instagram_url, '_blank');
      } else {
        throw new Error(`Unknown action: ${action}`);
      }
    } catch (error: any) {
      console.error('Failed to handle approval:', error);
      addMessage({
        role: 'assistant',
        content: `⚠️ Error: ${error?.response?.data?.detail || error.message}`,
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

  const handleAppClick = (appId: string) => {
    console.log('App clicked:', appId);
    // Handle app-specific actions
    if (appId === 'gmail') {
      handleSendMessage('Open Gmail and show my inbox');
    } else if (appId === 'whatsapp') {
      handleSendMessage('Open WhatsApp and show my recent chats');
    } else if (appId === 'instagram') {
      handleSendMessage('Open Instagram and show my feed');
    } else if (appId === 'noon') {
      handleSendMessage('Open Noon and show my orders');
    }
  };

  const handleAddApp = () => {
    console.log('Add app clicked');
  };

  return (
    <div className="app-container">
      <AppSidebar onAppClick={handleAppClick} onAddApp={handleAddApp} />
      <div className="main-content">
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
            <ChatPanel onSendMessage={handleSendMessage} onApproval={handleApproval} />
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
    </div>
  );
};

export default App;

