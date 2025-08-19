import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import ChatMessage from './components/ChatMessage';
import { ChatResponse } from './types';

function App() {
  const [messages, setMessages] = useState<ChatResponse[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate session ID on component mount
    setSessionId(Math.random().toString(36).substring(2, 15));
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8001/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data: ChatResponse = await response.json();
      
      setMessages(prev => [...prev, {
        ...data,
        userMessage: userMessage,
        timestamp: new Date().toISOString(),
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        response: 'Sorry, I encountered an error while processing your request.',
        tool_used: 'Error',
        cached: false,
        session_id: sessionId,
        userMessage: userMessage,
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🐍 Python Documentation Assistant</h1>
        <p>Powered by RAG, Agent, and Semantic Caching</p>
      </header>
      
      <main className="chat-container">
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>Welcome to the Python Documentation Assistant!</h2>
              <p>Ask me anything about Python programming, and I'll help you find the answers using:</p>
              <ul>
                <li>📚 <strong>RAG (Retrieval-Augmented Generation)</strong> - Searches through your Python documentation</li>
                <li>🔍 <strong>Web Search</strong> - Finds information from the internet when needed</li>
                <li>⚡ <strong>Semantic Caching</strong> - Remembers similar questions for faster responses</li>
              </ul>
              <p>Try asking questions like:</p>
              <ul>
                <li>"How do I use list comprehensions?"</li>
                <li>"What are decorators in Python?"</li>
                <li>"Explain the difference between lists and tuples"</li>
              </ul>
            </div>
          )}
          
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
          
          {isLoading && (
            <div className="message assistant-message">
              <div className="message-content">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about Python programming..."
              disabled={isLoading}
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !inputMessage.trim()}
              className="send-button"
            >
              {isLoading ? '⏳' : '📤'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App; 