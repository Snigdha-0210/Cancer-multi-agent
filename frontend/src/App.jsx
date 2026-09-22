import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import AgentActivity from './components/AgentActivity';
import { askQuestion, checkBackendHealth } from './services/api';

/**
 * Main Application Component for OncoAgent AI.
 */
export default function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuestion, setLastQuestion] = useState('');
  const [systemMode, setSystemMode] = useState('mock'); // 'mock' | 'live' | 'offline'
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [selectedMessage, setSelectedMessage] = useState(null);

  // Check backend health on initial load
  useEffect(() => {
    async function initHealth() {
      const health = await checkBackendHealth();
      if (health.online) {
        setSystemMode(health.mode || 'mock');
      } else {
        setSystemMode('offline');
      }
    }
    initHealth();
  }, []);

  /**
   * Submit question to the multi-agent backend.
   */
  const handleSendMessage = useCallback(
    async (questionText) => {
      const question = questionText.trim();
      if (!question || isLoading) return;

      const userMsgId = `user-${Date.now()}`;
      const userMessage = {
        id: userMsgId,
        role: 'user',
        question: question,
        content: question,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setLastQuestion(question);
      setError(null);
      setIsLoading(true);

      try {
        const response = await askQuestion(question);

        const assistantMsgId = `assistant-${Date.now()}`;
        const assistantMessage = {
          id: assistantMsgId,
          role: 'assistant',
          question: response.question || question,
          answer: response.answer,
          verification_status: response.verification_status || 'PASS',
          sources: response.sources || [],
          agents_used: response.agents_used || [],
          verification_attempts: response.verification_attempts || 1,
          mode: response.mode || systemMode,
          route: response.route || {},
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setSelectedMessage(assistantMessage);

        if (response.mode) {
          setSystemMode(response.mode);
        }
      } catch (err) {
        console.error('Error in multi-agent pipeline:', err);
        setError(err);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, systemMode]
  );

  const handleRetry = () => {
    if (lastQuestion) {
      handleSendMessage(lastQuestion);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setSelectedMessage(null);
    setError(null);
    setLastQuestion('');
  };

  const handleInspectMessage = (msg) => {
    setSelectedMessage(msg);
    setIsPanelOpen(true);
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        mode={systemMode}
        isPanelOpen={isPanelOpen}
        onTogglePanel={() => setIsPanelOpen((prev) => !prev)}
        onClearChat={handleClearChat}
        messageCount={messages.length}
      />

      {/* Main Workspace */}
      <main className="main-layout">
        {/* Central Chat Stream & Input */}
        <section className="chat-section">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            error={error}
            onRetry={handleRetry}
            onSelectPrompt={handleSendMessage}
            onInspectMessage={handleInspectMessage}
            selectedMessage={selectedMessage}
          />

          <ChatInput
            onSend={handleSendMessage}
            isLoading={isLoading}
            mode={systemMode}
          />
        </section>

        {/* Right-Side Agent Activity & Evidence Panel */}
        <AgentActivity
          isOpen={isPanelOpen}
          onClose={() => setIsPanelOpen(false)}
          selectedMessage={selectedMessage}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}
