import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ChatResponse } from '../types';
import './ChatMessage.css';

interface ChatMessageProps {
  message: ChatResponse;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getToolIcon = (tool: string) => {
    switch (tool.toLowerCase()) {
      case 'rag':
        return '📚';
      case 'tavily':
        return '🔍';
      case 'cache':
        return '⚡';
      case 'semantic_cache':
        return '🧠';
      case 'error':
        return '❌';
      default:
        return '🤖';
    }
  };

  const getToolLabel = (tool: string) => {
    switch (tool.toLowerCase()) {
      case 'rag':
        return 'RAG (Documentation Search)';
      case 'tavily':
        return 'Web Search';
      case 'cache':
        return 'Cache (Exact Match)';
      case 'semantic_cache':
        return 'Cache (Semantic Match)';
      case 'error':
        return 'Error';
      default:
        return tool;
    }
  };

  return (
    <div className="message-container">
      {/* User Message */}
      {message.userMessage && (
        <div className="message user-message">
          <div className="message-avatar">👤</div>
          <div className="message-content">
            <div className="message-text">{message.userMessage}</div>
            {message.timestamp && (
              <div className="message-timestamp">
                {formatTimestamp(message.timestamp)}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Assistant Message */}
      <div className="message assistant-message">
        <div className="message-avatar">🐍</div>
        <div className="message-content">
          <div className="message-header">
            <span className="tool-indicator">
              {getToolIcon(message.tool_used)} {getToolLabel(message.tool_used)}
            </span>
            {message.cached && (
              <span className="cache-indicator">
                ⚡ Cached Response
              </span>
            )}
          </div>
          
          <div className="message-text">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={tomorrow as any}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                // Custom styling for other markdown elements
                h1: ({ children }) => <h1 className="markdown-h1">{children}</h1>,
                h2: ({ children }) => <h2 className="markdown-h2">{children}</h2>,
                h3: ({ children }) => <h3 className="markdown-h3">{children}</h3>,
                p: ({ children }) => <p className="markdown-p">{children}</p>,
                ul: ({ children }) => <ul className="markdown-ul">{children}</ul>,
                ol: ({ children }) => <ol className="markdown-ol">{children}</ol>,
                li: ({ children }) => <li className="markdown-li">{children}</li>,
                blockquote: ({ children }) => (
                  <blockquote className="markdown-blockquote">{children}</blockquote>
                ),
                table: ({ children }) => (
                  <div className="markdown-table-wrapper">
                    <table className="markdown-table">{children}</table>
                  </div>
                ),
                th: ({ children }) => <th className="markdown-th">{children}</th>,
                td: ({ children }) => <td className="markdown-td">{children}</td>,
              }}
            >
              {message.response}
            </ReactMarkdown>
          </div>
          
          {message.timestamp && (
            <div className="message-timestamp">
              {formatTimestamp(message.timestamp)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 