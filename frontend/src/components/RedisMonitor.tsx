import React, { useEffect, useState, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Activity, X } from 'lucide-react';

export const RedisMonitor: React.FC = () => {
  const { sessionId } = useAppStore();
  const [events, setEvents] = useState<any[]>([]);
  const [active, setActive] = useState(0);
  const idleTimer = useRef<number | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(true);
  const [position, setPosition] = useState({ x: 24, y: 24 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const monitorRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!sessionId) return;
    const es = new EventSource(`/api/events/${sessionId}`);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setEvents((prev) => [data, ...prev].slice(0, 50));
        if (data.type === 'agent_started' || data.type === 'team_started') setActive((a) => a + 1);
        if (['agent_completed','team_completed','query_completed'].includes(data.type)) setActive((a) => Math.max(0, a - 1));
      } catch {}
    };
    es.onerror = () => es.close();
    return () => es.close();
  }, [sessionId]);

  // Auto-clear when idle for 8s and no active ops
  useEffect(() => {
    if (idleTimer.current) window.clearTimeout(idleTimer.current);
    idleTimer.current = window.setTimeout(() => {
      if (active <= 0) setEvents([]);
    }, 8000) as unknown as number;
    return () => {
      if (idleTimer.current) window.clearTimeout(idleTimer.current);
    };
  }, [events, active]);

  const handleMouseDown = (e: React.MouseEvent, ref: React.RefObject<HTMLElement>) => {
    if (isOpen && !isMinimized) return; // Don't drag when panel is expanded
    setIsDragging(true);
    const rect = ref.current?.getBoundingClientRect();
    if (rect) {
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      
      const newX = window.innerWidth - e.clientX - dragOffset.x;
      const newY = window.innerHeight - e.clientY - dragOffset.y;
      
      // Constrain to viewport
      const constrainedX = Math.max(24, Math.min(newX, window.innerWidth - 72));
      const constrainedY = Math.max(24, Math.min(newY, window.innerHeight - 72));
      
      setPosition({ x: constrainedX, y: constrainedY });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  if (!isOpen) {
    return (
      <button
        ref={buttonRef}
        onMouseDown={(e) => handleMouseDown(e, buttonRef)}
        onClick={() => !isDragging && setIsOpen(true)}
        className="redis-monitor-trigger"
        style={{
          position: 'fixed',
          bottom: position.y,
          right: position.x,
          width: 48,
          height: 48,
          borderRadius: 24,
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: isDragging ? 'grabbing' : 'grab',
          transition: isDragging ? 'none' : 'all 0.2s',
          boxShadow: 'var(--shadow-md)',
          zIndex: 1000,
          userSelect: 'none',
        }}
        onMouseEnter={(e) => {
          if (!isDragging) {
            e.currentTarget.style.transform = 'scale(1.1)';
            e.currentTarget.style.borderColor = 'var(--accent-primary)';
          }
        }}
        onMouseLeave={(e) => {
          if (!isDragging) {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.borderColor = 'var(--border-primary)';
          }
        }}
      >
        <Activity size={20} color="var(--accent-primary)" />
      </button>
    );
  }

  return (
    <div
      ref={monitorRef}
      onMouseDown={isMinimized ? (e) => handleMouseDown(e, monitorRef) : undefined}
      className="redis-monitor glass-effect"
      style={{
        position: 'fixed',
        bottom: position.y,
        right: position.x,
        width: isMinimized ? 320 : 480,
        maxHeight: isMinimized ? 60 : 400,
        background: 'rgba(17, 21, 46, 0.95)',
        backdropFilter: 'blur(12px)',
        border: '1px solid var(--border-primary)',
        borderRadius: 12,
        boxShadow: 'var(--shadow-lg)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 1000,
        transition: isDragging ? 'none' : 'all 0.3s ease',
        cursor: isMinimized && !isDragging ? 'grab' : isMinimized && isDragging ? 'grabbing' : 'default',
        userSelect: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          borderBottom: isMinimized ? 'none' : '1px solid var(--border-primary)',
          cursor: 'pointer',
        }}
        onClick={() => setIsMinimized(!isMinimized)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Activity size={16} color="var(--accent-primary)" />
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
            Redis Bus
          </span>
          <span
            style={{
              fontSize: 11,
              padding: '2px 8px',
              background: 'var(--accent-primary)',
              color: 'var(--bg-primary)',
              borderRadius: 10,
              fontWeight: 600,
            }}
          >
            {events.length}
          </span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsOpen(false);
          }}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            padding: 4,
          }}
        >
          <X size={16} color="var(--text-tertiary)" />
        </button>
      </div>

      {!isMinimized && (
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '8px 0',
          }}
        >
          {events.length === 0 ? (
            <div
              style={{
                padding: '32px 16px',
                textAlign: 'center',
                color: 'var(--text-tertiary)',
                fontSize: 12,
              }}
            >
              No events yet
            </div>
          ) : (
            events.map((event, idx) => (
              <div
                key={idx}
                style={{
                  padding: '8px 16px',
                  borderBottom:
                    idx < events.length - 1 ? '1px solid var(--border-primary)' : 'none',
                  fontSize: 11,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: event.type === 'agent_started' ? 'var(--accent-primary)' : event.type === 'agent_completed' ? 'var(--accent-secondary)' : 'var(--accent-silver)',
                    flexShrink: 0,
                  }}
                />
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <code
                      style={{
                        fontSize: 10,
                        padding: '2px 6px',
                        background: 'var(--bg-tertiary)',
                        borderRadius: 4,
                        color: 'var(--accent-primary)',
                      }}
                    >
                      {event.type}
                    </code>
                    {event.agent && (
                      <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>
                        {event.agent}
                      </span>
                    )}
                  </div>
                  {event.module && (
                    <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>
                      module: {event.module}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
