import React from 'react';
import { PlusCircle, X } from 'lucide-react';

const HistoryPanel = ({ chats, onLoadChat, onNewChat, onClose }) => {
  return (
    <div className="history-panel">
      <div className="history-panel__header">
        <span className="history-panel__title">Chat History</span>
        <button className="history-panel__close" onClick={onClose} aria-label="Close history">
          <X size={18} />
        </button>
      </div>

      <button className="history-panel__new-btn" onClick={onNewChat}>
        <PlusCircle size={16} /> New Chat
      </button>

      <div className="history-panel__list">
        {chats.length === 0 ? (
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
            No conversations yet
          </p>
        ) : (
          chats.map(c => (
            <button 
              key={c.id} 
              className="history-panel__item" 
              onClick={() => onLoadChat(c.id)}
            >
              {c.title}
            </button>
          ))
        )}
      </div>
    </div>
  );
};

export default HistoryPanel;
