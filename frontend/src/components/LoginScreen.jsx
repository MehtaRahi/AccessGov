import React, { useState } from 'react';

const LoginScreen = ({ onLogin, onGuest, BACKEND_URL }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');

  const handleAuth = async (e) => {
    e.preventDefault();
    const url = `${BACKEND_URL}/api/auth/${isRegister ? 'register' : 'login'}`;
    const payload = isRegister ? { email, password, name } : { email, password };
    
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        onLogin(data);
      } else {
        alert("Authentication failed. Check your credentials.");
      }
    } catch (error) {
      alert("Network error connecting to backend.");
    }
  };

  return (
    <div className="login-screen">
      <div className="login-card glass-panel">
        <h1 style={{ color: 'var(--accent)', marginBottom: '8px', fontSize: '36px' }}>AccessGov</h1>
        <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>Your AI Government Assistant</p>

        <form className="auth-form" onSubmit={handleAuth} style={{ width: '100%' }}>
          {isRegister && <input className="input-field" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)} required />}
          <input className="input-field" type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} required />
          <input className="input-field" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
          
          <button className="btn-primary" type="submit" style={{ marginTop: '12px' }}>
            {isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '24px', width: '100%' }}>
          <button className="btn-outline" type="button" onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? 'Already have an account? Sign In' : 'Need an account? Register'}
          </button>
          <div className="divider-text"><span>or</span></div>
          <button className="btn-outline" type="button" onClick={onGuest}>
            Continue as Guest
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
