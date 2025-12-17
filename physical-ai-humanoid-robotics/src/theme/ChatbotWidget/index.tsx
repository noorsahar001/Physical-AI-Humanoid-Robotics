import React, { useState, useEffect, useRef, useCallback } from 'react';
import styles from './styles.module.css';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'source' | 'error';
  content: string;
}

interface ChatResponseChunk {
  type: 'text' | 'source' | 'end' | 'error';
  content: string;
  session_id: string;
}

// API URL - configure based on environment
const API_BASE_URL = typeof window !== 'undefined'
  ? (window as any).CHATBOT_API_URL || 'http://localhost:8000/api/chatbot'
  : 'http://localhost:8000/api/chatbot';

// Simple UUID generator
const generateId = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

const ChatbotWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedText, setSelectedText] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize session ID from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedSessionId = localStorage.getItem('chatbot_session_id');
      if (storedSessionId) {
        setSessionId(storedSessionId);
      } else {
        const newId = generateId();
        setSessionId(newId);
        localStorage.setItem('chatbot_session_id', newId);
      }
    }
  }, []);

  // Scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Handle text selection on the page
  const handleTextSelection = useCallback(() => {
    if (typeof window !== 'undefined') {
      const selection = window.getSelection()?.toString().trim();
      if (selection && selection.length > 10 && selection.length < 2000) {
        setSelectedText(selection);
        localStorage.setItem('chatbot_selected_text', selection);
      }
    }
  }, []);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.addEventListener('mouseup', handleTextSelection);
      return () => {
        document.removeEventListener('mouseup', handleTextSelection);
      };
    }
  }, [handleTextSelection]);

  // Clear selected text
  const clearSelectedText = () => {
    setSelectedText(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('chatbot_selected_text');
    }
  };

  // Send message to the chatbot
  const sendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: input,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    const queryToSend = input;
    setInput('');

    // Get selected text if any
    const textToSend = selectedText;
    clearSelectedText();

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: queryToSend,
          selected_text: textToSend || null,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      let assistantResponseContent = '';

      // Initialize assistant message container
      const assistantMessageId = generateId();
      setMessages((prev) => [
        ...prev,
        { id: assistantMessageId, role: 'assistant', content: '' },
      ]);

      // Read the stream
      while (true) {
        const { value, done } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n').filter((line) => line.startsWith('data:'));

        for (const line of lines) {
          try {
            const dataString = line.substring(5).trim();
            if (!dataString) continue;

            const parsedChunk: ChatResponseChunk = JSON.parse(dataString);

            // Update session ID if changed
            if (parsedChunk.session_id && parsedChunk.session_id !== sessionId) {
              setSessionId(parsedChunk.session_id);
              if (typeof window !== 'undefined') {
                localStorage.setItem('chatbot_session_id', parsedChunk.session_id);
              }
            }

            if (parsedChunk.type === 'text') {
              assistantResponseContent += parsedChunk.content;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: assistantResponseContent }
                    : msg
                )
              );
            } else if (parsedChunk.type === 'source') {
              setMessages((prev) => [
                ...prev,
                { id: generateId(), role: 'source', content: parsedChunk.content },
              ]);
            } else if (parsedChunk.type === 'error') {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, role: 'error', content: parsedChunk.content }
                    : msg
                )
              );
            }
          } catch (parseError) {
            console.error('Error parsing chunk:', parseError, 'Line:', line);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: 'error',
          content: 'Sorry, something went wrong. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key press
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={styles.chatbotContainer}>
      {/* Toggle Button */}
      <button
        className={`${styles.toggleButton} ${isOpen ? styles.open : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className={styles.chatWindow}>
          {/* Header */}
          <div className={styles.chatHeader}>
            <h3 className={styles.chatTitle}>Book Assistant</h3>
            <button
              className={styles.closeButton}
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ✕
            </button>
          </div>

          {/* Selected Text Indicator */}
          {selectedText && (
            <div className={styles.selectedTextIndicator}>
              <span>📝</span>
              <span className={styles.selectedTextContent}>
                Selected: "{selectedText.substring(0, 50)}..."
              </span>
              <button
                className={styles.clearSelectedText}
                onClick={clearSelectedText}
                aria-label="Clear selected text"
              >
                ✕
              </button>
            </div>
          )}

          {/* Messages */}
          <div className={styles.messages}>
            {messages.length === 0 && (
              <div className={styles.message + ' ' + styles.assistant}>
                👋 Hi! I'm your book assistant. Ask me anything about Physical AI
                & Humanoid Robotics. You can also select text on the page to ask
                questions about it!
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`${styles.message} ${styles[msg.role]}`}
              >
                {msg.role === 'source' ? (
                  <a href={msg.content} target="_blank" rel="noopener noreferrer">
                    📖 Source: {msg.content}
                  </a>
                ) : (
                  msg.content
                )}
              </div>
            ))}
            {isLoading && <div className={styles.loadingIndicator}>...</div>}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={sendMessage} className={styles.inputForm}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about the book..."
              disabled={isLoading}
              aria-label="Message input"
            />
            <button type="submit" disabled={isLoading}>
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default ChatbotWidget;
