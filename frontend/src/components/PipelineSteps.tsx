import React from 'react';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';

interface Step {
  name: string;
  label: string;
  status: 'pending' | 'started' | 'completed' | 'failed';
  message?: string;
}

interface PipelineStepsProps {
  steps: Step[];
}

export const PipelineSteps: React.FC<PipelineStepsProps> = ({ steps }) => {
  if (steps.length === 0) return null;

  return (
    <div className="glass-effect" style={{ 
      border: '1px solid var(--border-primary)', 
      borderRadius: 12, 
      padding: 16, 
      marginTop: 16,
      background: 'rgba(15, 23, 42, 0.4)'
    }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Processing Pipeline
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {steps.map((step, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {step.status === 'completed' && <CheckCircle2 size={20} color="var(--accent-primary)" />}
              {step.status === 'started' && <Loader2 size={20} color="var(--accent-secondary)" className="spin" />}
              {step.status === 'failed' && <XCircle size={20} color="var(--error)" />}
              {step.status === 'pending' && <Circle size={20} color="var(--text-tertiary)" />}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, color: step.status === 'completed' ? 'var(--text-primary)' : step.status === 'failed' ? 'var(--error)' : 'var(--text-secondary)', fontWeight: 500 }}>
                {step.label}
              </div>
              {step.message && (
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
                  {step.message}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

