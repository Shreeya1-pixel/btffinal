import React, { useRef, useState } from 'react';
import { Upload, Zap, Loader2, BarChart3, Brain } from 'lucide-react';
import { api } from '../services/api';
import { useAppStore } from '../store/useAppStore';
import { DataStatsPanel } from './DataStatsPanel';
import { GeoPlot } from './GeoPlot';
import { ShapPlot } from './ShapPlot';

export const AnomalyLab: React.FC = () => {
  const { sessionId, geojson, anomalies, setGeoData, setShap } = useAppStore();
  const fileRef = useRef<HTMLInputElement>(null);
  const [topK, setTopK] = useState<number>(10);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [csvStats, setCsvStats] = useState<any>(null);
  const [csvContent, setCsvContent] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const [step, setStep] = useState<'upload' | 'analyze' | 'detect'>('upload');
  const [analysisSteps, setAnalysisSteps] = useState<Array<{
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'error';
    message?: string;
  }>>([]);

  const updateStep = (name: string, status: 'pending' | 'in_progress' | 'completed' | 'error', message?: string) => {
    setAnalysisSteps(prev => {
      const existing = prev.find(s => s.name === name);
      if (existing) {
        return prev.map(s => s.name === name ? { ...s, status, message } : s);
      }
      return [...prev, { name, status, message }];
    });
  };

  const handleFileSelect = async (file: File) => {
    setFileName(file.name);
    setStep('analyze');
    setAnalyzing(true);
    setAnalysisSteps([]);
    
    try {
      // Step 1: Read file
      updateStep('read_file', 'in_progress', 'Reading CSV file...');
      const text = await file.text();
      setCsvContent(text);
      const lines = text.split('\n').filter(l => l.trim());
      const rows = lines.length - 1;
      updateStep('read_file', 'completed', `Read ${rows} rows from ${file.name}`);
      
      await new Promise(r => setTimeout(r, 300)); // Brief pause for UX
      
      // Step 2: Validate structure
      updateStep('validate', 'in_progress', 'Validating CSV structure...');
      const headers = lines[0].split(',');
      updateStep('validate', 'completed', `Found ${headers.length} columns: ${headers.join(', ')}`);
      
      await new Promise(r => setTimeout(r, 300));
      
      // Step 3: Perform local statistical analysis (no LLM needed)
      updateStep('analyze', 'in_progress', 'Computing statistics and data quality metrics...');
      
      // Send full CSV directly to analysis tool (bypass LLM)
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/analyze-stats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          csv_data: text,
          session_id: sessionId || undefined,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const stats = await response.json();
      
      // Step 4: Parse results
      updateStep('parse', 'in_progress', 'Processing analysis results...');
      if (stats.summary && stats.columns) {
        setCsvStats(stats);
        updateStep('analyze', 'completed', `Quality score: ${stats.summary.quality_score}% (Grade ${stats.summary.quality_grade})`);
        updateStep('parse', 'completed', `Analyzed ${stats.columns.length} columns with ${stats.summary.total_rows} rows`);
      } else {
        updateStep('analyze', 'error', 'Invalid analysis structure');
        updateStep('parse', 'error', 'Failed to parse results');
      }
    } catch (e: any) {
      const errorMsg = e.message || String(e);
      updateStep('analyze', 'error', errorMsg.substring(0, 150));
      console.error('Failed to analyze CSV:', e);
      
      // Show user-friendly error in UI
      setTimeout(() => {
        alert(`Analysis failed: ${errorMsg}\n\nPlease try again or use a smaller CSV file.`);
      }, 500);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDetectAnomalies = async () => {
    if (!csvContent) return;
    setLoading(true);
    setStep('detect');
    
    try {
      const res = await api.uploadAnomalyDataset({ 
        file: new File([csvContent], fileName, { type: 'text/csv' }), 
        sessionId: sessionId || undefined, 
        topK 
      });
      const geo = JSON.parse(res.geojson);
      const anomJson = JSON.parse(res.anomalies);
      setGeoData(geo, anomJson.anomalies);
      setShap(anomJson.shap || []);
    } catch (e) {
      console.error('Anomaly detection failed:', e);
    } finally {
      setLoading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleReset = () => {
    setStep('upload');
    setCsvStats(null);
    setCsvContent('');
    setFileName('');
    setGeoData(null, null);
    setShap([]);
    if (fileRef.current) fileRef.current.value = '';
  };

  return (
    <div style={{ 
      padding: 24, 
      height: '100%', 
      overflowY: 'auto',
      background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%)'
    }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ 
          fontSize: 32, 
          fontWeight: 700, 
          color: 'var(--text-primary)', 
          marginBottom: 8,
          background: 'linear-gradient(135deg, #00ffa3 0%, #00e5ff 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Anomaly Detection Lab
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-tertiary)' }}>
          Advanced ML-powered anomaly detection with comprehensive data analysis
        </p>
      </div>

      {/* Upload Section */}
      {step === 'upload' && (
        <div className="glass-effect" style={{ 
          padding: 32, 
          border: '2px dashed rgba(0, 255, 163, 0.3)', 
          borderRadius: 16,
          textAlign: 'center',
          background: 'linear-gradient(135deg, rgba(0, 255, 163, 0.03) 0%, rgba(0, 229, 255, 0.03) 100%)',
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const file = e.dataTransfer.files[0];
          if (file && file.name.endsWith('.csv')) handleFileSelect(file);
        }}>
          <input 
            ref={fileRef} 
            type="file" 
            accept=".csv,text/csv" 
            style={{ display: 'none' }} 
            onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])} 
          />
          <Upload size={48} color="var(--accent-primary)" style={{ marginBottom: 16 }} />
          <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
            Drop CSV file here or click to browse
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            Supports any CSV with numeric columns • Max 10MB
          </div>
        </div>
      )}

      {/* Analysis Section */}
      {step === 'analyze' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* File Info Bar */}
          <div className="glass-effect" style={{ 
            padding: 16, 
            border: '1px solid var(--border-primary)', 
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(15, 23, 42, 0.6)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <BarChart3 size={20} color="var(--accent-primary)" />
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{fileName}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  {analyzing ? 'Analyzing data quality...' : 'Analysis complete'}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button 
                className="send-button" 
                onClick={handleReset}
                style={{ padding: '8px 16px', fontSize: 13 }}
              >
                Reset
              </button>
            </div>
          </div>

          {analyzing || analysisSteps.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Analysis Progress Steps */}
              <div className="glass-effect" style={{ 
                padding: 20, 
                border: '1px solid rgba(0, 255, 163, 0.2)', 
                borderRadius: 12,
                background: 'linear-gradient(135deg, rgba(0, 255, 163, 0.03) 0%, rgba(15, 23, 42, 0.6) 100%)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <Brain size={20} color="var(--accent-primary)" />
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                    Analysis Pipeline
                  </div>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {analysisSteps.map((step, idx) => (
                    <div key={idx} style={{ 
                      display: 'flex', 
                      alignItems: 'flex-start', 
                      gap: 12,
                      padding: 12,
                      background: step.status === 'error' ? 'rgba(255, 71, 87, 0.05)' : 'rgba(30, 41, 59, 0.4)',
                      border: `1px solid ${
                        step.status === 'completed' ? 'rgba(0, 255, 163, 0.3)' :
                        step.status === 'error' ? 'rgba(255, 71, 87, 0.3)' :
                        'rgba(100, 116, 139, 0.2)'
                      }`,
                      borderRadius: 8,
                      transition: 'all 0.3s ease'
                    }}>
                      <div style={{ width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 2 }}>
                        {step.status === 'completed' && (
                          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <circle cx="10" cy="10" r="9" stroke="#00ffa3" strokeWidth="2" />
                            <path d="M6 10L9 13L14 7" stroke="#00ffa3" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        )}
                        {step.status === 'in_progress' && (
                          <Loader2 size={20} color="var(--accent-secondary)" className="spin" />
                        )}
                        {step.status === 'error' && (
                          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <circle cx="10" cy="10" r="9" stroke="#ff4757" strokeWidth="2" />
                            <path d="M7 7L13 13M13 7L7 13" stroke="#ff4757" strokeWidth="2" strokeLinecap="round" />
                          </svg>
                        )}
                        {step.status === 'pending' && (
                          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <circle cx="10" cy="10" r="9" stroke="#64748b" strokeWidth="2" strokeDasharray="4 4" />
                          </svg>
                        )}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ 
                          fontSize: 13, 
                          fontWeight: 600, 
                          color: step.status === 'error' ? '#ff4757' : 'var(--text-primary)',
                          marginBottom: 4,
                          textTransform: 'capitalize'
                        }}>
                          {step.name.replace(/_/g, ' ')}
                        </div>
                        {step.message && (
                          <div style={{ 
                            fontSize: 12, 
                            color: step.status === 'error' ? '#ff9a9a' : 'var(--text-tertiary)',
                            fontFamily: 'var(--font-mono)'
                          }}>
                            {step.message}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {!analyzing && csvStats && (
                <div style={{ textAlign: 'center', padding: 12 }}>
                  <div style={{ 
                    display: 'inline-flex', 
                    alignItems: 'center', 
                    gap: 8, 
                    padding: '8px 16px', 
                    background: 'rgba(0, 255, 163, 0.1)',
                    border: '1px solid rgba(0, 255, 163, 0.3)',
                    borderRadius: 8
                  }}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <circle cx="8" cy="8" r="7" stroke="#00ffa3" strokeWidth="2" />
                      <path d="M5 8L7 10L11 5" stroke="#00ffa3" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-primary)' }}>
                      Analysis Complete
                    </span>
                  </div>
                </div>
              )}
            </div>
          ) : null}
          
          {csvStats && !analyzing ? (
            <>
              <DataStatsPanel stats={csvStats} />
              
              {/* Detection Controls */}
              <div className="glass-effect" style={{ 
                padding: 20, 
                border: '1px solid rgba(0, 255, 163, 0.2)', 
                borderRadius: 12,
                background: 'linear-gradient(135deg, rgba(0, 255, 163, 0.05) 0%, rgba(15, 23, 42, 0.4) 100%)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <Brain size={20} color="var(--accent-primary)" />
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                    Anomaly Detection Configuration
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 8, display: 'block' }}>
                      Top-K Anomalies
                    </label>
                    <input 
                      type="number" 
                      min={1} 
                      max={100} 
                      value={topK} 
                      onChange={(e) => setTopK(Number(e.target.value))} 
                      style={{ 
                        width: '100%',
                        padding: 12,
                        background: 'rgba(30, 41, 59, 0.6)', 
                        color: 'var(--text-primary)', 
                        border: '1px solid var(--border-primary)', 
                        borderRadius: 8,
                        fontSize: 14,
                        fontWeight: 600
                      }} 
                    />
                  </div>
                  <button 
                    className="send-button" 
                    onClick={handleDetectAnomalies}
                    disabled={loading}
                    style={{ 
                      padding: '12px 32px', 
                      fontSize: 14, 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: 8,
                      alignSelf: 'flex-end'
                    }}
                  >
                    {loading ? (
                      <>
                        <Loader2 size={18} className="spin" />
                        Detecting...
                      </>
                    ) : (
                      <>
                        <Zap size={18} />
                        Detect Anomalies
                      </>
                    )}
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Results Section */}
      {step === 'detect' && geojson && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Results Header */}
          <div className="glass-effect" style={{ 
            padding: 16, 
            border: '1px solid rgba(0, 255, 163, 0.3)', 
            borderRadius: 12,
            background: 'rgba(0, 255, 163, 0.05)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Zap size={20} color="var(--accent-primary)" />
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                  Detection Complete
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  {(anomalies as any[])?.length || 0} anomalies identified
                </div>
              </div>
            </div>
            <button 
              className="send-button" 
              onClick={handleReset}
              style={{ padding: '8px 16px', fontSize: 13 }}
            >
              New Analysis
            </button>
          </div>

          {/* Visualization Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
            <GeoPlot geojson={geojson} anomalies={(anomalies as any[]) || []} />
            <ShapPlot shap={useAppStore.getState().shap || []} />
          </div>
        </div>
      )}
    </div>
  );
};
