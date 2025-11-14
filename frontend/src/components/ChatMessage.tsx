import React from 'react';
import { User, Cpu, Bot, CheckCircle, Edit, XCircle } from 'lucide-react';
import { GeoPlot } from './GeoPlot';
import { PipelineSteps } from './PipelineSteps';
import { useAppStore } from '../store/useAppStore';
import type { Message } from '../types';

interface ChatMessageProps {
  message: Message;
  onApproval?: (action: string, data: any) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onApproval }) => {
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

  // Check for special response types
  let approvalData: any = null;
  let displayContent = message.content;
  
  try {
    const contentData = JSON.parse(message.content);
    
    // Check for approval workflow (draft mode)
    if (contentData.status === 'requires_approval') {
      approvalData = contentData;
    }
    // Check for link generation (direct send mode)
    else if (contentData.status === 'link_generated') {
      // Create user-friendly message
      const channel = contentData.whatsapp_url ? 'WhatsApp' : 
                     contentData.mailto_link ? 'Gmail' : 
                     contentData.instagram_url ? 'Instagram' : 'app';
      
      const recipient = contentData.to_name || contentData.phone_number || contentData.to || contentData.instagram_handle || 'contact';
      
      displayContent = `✓ Opening ${channel} to message ${recipient}...`;
      
      // Auto-open the link
      setTimeout(() => {
        const url = contentData.whatsapp_url || contentData.mailto_link || contentData.instagram_url;
        if (url) {
          window.open(url, '_blank');
        }
      }, 100);
    }
  } catch {}

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-icon">
        {isUser ? <User size={16} /> : <Cpu size={16} />}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span>{isUser ? 'You' : 'Neuroverse'}</span>
          <span className="message-timestamp">{new Date(message.timestamp).toLocaleTimeString()}</span>
        </div>
        
        {approvalData ? (
          <div className="approval-content">
            <div className="approval-header">
              <Bot size={16} /> <span>Action Required</span>
            </div>
            <p><strong>Action:</strong> {approvalData.action.replace(/_/g, ' ')}</p>
            {approvalData.to_name && <p><strong>To:</strong> {approvalData.to_name}</p>}
            {approvalData.phone_number && <p><strong>Phone:</strong> {approvalData.phone_number}</p>}
            {approvalData.to && <p><strong>Email:</strong> {approvalData.to}</p>}
            {approvalData.instagram_handle && <p><strong>Instagram:</strong> {approvalData.instagram_handle}</p>}
            {approvalData.subject && <p><strong>Subject:</strong> {approvalData.subject}</p>}
            {approvalData.message && <p className="approval-message-body">"{approvalData.message}"</p>}
            {approvalData.body && <p className="approval-message-body">"{approvalData.body}"</p>}
            
            <div className="approval-buttons">
              <button className="approve-btn" onClick={() => onApproval?.(approvalData.action, approvalData)}>
                <CheckCircle size={16} /> Approve & Send
              </button>
              <button className="edit-btn">
                <Edit size={16} /> Edit
              </button>
              <button className="cancel-btn">
                <XCircle size={16} /> Cancel
              </button>
            </div>
          </div>
        ) : (
          <div dangerouslySetInnerHTML={{ __html: displayContent }} />
        )}

        {/* Display pipeline steps if they exist for this message */}
        {steps.length > 0 && <PipelineSteps steps={steps} />}
        
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

