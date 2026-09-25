import React, { useRef, useEffect } from 'react';
import { Mic, Send, Volume2, FileText, GraduationCap, Receipt, ShieldCheck } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const SUGGESTIONS = [
  { icon: FileText, text: "How do I apply for a new passport?", query: "How do I apply for a new passport in India?" },
  { icon: ShieldCheck, text: "What pension schemes am I eligible for?", query: "What pension schemes are available for senior citizens in India?" },
  { icon: GraduationCap, text: "Help me find scholarship programs", query: "What government scholarship programs are available for students?" },
  { icon: Receipt, text: "Guide me through tax filing", query: "Can you guide me through the income tax filing process?" },
];

const ChatArea = ({ 
  messages, 
  input, 
  setInput, 
  isRecording, 
  handleSendMessage, 
  handleStartRecording, 
  handleStopRecording, 
  handlePlayTTS,
  onSuggestionClick 
}) => {
  const messagesEndRef = useRef(null);
  const isHeroState = messages.length <= 1;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="main-content">
      {isHeroState ? (
        /* === Hero / Landing State === */
        <div className="hero">
          <div className="hero__branding">
            <h1 className="hero__title">Access<span>Gov</span></h1>
            <p className="hero__subtitle">Navigate government services with AI</p>
          </div>

          <div className="hero__suggestions">
            {SUGGESTIONS.map((s, i) => (
              <button 
                key={i} 
                className="suggestion-card"
                onClick={() => onSuggestionClick(s.query)}
              >
                <div className="suggestion-card__icon">
                  <s.icon size={22} />
                </div>
                <span className="suggestion-card__text">{s.text}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* === Messages State === */
        <div className="messages">
          <div className="messages__wrapper">
            {messages.map((msg, i) => (
              <div key={i} className={`message message--${msg.role}`}>
                {msg.role === 'assistant' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
                
                {msg.role === 'assistant' && (
                  <button className="message__tts" onClick={() => handlePlayTTS(msg.content)} title="Read aloud">
                    <Volume2 size={15} /> Listen
                  </button>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* === Floating Input Bar === */}
      <div className="input-bar-container">
        <div className="input-bar">
          <button 
            className={`input-bar__mic ${isRecording ? 'input-bar__mic--recording' : ''}`}
            onMouseDown={handleStartRecording}
            onMouseUp={handleStopRecording}
            onMouseLeave={handleStopRecording}
            title="Hold to speak"
            aria-label={isRecording ? "Recording..." : "Hold to speak"}
          >
            <Mic size={20} />
          </button>
          
          <input 
            type="text" 
            className="input-bar__field" 
            placeholder="Ask about any government service..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          
          <button 
            className="input-bar__send" 
            onClick={handleSendMessage} 
            title="Send"
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;
