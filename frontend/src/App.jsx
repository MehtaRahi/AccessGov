import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import AdminDashboard from './components/AdminDashboard'
import LoginScreen from './components/LoginScreen'
import NavRail from './components/NavRail'
import HistoryPanel from './components/HistoryPanel'
import ChatArea from './components/ChatArea'

const BACKEND_URL = "http://localhost:8001";

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null)
  const [isGuest, setIsGuest] = useState(false)

  const [chats, setChats] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AccessGov assistant. How can I help you today?' }
  ])
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)

  // UI States
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isAdminOpen, setIsAdminOpen] = useState(false)

  // Accessibility States
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [isDyslexiaFont, setIsDyslexiaFont] = useState(false)
  const [textSize, setTextSize] = useState('normal')
  const [highContrast, setHighContrast] = useState(false)
  const [colorblindMode, setColorblindMode] = useState('none')
  const [readingMask, setReadingMask] = useState(false)
  const [reducedMotion, setReducedMotion] = useState(false)
  const [textOnlyMode, setTextOnlyMode] = useState(false)
  const [simpleLanguage, setSimpleLanguage] = useState(false)
  const [mouseY, setMouseY] = useState(0)

  // Accessibility class management
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
    if (user && token) fetchChats()
  }, [user, token])

  // API calls
  const fetchChats = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/chats/${user.user_id}`)
      const data = await res.json()
      setChats(data)
    } catch (e) { console.error(e) }
  }

  const loadChat = async (id) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/chats/${user.user_id}/session/${id}`)
      const data = await res.json()
      setSessionId(id)
      setMessages(data.messages.length ? data.messages : messages)
      setIsHistoryOpen(false)
    } catch (e) { console.error(e) }
  }

  const handleLogin = (data) => {
    setToken(data.access_token)
    setUser({ user_id: data.user_id, name: data.name })
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify({ user_id: data.user_id, name: data.name }))
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    setSessionId(null)
    setIsHistoryOpen(false)
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
      setMessages([...newMsgs, { role: 'assistant', content: 'Connection error. Please check that the backend is running.' }])
    }
  }

  // TTS
  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text)
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
  }

  // STT
  let recognition = null
  const toggleRecording = () => {
    if (isRecording) return
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser.")
      return
    }
    recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onstart = () => setIsRecording(true)
    recognition.onend = () => setIsRecording(false)
    recognition.onerror = () => setIsRecording(false)
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      sendMessage(transcript)
    }
    recognition.start()
  }

  const stopRecording = () => {
    if (recognition) recognition.stop()
    setIsRecording(false)
  }

  // === Login Gate ===
  if (!user && !isGuest) {
    return <LoginScreen onLogin={handleLogin} onGuest={() => setIsGuest(true)} BACKEND_URL={BACKEND_URL} />
  }

  // === Main App ===
  return (
    <div className="app-layout">
      {readingMask && (
        <div
          className="reading-mask"
          style={{ background: `radial-gradient(circle 800px at 50% ${mouseY}px, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.8) 15%)` }}
        />
      )}

      <NavRail
        user={user}
        activeView="chat"
        isHistoryOpen={isHistoryOpen}
        onToggleHistory={() => setIsHistoryOpen(!isHistoryOpen)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenAdmin={() => setIsAdminOpen(true)}
        onLogout={logout}
        onGuestExit={() => setIsGuest(false)}
      />

      {isHistoryOpen && (
        <HistoryPanel
          chats={chats}
          onLoadChat={loadChat}
          onNewChat={() => { newChat(); setIsHistoryOpen(false); }}
          onClose={() => setIsHistoryOpen(false)}
        />
      )}

      {isAdminOpen && <AdminDashboard onClose={() => setIsAdminOpen(false)} />}

      {isSettingsOpen && (
        <div className="modal-overlay" onClick={() => setIsSettingsOpen(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal__header">
              <h2>Settings</h2>
              <button className="modal__close" aria-label="Close settings" onClick={() => setIsSettingsOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="settings-list">
              <div className="settings-row">
                <span>Translate App</span>
                <div id="google_translate_element"></div>
              </div>
              <div className="settings-row">
                <span>Text Size</span>
                <select className="select-field" value={textSize} onChange={e => setTextSize(e.target.value)} aria-label="Select text size">
                  <option value="normal">Normal</option>
                  <option value="large">Large</option>
                  <option value="xlarge">Extra Large</option>
                </select>
              </div>
              <div className="settings-row">
                <span>Colorblind Filter</span>
                <select className="select-field" value={colorblindMode} onChange={e => setColorblindMode(e.target.value)} aria-label="Select colorblind filter">
                  <option value="none">None</option>
                  <option value="protanopia">Protanopia (Red)</option>
                  <option value="deuteranopia">Deuteranopia (Green)</option>
                  <option value="tritanopia">Tritanopia (Blue)</option>
                </select>
              </div>
              <div className="settings-row">
                <span>Simple Language</span>
                <label className="toggle">
                  <input type="checkbox" checked={simpleLanguage} onChange={e => setSimpleLanguage(e.target.checked)} />
                  <span className="toggle__track"></span>
                  <span className="toggle__thumb"></span>
                </label>
              </div>
              <div className="settings-row">
                <span>Reading Mask</span>
                <label className="toggle">
                  <input type="checkbox" checked={readingMask} onChange={e => setReadingMask(e.target.checked)} />
                  <span className="toggle__track"></span>
                  <span className="toggle__thumb"></span>
                </label>
              </div>
              <div className="settings-row">
                <span>Reduced Motion</span>
                <label className="toggle">
                  <input type="checkbox" checked={reducedMotion} onChange={e => setReducedMotion(e.target.checked)} />
                  <span className="toggle__track"></span>
                  <span className="toggle__thumb"></span>
                </label>
              </div>
              <div className="settings-row">
                <span>Text-Only Mode</span>
                <label className="toggle">
                  <input type="checkbox" checked={textOnlyMode} onChange={e => setTextOnlyMode(e.target.checked)} />
                  <span className="toggle__track"></span>
                  <span className="toggle__thumb"></span>
                </label>
              </div>
              <div className="settings-row">
                <span>High Contrast</span>
                <label className="toggle">
                  <input type="checkbox" checked={highContrast} onChange={e => setHighContrast(e.target.checked)} />
                  <span className="toggle__track"></span>
                  <span className="toggle__thumb"></span>
                </label>
              </div>
              <div className="settings-row">
                <span>Dark Mode</span>
                <label className="toggle">
                  <input type="checkbox" checked={isDarkMode} onChange={e => setIsDarkMode(e.target.checked)} />
                  <span className="toggle__track"></span>
                  <span className="toggle__thumb"></span>
                </label>
              </div>
              <div className="settings-row">
                <span>Dyslexia Font</span>
                <label className="toggle">
                  <input type="checkbox" checked={isDyslexiaFont} onChange={e => setIsDyslexiaFont(e.target.checked)} />
                  <span className="toggle__track"></span>
                  <span className="toggle__thumb"></span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}

      <ChatArea
        messages={messages}
        input={input}
        setInput={setInput}
        isRecording={isRecording}
        handleSendMessage={() => sendMessage()}
        handleStartRecording={toggleRecording}
        handleStopRecording={stopRecording}
        handlePlayTTS={speak}
        onSuggestionClick={(query) => sendMessage(query)}
      />
    </div>
  )
}

export default App
