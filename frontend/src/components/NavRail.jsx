import React from 'react';
import { MessageSquare, Clock, ShieldAlert, Settings, LogOut, User } from 'lucide-react';

const NavRail = ({ 
  user, 
  activeView,
  onToggleHistory, 
  onOpenSettings, 
  onOpenAdmin, 
  onLogout,
  onGuestExit,
  isHistoryOpen 
}) => {
  return (
    <nav className="nav-rail" aria-label="Main navigation">
      {/* Logo */}
      <div className="nav-rail__logo" title="AccessGov">A</div>

      {/* Primary nav */}
      <div className="nav-rail__group">
        <button 
          className={`nav-rail__btn ${activeView === 'chat' && !isHistoryOpen ? 'nav-rail__btn--active' : ''}`}
          data-tooltip="Chat"
          onClick={() => isHistoryOpen && onToggleHistory()}
          aria-label="Chat"
        >
          <MessageSquare size={22} />
        </button>

        {user && (
          <button 
            className={`nav-rail__btn ${isHistoryOpen ? 'nav-rail__btn--active' : ''}`}
            data-tooltip="Chat History"
            onClick={onToggleHistory}
            aria-label="Chat History"
          >
            <Clock size={22} />
          </button>
        )}
      </div>

      <div className="nav-rail__spacer" />

      {/* Secondary nav */}
      <div className="nav-rail__group">
        <button 
          className="nav-rail__btn"
          data-tooltip="Admin Panel"
          onClick={onOpenAdmin}
          aria-label="Admin Panel"
        >
          <ShieldAlert size={22} />
        </button>

        <button 
          className="nav-rail__btn"
          data-tooltip="Settings"
          onClick={onOpenSettings}
          aria-label="Settings"
        >
          <Settings size={22} />
        </button>

        {user ? (
          <button 
            className="nav-rail__btn nav-rail__btn--danger"
            data-tooltip="Logout"
            onClick={onLogout}
            aria-label="Logout"
          >
            <LogOut size={20} />
          </button>
        ) : (
          <button 
            className="nav-rail__btn"
            data-tooltip="Sign In"
            onClick={onGuestExit}
            aria-label="Sign In"
          >
            <LogOut size={20} />
          </button>
        )}
      </div>

      {/* Avatar */}
      <div className="nav-rail__avatar" title={user ? user.name : 'Guest'}>
        {user ? user.name.charAt(0).toUpperCase() : <User size={16} />}
      </div>
    </nav>
  );
};

export default NavRail;
