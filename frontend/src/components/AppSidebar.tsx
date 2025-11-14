import React, { useState } from 'react';
import { Mail, MessageCircle, Instagram, ShoppingCart, Plus, X } from 'lucide-react';
import './AppSidebar.css';

interface App {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  connected: boolean;
}

interface AppSidebarProps {
  onAppClick: (appId: string) => void;
  onAddApp: () => void;
}

const defaultApps: App[] = [
  {
    id: 'gmail',
    name: 'Gmail',
    icon: <Mail size={20} />,
    color: '#EA4335',
    connected: false,
  },
  {
    id: 'whatsapp',
    name: 'WhatsApp',
    icon: <MessageCircle size={20} />,
    color: '#25D366',
    connected: false,
  },
  {
    id: 'instagram',
    name: 'Instagram',
    icon: <Instagram size={20} />,
    color: '#E4405F',
    connected: false,
  },
  {
    id: 'noon',
    name: 'Noon',
    icon: <ShoppingCart size={20} />,
    color: '#FFB800',
    connected: false,
  },
];

export const AppSidebar: React.FC<AppSidebarProps> = ({ onAppClick, onAddApp }) => {
  const [apps] = useState<App[]>(defaultApps);
  const [showAddMenu, setShowAddMenu] = useState(false);
  const [customApps, setCustomApps] = useState<App[]>([]);

  const handleAddApp = () => {
    onAddApp();
    setShowAddMenu(true);
  };

  const handleAddCustomApp = (appName: string, icon: React.ReactNode, color: string) => {
    const newApp: App = {
      id: appName.toLowerCase().replace(/\s+/g, '-'),
      name: appName,
      icon,
      color,
      connected: false,
    };
    setCustomApps([...customApps, newApp]);
    setShowAddMenu(false);
  };

  const handleRemoveApp = (appId: string) => {
    setCustomApps(customApps.filter(app => app.id !== appId));
  };

  const allApps = [...apps, ...customApps];

  return (
    <div className="app-sidebar">
      <div className="app-sidebar-header">
        <h3>Apps</h3>
      </div>
      
      <div className="app-sidebar-content">
        {allApps.map((app) => (
          <div
            key={app.id}
            className={`app-icon ${app.connected ? 'connected' : ''}`}
            onClick={() => onAppClick(app.id)}
            style={{ '--app-color': app.color } as React.CSSProperties}
            title={app.name}
          >
            <div className="app-icon-wrapper">
              {app.icon}
              {customApps.some(a => a.id === app.id) && (
                <button
                  className="remove-app-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveApp(app.id);
                  }}
                  title="Remove app"
                >
                  <X size={12} />
                </button>
              )}
            </div>
            {app.connected && <div className="connection-indicator" />}
          </div>
        ))}
        
        <div className="app-icon add-app" onClick={handleAddApp} title="Add App">
          <Plus size={20} />
        </div>
      </div>

      {showAddMenu && (
        <div className="add-app-menu">
          <div className="add-app-menu-header">
            <h4>Add Custom App</h4>
            <button onClick={() => setShowAddMenu(false)}>
              <X size={16} />
            </button>
          </div>
          <div className="add-app-menu-content">
            <input
              type="text"
              placeholder="App name"
              id="custom-app-name"
              className="custom-app-input"
            />
            <input
              type="color"
              id="custom-app-color"
              defaultValue="#6366f1"
              className="custom-app-color"
            />
            <button
              onClick={() => {
                const nameInput = document.getElementById('custom-app-name') as HTMLInputElement;
                const colorInput = document.getElementById('custom-app-color') as HTMLInputElement;
                if (nameInput?.value) {
                  handleAddCustomApp(
                    nameInput.value,
                    <div className="custom-app-icon">{nameInput.value[0].toUpperCase()}</div>,
                    colorInput?.value || '#6366f1'
                  );
                  nameInput.value = '';
                }
              }}
              className="add-app-submit-btn"
            >
              Add App
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

