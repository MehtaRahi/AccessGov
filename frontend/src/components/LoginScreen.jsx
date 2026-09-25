import React, { useState } from 'react';

const LoginScreen = ({ onLogin, onGuest, BACKEND_URL }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleAuth = async (e) => {
    e.preventDefault();
    setIsLoading(true);
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
        alert("Authentication failed. Please check your credentials.");
      }
    } catch (error) {
      alert("Cannot connect to the server.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <div className="login-card">
        <h1>Access<span>Gov</span></h1>
        <p style={{ color: 'var(--text-muted)', marginBottom: '32px', fontSize: '15px' }}>
          Navigate government services with AI
        </p>

        <form className="auth-form" onSubmit={handleAuth}>
          {isRegister && (
            <input 
              className="input-field" 
              placeholder="Full Name" 
              value={name} 
              onChange={e => setName(e.target.value)} 
              required 
            />
          )}
          <input 
            className="input-field" 
            type="email" 
            placeholder="Email Address" 
            value={email} 
            onChange={e => setEmail(e.target.value)} 
            required 
          />
          <input 
            className="input-field" 
            type="password" 
            placeholder="Password" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
            required 
          />
          
          <button 
            className="btn-primary" 
            type="submit" 
            style={{ marginTop: '8px', width: '100%', padding: '14px' }}
            disabled={isLoading}
          >
            {isLoading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '20px', width: '100%' }}>
          <button className="btn-outline" style={{ width: '100%' }} type="button" onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
          </button>
          
          <div className="divider-text">or</div>
          
          <button className="btn-outline" style={{ width: '100%' }} type="button" onClick={onGuest}>
            Continue as Guest
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
