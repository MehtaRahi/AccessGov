import React, { useRef, useEffect } from 'react';
import { Mic, Send, Volume2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const ChatArea = ({ 
  currentChat, 
  messages, 
  input, 
  setInput, 
  isRecording, 
  handleSendMessage, 
  handleStartRecording, 
  handleStopRecording, 
  handlePlayTTS 
}) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-area">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.role === 'assistant' ? (
              <div className="markdown-body">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            ) : (
              msg.content
            )}
            
            {msg.role === 'assistant' && (
              <button className="tts-btn" onClick={() => handlePlayTTS(msg.content)} title="Read Aloud">
                <Volume2 size={16} /> Listen
              </button>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <button 
          className={`mic-btn ${isRecording ? 'recording' : ''}`}
          onMouseDown={handleStartRecording}
          onMouseUp={handleStopRecording}
          onMouseLeave={handleStopRecording}
          title="Hold to speak"
        >
          <Mic size={20} />
        </button>
        
        <input 
          type="text" 
          className="chat-input" 
          placeholder="Ask about government schemes..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
        />
        
        <button className="send-btn" onClick={handleSendMessage} title="Send Message">
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default ChatArea;
