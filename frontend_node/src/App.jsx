import { useState, useEffect, useRef } from 'react'
import { Mic, Send, Volume2, PlusCircle, LogOut, Settings, X } from 'lucide-react'

// Same fallback logic as Streamlit
const BACKEND_URL = "http://localhost:8001"; // When running via Vite Dev Server. In production/Docker it's exposed on 8001 on the host for browser access. Wait, the browser hits the backend directly!
// Yes, the browser is on the host machine, so it must hit localhost:8001 (which maps to backend:8000).

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [name, setName] = useState('')
  const [isGuest, setIsGuest] = useState(false) // Track if user skipped login

  const [chats, setChats] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AccessGov assistant. How can I help you today?' }
  ])
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)

  // Accessibility States
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [isDyslexiaFont, setIsDyslexiaFont] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [textSize, setTextSize] = useState('normal') // normal, large, xlarge
  const [highContrast, setHighContrast] = useState(false)
  const [colorblindMode, setColorblindMode] = useState('none')
  const [readingMask, setReadingMask] = useState(false)
  const [reducedMotion, setReducedMotion] = useState(false)
  const [textOnlyMode, setTextOnlyMode] = useState(false)
  const [simpleLanguage, setSimpleLanguage] = useState(false)
  
  const [mouseY, setMouseY] = useState(0)

  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (isDarkMode) document.body.classList.remove('light-mode')
    else document.body.classList.add('light-mode')

    if (isDyslexiaFont) document.body.classList.add('dyslexia-font')
    else document.body.classList.remove('dyslexia-font')

    if (highContrast) document.body.classList.add('high-contrast')
    else document.body.classList.remove('high-contrast')

    const htmlClasses = document.documentElement.classList
    htmlClasses.remove('text-large', 'text-xlarge')
    if (textSize === 'large') htmlClasses.add('text-large')
    if (textSize === 'xlarge') htmlClasses.add('text-xlarge')
    
    if (reducedMotion) document.body.classList.add('reduced-motion')
    else document.body.classList.remove('reduced-motion')

    if (textOnlyMode) document.body.classList.add('text-only-mode')
    else document.body.classList.remove('text-only-mode')

    document.body.classList.remove('cb-protanopia', 'cb-deuteranopia', 'cb-tritanopia')
    if (colorblindMode !== 'none') document.body.classList.add(`cb-${colorblindMode}`)
  }, [isDarkMode, isDyslexiaFont, highContrast, textSize, reducedMotion, textOnlyMode, colorblindMode])

  useEffect(() => {
    if (!readingMask) return
    const handleMouseMove = (e) => setMouseY(e.clientY)
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [readingMask])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (user && token) {
      fetchChats()
      // Ideally fetch prefs from /api/users/{user_id} here
    }
  }, [user, token])

  const fetchChats = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/chats/${user.user_id}`)
      const data = await res.json()
      setChats(data)
    } catch (e) {
      console.error(e)
    }
  }

  const loadChat = async (id) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/chats/${user.user_id}/session/${id}`)
      const data = await res.json()
      setSessionId(id)
      setMessages(data.messages.length ? data.messages : messages)
    } catch (e) {
      console.error(e)
    }
  }

  const handleAuth = async (e) => {
    e.preventDefault()
    const url = `${BACKEND_URL}/api/auth/${isRegister ? 'register' : 'login'}`
    const payload = isRegister ? { email, password, name } : { email, password }
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (res.ok) {
        const data = await res.json()
        setToken(data.access_token)
        setUser({ user_id: data.user_id, name: data.name })
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify({ user_id: data.user_id, name: data.name }))
      } else {
        alert("Authentication failed")
      }
    } catch (error) {
      alert("Network error")
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    setSessionId(null)
    setMessages([{ role: 'assistant', content: 'Hello! I am your AccessGov assistant. How can I help you today?' }])
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const newChat = () => {
    setSessionId(null)
    setMessages([{ role: 'assistant', content: 'Hello! I am your AccessGov assistant. How can I help you today?' }])
  }

  const sendMessage = async (textOverride = null) => {
    const text = textOverride || input
    if (!text.trim()) return

    const newMsgs = [...messages, { role: 'user', content: text }]
    setMessages(newMsgs)
    setInput('')

    // history logic - get last 4
    const history = newMsgs.length > 2 ? newMsgs.slice(1, -1).slice(-4) : []

    let queryText = text
    if (simpleLanguage) {
      queryText += " (IMPORTANT: Please explain this as simply as possible, avoiding bureaucratic jargon, as if I am 5 years old.)"
    }

    const payload = {
      query: queryText,
      mode: 'normal',
      chat_history: history,
      user_id: user?.user_id || null,
      session_id: sessionId
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      setMessages([...newMsgs, { role: 'assistant', content: data.answer }])
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
        if (user) fetchChats()
      }
    } catch (e) {
      setMessages([...newMsgs, { role: 'assistant', content: 'Connection Error.' }])
    }
  }

  // Web Speech API for TTS
  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text)
    window.speechSynthesis.cancel() // cancel current
    window.speechSynthesis.speak(utterance)
  }

  // Web Speech API for STT
  const toggleRecording = () => {
    if (isRecording) return // Can't manually stop native easily without ref
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser.")
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = () => setIsRecording(true)
    recognition.onend = () => setIsRecording(false)
    recognition.onerror = () => setIsRecording(false)

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      sendMessage(transcript) // auto send
    }

    recognition.start()
  }

  // --- FULL PAGE LOGIN SCREEN ---
  if (!user && !isGuest) {
    return (
      <div className="login-screen">
        <div className="login-card glass-panel">
          <h1 style={{ color: 'var(--accent)', marginBottom: '10px' }}>AccessGov</h1>
          <p style={{ color: 'var(--text-muted)', marginBottom: '30px' }}>Your AI Government Assistant</p>

          <form className="auth-form" onSubmit={handleAuth} style={{ width: '100%' }}>
            {isRegister && <input className="input-field" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)} required />}
            <input className="input-field" type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} required />
            <input className="input-field" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
            
            <button className="btn-primary" type="submit" style={{ marginTop: '10px' }}>
              {isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '20px', width: '100%' }}>
            <button className="btn-outline" type="button" onClick={() => setIsRegister(!isRegister)}>
              {isRegister ? 'Already have an account? Sign In' : 'Need an account? Register'}
            </button>
            <div className="divider-text"><span>or</span></div>
            <button className="btn-outline" type="button" onClick={() => setIsGuest(true)}>
              Continue as Guest
            </button>
          </div>
        </div>
      </div>
    )
  }

  // --- MAIN APP (Authenticated or Guest) ---
  return (
    <div className="app-container">
      {readingMask && (
        <div 
          className="reading-mask"
          style={{
            background: `radial-gradient(circle 800px at 50% ${mouseY}px, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.8) 15%)`
          }}
        />
      )}
      
      {/* SIDEBAR */}
      <div className="sidebar">
        <h1>AccessGov</h1>
        <p>AI Government Assistant</p>

        {!user ? (
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <p style={{ fontSize: '14px', marginBottom: '10px', color: 'var(--text-muted)' }}>Browsing as Guest</p>
            <button className="btn-outline" style={{ width: '100%' }} onClick={() => setIsGuest(false)}>Sign In to Save Chats</button>
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <span style={{ fontWeight: 'bold' }}>{user.name}</span>
              <button onClick={logout} className="btn-outline" style={{ padding: '5px' }} title="Logout">
                <LogOut size={16}/>
              </button>
            </div>
            <button className="btn-primary" onClick={newChat} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
              <PlusCircle size={18} /> New Chat
            </button>

            <div className="chat-history">
              {chats.map(c => (
                <button key={c.id} className="chat-session-btn" onClick={() => loadChat(c.id)}>
                  {c.title}
                </button>
              ))}
            </div>
          </>
        )}

        <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'center' }}>
          <button className="btn-outline" style={{ width: '100%', display: 'flex', gap: '10px', alignItems: 'center', justifyContent: 'center' }} onClick={() => setIsSettingsOpen(true)}>
            <Settings size={18} /> Settings & Accessibility
          </button>
        </div>
      </div>

      {isSettingsOpen && (
        <div className="modal-overlay" onClick={() => setIsSettingsOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Settings</h2>
              <button className="close-btn" aria-label="Close settings" onClick={() => setIsSettingsOpen(false)}><X size={24}/></button>
            </div>
            
            <div className="settings">
              <div className="toggle-row">
                <span>Translate App</span>
                <div id="google_translate_element"></div>
              </div>
              <div className="toggle-row">
                <span>Text Size</span>
                <select className="select-field" value={textSize} onChange={e => setTextSize(e.target.value)} aria-label="Select text size">
                  <option value="normal">Normal</option>
                  <option value="large">Large</option>
                  <option value="xlarge">Extra Large</option>
                </select>
              </div>
              <div className="toggle-row">
                <span>Colorblind Filter</span>
                <select className="select-field" value={colorblindMode} onChange={e => setColorblindMode(e.target.value)} aria-label="Select colorblind filter">
                  <option value="none">None</option>
                  <option value="protanopia">Protanopia (Red)</option>
                  <option value="deuteranopia">Deuteranopia (Green)</option>
                  <option value="tritanopia">Tritanopia (Blue)</option>
                </select>
              </div>
              <div className="toggle-row">
                <span>Always Use Simple Language</span>
                <input type="checkbox" checked={simpleLanguage} onChange={e => setSimpleLanguage(e.target.checked)} aria-label="Toggle simple language" />
              </div>
              <div className="toggle-row">
                <span>Reading Mask / Focus Ruler</span>
                <input type="checkbox" checked={readingMask} onChange={e => setReadingMask(e.target.checked)} aria-label="Toggle reading mask" />
              </div>
              <div className="toggle-row">
                <span>Reduced Motion</span>
                <input type="checkbox" checked={reducedMotion} onChange={e => setReducedMotion(e.target.checked)} aria-label="Toggle reduced motion" />
              </div>
              <div className="toggle-row">
                <span>Text-Only (Screen Reader)</span>
                <input type="checkbox" checked={textOnlyMode} onChange={e => setTextOnlyMode(e.target.checked)} aria-label="Toggle text only mode" />
              </div>
              <div className="toggle-row">
                <span>High Contrast Mode</span>
                <input type="checkbox" checked={highContrast} onChange={e => setHighContrast(e.target.checked)} aria-label="Toggle high contrast" />
              </div>
              <div className="toggle-row">
                <span>Dark Mode</span>
                <input type="checkbox" checked={isDarkMode} onChange={e => setIsDarkMode(e.target.checked)} aria-label="Toggle dark mode" />
              </div>
              <div className="toggle-row">
                <span>Dyslexia Font</span>
                <input type="checkbox" checked={isDyslexiaFont} onChange={e => setIsDyslexiaFont(e.target.checked)} aria-label="Toggle dyslexia font" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CHAT AREA */}
      <div className="chat-area">
        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`}>
              {/* Note: In a real app we'd use react-markdown here instead of raw text, but raw text works for prototype */}
              <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
              {m.role === 'assistant' && (
                <button className="tts-btn" onClick={() => speak(m.content)}>
                  <Volume2 size={14} /> Play Audio
                </button>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input 
            className="chat-input" 
            placeholder="Type your question..." 
            value={input} 
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
          />
          <button className={`mic-btn ${isRecording ? 'recording' : ''}`} onClick={toggleRecording} aria-label={isRecording ? "Stop voice input" : "Start voice input"}>
            <Mic size={20} />
          </button>
          <button className="send-btn" onClick={() => sendMessage()} aria-label="Send message">
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
