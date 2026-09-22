import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, BookOpen, Globe, AlertTriangle, CornerDownLeft } from 'lucide-react';

const QUICK_PROMPTS = [
  {
    label: 'Melanoma Risk Factors',
    text: 'What are the established risk factors and early warning signs for melanoma skin cancer?',
    icon: BookOpen,
    category: 'faculty',
  },
  {
    label: 'Latest 2026 Immunotherapy',
    text: 'What are the latest 2026 immunotherapy clinical trial findings for advanced oncology patients?',
    icon: Globe,
    category: 'research',
  },
  {
    label: 'Chemotherapy Side Effects',
    text: 'What are common side effects associated with chemotherapy regimens and how are they managed?',
    icon: BookOpen,
    category: 'faculty',
  },
  {
    label: 'Emergency / Urgent Safety',
    text: 'I am experiencing sudden severe shortness of breath and chest pain after chemotherapy.',
    icon: AlertTriangle,
    category: 'emergency',
  },
];

/**
 * ChatInput handles user text query entry and quick clinical suggestions.
 *
 * @param {Object} props
 * @param {Function} props.onSend - Submit callback (question: string)
 * @param {boolean} props.isLoading - Whether a query is in progress
 * @param {string} [props.mode="mock"] - "mock" | "live" | string
 */
export default function ChatInput({ onSend, isLoading, mode = 'mock' }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSelectQuickPrompt = (promptText) => {
    if (isLoading) return;
    setInput(promptText);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="chat-input-section">
      <div className="chat-input-wrapper">
        {/* Quick Suggestion Chips */}
        <div className="quick-chips-row">
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Sparkles size={12} style={{ color: 'var(--accent-cyan)' }} />
            Suggested:
          </span>
          {QUICK_PROMPTS.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                type="button"
                className="quick-chip-btn"
                onClick={() => handleSelectQuickPrompt(item.text)}
                disabled={isLoading}
              >
                <Icon size={12} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Input Box Form */}
        <form onSubmit={handleSubmit} className="input-form-box">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isLoading
                ? 'Processing multi-agent clinical pipeline...'
                : 'Ask a cancer research, clinical guideline, or patient care question...'
            }
            disabled={isLoading}
            className="input-textarea"
          />

          <div className="input-actions">
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="send-btn"
              title="Send question (Enter)"
              aria-label="Send question"
            >
              <Send size={16} />
            </button>
          </div>
        </form>

        <div className="input-helper-text">
          <span>Press <strong>Enter</strong> to submit, <strong>Shift + Enter</strong> for a new line</span>
          <span>
            {mode === 'mock'
              ? 'Development simulation — no live evidence retrieved'
              : 'Grounded in institutional faculty PDFs & current oncology research'}
          </span>
        </div>
      </div>
    </div>
  );
}
