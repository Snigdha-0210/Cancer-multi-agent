import React, { useEffect, useRef } from 'react';
import {
  BookOpen,
  Globe,
  ShieldCheck,
  AlertCircle,
  RefreshCw,
  Compass,
  Cpu,
  ChevronRight,
} from 'lucide-react';
import MessageBubble, { LoadingMessageBubble } from './MessageBubble';

/**
 * ChatWindow — scrollable message viewport, welcome hero, and error card.
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

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  return (
    <div className="chat-window">
      <div className="chat-window-inner">

        {/* ── Welcome Hero ── */}
        {messages.length === 0 && (
          <div className="welcome-hero">
            {/* Icon */}
            <div className="hero-icon-area">
              <div className="hero-shield-icon">
                <ShieldCheck size={30} />
              </div>
            </div>

            <h1 className="hero-title">Oncology Intelligence Assistant</h1>
            <p className="hero-description">
              A specialized multi-agent system combining institutional oncology faculty knowledge,
              current peer-reviewed research, and strict fact-verification to provide grounded clinical answers.
            </p>

            {/* Mini pipeline architecture diagram */}
            <div className="hero-pipeline-diagram" aria-hidden="true">
              <div className="pipeline-step">
                <div className="pipeline-step-dot router">
                  <Compass size={13} />
                </div>
                <span className="pipeline-step-label">Router</span>
              </div>
              <div className="pipeline-arrow"><ChevronRight size={12} /></div>
              <div className="pipeline-step">
                <div className="pipeline-step-dot faculty">
                  <BookOpen size={13} />
                </div>
                <span className="pipeline-step-label">Faculty RAG</span>
              </div>
              <div className="pipeline-arrow"><ChevronRight size={12} /></div>
              <div className="pipeline-step">
                <div className="pipeline-step-dot research">
                  <Globe size={13} />
                </div>
                <span className="pipeline-step-label">Research</span>
              </div>
              <div className="pipeline-arrow"><ChevronRight size={12} /></div>
              <div className="pipeline-step">
                <div className="pipeline-step-dot synthesis">
                  <Cpu size={13} />
                </div>
                <span className="pipeline-step-label">Synthesis</span>
              </div>
              <div className="pipeline-arrow"><ChevronRight size={12} /></div>
              <div className="pipeline-step">
                <div className="pipeline-step-dot verify">
                  <ShieldCheck size={13} />
                </div>
                <span className="pipeline-step-label">Verification</span>
              </div>
            </div>

            {/* Feature cards */}
            <div className="hero-features">
              <div className="hero-feature-card">
                <div className="feature-icon-box faculty">
                  <BookOpen size={15} />
                </div>
                <h4>Faculty Knowledge Base</h4>
                <p>Curated oncology guidelines, clinical textbook PDFs, and institutional protocols.</p>
              </div>

              <div className="hero-feature-card">
                <div className="feature-icon-box research">
                  <Globe size={15} />
                </div>
                <h4>Current Research</h4>
                <p>Extracts up-to-date literature and clinical trials for emerging therapies.</p>
              </div>

              <div className="hero-feature-card">
                <div className="feature-icon-box verified">
                  <ShieldCheck size={15} />
                </div>
                <h4>Evidence Verification</h4>
                <p>Multi-step automated fact-checking ensures answers match verified sources.</p>
              </div>
            </div>

            {/* Starter prompts */}
            <div className="hero-prompts-container">
              <div className="hero-prompts-label">Example queries to test the pipeline</div>

              <div className="hero-prompts-list">
                <button
                  className="hero-prompt-btn"
                  onClick={() =>
                    onSelectPrompt(
                      'What are the established risk factors and early warning signs for melanoma skin cancer?'
                    )
                  }
                >
                  <span className="hero-prompt-btn-text">
                    What are the established risk factors and early warning signs for melanoma?
                  </span>
                  <div className="hero-prompt-btn-right">
                    <span className="prompt-badge faculty">Faculty RAG</span>
                    <ChevronRight size={13} style={{ color: 'var(--text-muted)' }} />
                  </div>
                </button>

                <button
                  className="hero-prompt-btn"
                  onClick={() =>
                    onSelectPrompt(
                      'What are the latest 2026 immunotherapy clinical trial findings for advanced oncology patients?'
                    )
                  }
                >
                  <span className="hero-prompt-btn-text">
                    What are the latest 2026 immunotherapy clinical trial findings?
                  </span>
                  <div className="hero-prompt-btn-right">
                    <span className="prompt-badge research">Live Research</span>
                    <ChevronRight size={13} style={{ color: 'var(--text-muted)' }} />
                  </div>
                </button>

                <button
                  className="hero-prompt-btn"
                  onClick={() =>
                    onSelectPrompt(
                      'I feel like I am going to die from unbearable chemo pain and need emergency help.'
                    )
                  }
                >
                  <span className="hero-prompt-btn-text">
                    Emergency: Experiencing sudden severe distress during chemotherapy
                  </span>
                  <div className="hero-prompt-btn-right">
                    <span className="prompt-badge emergency">Emergency Triage</span>
                    <ChevronRight size={13} style={{ color: 'var(--text-muted)' }} />
                  </div>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Message Stream ── */}
        {messages.map((msg, index) => (
          <MessageBubble
            key={msg.id || index}
            message={msg}
            isSelected={selectedMessage?.id === msg.id}
            onInspect={onInspectMessage}
          />
        ))}

        {/* ── Pipeline Loading Indicator ── */}
        {isLoading && <LoadingMessageBubble />}

        {/* ── Error Banner ── */}
        {error && (
          <div className="error-card">
            <AlertCircle size={18} />
            <div className="error-card-content">
              <span className="error-card-title">Multi-Agent Pipeline Error</span>
              <p>{error.message || 'An unexpected error occurred while communicating with the backend.'}</p>
              {onRetry && (
                <button className="error-retry-btn" onClick={onRetry}>
                  <RefreshCw size={11} />
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
