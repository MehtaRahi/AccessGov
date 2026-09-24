import React from 'react';
import { PlusCircle, LogOut, Settings, ShieldAlert } from 'lucide-react';

const Sidebar = ({ 
  user, 
  chats, 
  onLogout, 
  onNewChat, 
  onLoadChat, 
  onOpenSettings, 
  onOpenAdmin, 
  onGuestExit 
}) => {
  return (
    <div className="sidebar">
      <h1>AccessGov</h1>
      <p>AI Government Assistant</p>

      {!user ? (
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <p style={{ fontSize: '14px', marginBottom: '10px', color: 'var(--text-muted)' }}>Browsing as Guest</p>
          <button className="btn-outline" style={{ width: '100%' }} onClick={onGuestExit}>Sign In to Save Chats</button>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <span style={{ fontWeight: 'bold' }}>{user.name}</span>
            <button onClick={onLogout} className="btn-outline" style={{ padding: '6px' }} title="Logout">
              <LogOut size={16}/>
            </button>
          </div>
          <button className="btn-primary" onClick={onNewChat} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <PlusCircle size={18} /> New Chat
          </button>

          <div className="chat-history">
            {chats.map(c => (
              <button key={c.id} className="chat-session-btn" onClick={() => onLoadChat(c.id)}>
                {c.title}
              </button>
            ))}
          </div>
        </>
      )}

      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', alignItems: 'center' }}>
        <button 
          className="btn-outline" 
          style={{ width: '100%', display: 'flex', gap: '10px', alignItems: 'center', justifyContent: 'center', borderColor: '#ffaa00', color: '#ffaa00' }} 
          onClick={onOpenAdmin}
        >
          <ShieldAlert size={18} /> Admin Panel
        </button>
        <button 
          className="btn-outline" 
          style={{ width: '100%', display: 'flex', gap: '10px', alignItems: 'center', justifyContent: 'center' }} 
          onClick={onOpenSettings}
        >
          <Settings size={18} /> Settings
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
