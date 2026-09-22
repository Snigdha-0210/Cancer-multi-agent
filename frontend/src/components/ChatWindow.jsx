import React, { useEffect, useRef } from 'react';
import {
  BookOpen,
  Globe,
  ShieldCheck,
  Activity,
  AlertCircle,
  RefreshCw,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import MessageBubble, { LoadingMessageBubble } from './MessageBubble';

/**
 * ChatWindow manages the scrollable message viewport, welcome hero, and error cards.
 *
 * @param {Object} props
 * @param {Array} props.messages - List of chat messages
 * @param {boolean} props.isLoading - Whether a query is currently running
 * @param {Object|null} props.error - Error object if any
 * @param {Function} props.onRetry - Callback to retry failed question
 * @param {Function} props.onSelectPrompt - Callback when hero prompt is clicked
 * @param {Function} props.onInspectMessage - Callback to inspect message details in sidebar
 * @param {Object|null} props.selectedMessage - Currently inspected message
 */
export default function ChatWindow({
  messages = [],
  isLoading = false,
  error = null,
  onRetry,
  onSelectPrompt,
  onInspectMessage,
  selectedMessage,
}) {
  const scrollEndRef = useRef(null);

  // Auto-scroll on new messages or loading state
  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  return (
    <div className="chat-window">
      <div className="chat-window-inner">
        {/* Empty State Hero */}
        {messages.length === 0 && (
          <div className="welcome-hero">
            <div className="hero-shield-icon">
              <ShieldCheck size={28} />
            </div>

            <h1 className="hero-title">Oncology Intelligence Assistant</h1>
            <p className="hero-description">
              A specialized multi-agent system combining institutional oncology faculty knowledge, current peer-reviewed research, and strict fact-verification to provide grounded clinical answers.
            </p>

            {/* Architecture Highlights */}
            <div className="hero-features">
              <div className="hero-feature-card">
                <div className="feature-icon-box faculty">
                  <BookOpen size={16} />
                </div>
                <h4>Faculty Knowledge Base</h4>
                <p>Curated oncology guidelines, clinical textbook PDFs, and institutional protocols.</p>
              </div>

              <div className="hero-feature-card">
                <div className="feature-icon-box research">
                  <Globe size={16} />
                </div>
                <h4>Current Research</h4>
                <p>Extracts up-to-date literature and clinical trials for newly emerging therapies.</p>
              </div>

              <div className="hero-feature-card">
                <div className="feature-icon-box verified">
                  <ShieldCheck size={16} />
                </div>
                <h4>Evidence Verification</h4>
                <p>Multi-step automated fact-checking ensures answers match verified evidence sources.</p>
              </div>
            </div>

            {/* Starter Prompt Choices */}
            <div className="hero-prompts-container">
              <div className="hero-prompts-label">
                Select an example query to test the pipeline:
              </div>

              <div className="hero-prompts-list">
                <button
                  className="hero-prompt-btn"
                  onClick={() =>
                    onSelectPrompt(
                      'What are the established risk factors and early warning signs for melanoma skin cancer?'
                    )
                  }
                >
                  <span>What are the established risk factors and early warning signs for melanoma?</span>
                  <span className="prompt-badge faculty">Faculty RAG</span>
                </button>

                <button
                  className="hero-prompt-btn"
                  onClick={() =>
                    onSelectPrompt(
                      'What are the latest 2026 immunotherapy clinical trial findings for advanced oncology patients?'
                    )
                  }
                >
                  <span>What are the latest 2026 immunotherapy clinical trial findings?</span>
                  <span className="prompt-badge research">Live Research</span>
                </button>

                <button
                  className="hero-prompt-btn"
                  onClick={() =>
                    onSelectPrompt(
                      'I feel like I am going to die from unbearable chemo pain and need emergency help.'
                    )
                  }
                >
                  <span>Emergency: Experiencing sudden severe distress during chemotherapy</span>
                  <span className="prompt-badge emergency">Emergency Triage</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Message Stream */}
        {messages.map((msg, index) => (
          <MessageBubble
            key={msg.id || index}
            message={msg}
            isSelected={selectedMessage?.id === msg.id}
            onInspect={onInspectMessage}
          />
        ))}

        {/* Active Pipeline Loading Indicator */}
        {isLoading && <LoadingMessageBubble />}

        {/* Error State Banner */}
        {error && (
          <div className="error-card">
            <AlertCircle size={20} />
            <div className="error-card-content">
              <span className="error-card-title">Multi-Agent Workflow Error</span>
              <p>{error.message || 'An unexpected error occurred while communicating with the backend.'}</p>
              {onRetry && (
                <button className="error-retry-btn" onClick={onRetry}>
                  <RefreshCw size={12} />
                  <span>Retry Question</span>
                </button>
              )}
            </div>
          </div>
        )}

        <div ref={scrollEndRef} style={{ height: 1 }} />
      </div>
    </div>
  );
}
