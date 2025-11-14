import React, { useRef, useEffect } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { useAppStore } from '../store/useAppStore';
import { Sparkles } from 'lucide-react';

interface ChatPanelProps {
  onSendMessage: (message: string) => void;
  onApproval: (action: string, data: any) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ onSendMessage, onApproval }) => {
  const { messages, isLoading } = useAppStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="empty-icon">
              <Sparkles size={48} />
            </div>
            <h2>Welcome to Neuroverse</h2>
            <p>Ask anything across domains or explore GIS analytics with anomaly detection.</p>
            <div className="example-queries">
              <button
                onClick={() => onSendMessage('Find abnormal traffic heat-zones in Dubai last week')}
                className="example-query"
              >
                Find abnormal traffic in Dubai
              </button>
              <button
                onClick={() => onSendMessage('Analyze data trends and provide insights')}
                className="example-query"
              >
                Analyze data trends
              </button>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} onApproval={onApproval} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <ChatInput onSend={onSendMessage} disabled={isLoading} />
    </div>
  );
};

