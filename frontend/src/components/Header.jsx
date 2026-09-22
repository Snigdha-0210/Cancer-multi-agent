import React, { useState } from 'react';
import {
  Activity,
  Shield,
  Trash2,
  Sliders,
  AlertCircle,
  X,
  HeartPulse,
  Info,
  ExternalLink
} from 'lucide-react';

/**
 * Header component for the OncoAgent AI Assistant.
 *
 * @param {Object} props
 * @param {string} props.mode - "mock" | "live" | "offline"
 * @param {boolean} props.isPanelOpen - Whether the inspector panel is currently open
 * @param {Function} props.onTogglePanel - Toggle inspector panel
 * @param {Function} props.onClearChat - Clear current conversation
 * @param {number} props.messageCount - Number of messages in conversation
 */
export default function Header({
  mode = 'mock',
  isPanelOpen,
  onTogglePanel,
  onClearChat,
  messageCount = 0,
}) {
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  return (
    <>
      <header className="app-header">
        {/* Brand */}
        <div className="header-brand">
          <div className="brand-icon-wrapper" title="Oncology Clinical Multi-Agent AI">
            <HeartPulse size={20} />
          </div>
          <div className="brand-info">
            <div className="brand-title">
              <span>OncoAgent</span>
              <span className="brand-badge">Clinical AI</span>
            </div>
            <span className="brand-subtitle">
              Multi-Agent Oncology Research & Patient Intelligence
            </span>
          </div>
        </div>

        {/* Center Mode & Status Pill */}
        <div className="header-center">
          {mode === 'mock' && (
            <div className="mode-pill mock" title="Running in development mock workflow (no live LLM / vector DB costs)">
              <span className="mode-dot" />
              <span>Dev Mock Mode</span>
            </div>
          )}

          {mode === 'live' && (
            <div className="mode-pill live" title="Connected to live multi-agent graph & Qdrant vector database">
              <span className="mode-dot" />
              <span>Live Multi-Agent</span>
            </div>
          )}

          {mode === 'offline' && (
            <div className="mode-pill offline" title="Backend server unreachable on port 8000">
              <span className="mode-dot" />
              <span>Backend Offline</span>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="header-actions">
          <button
            className="header-btn"
            onClick={() => setShowDisclaimer(true)}
            title="View Clinical Safety Disclaimer"
          >
            <Shield size={14} />
            <span>Safety Disclaimer</span>
          </button>

          {messageCount > 0 && (
            <button
              className="header-btn"
              onClick={onClearChat}
              title="Reset conversation"
            >
              <Trash2 size={14} />
              <span>Clear</span>
            </button>
          )}

          <button
            className={`header-btn ${isPanelOpen ? 'active' : ''}`}
            onClick={onTogglePanel}
            title="Toggle Agent Activity and Sources Inspector"
          >
            <Activity size={14} />
            <span>Agent Inspector</span>
          </button>
        </div>
      </header>

      {/* Persistent Clinical Advisory Ribbon */}
      <div className="clinical-disclaimer-ribbon">
        <Info size={14} />
        <span>
          This AI system supports clinical exploration and patient education. In an emergency, contact local emergency services or seek immediate medical care.
        </span>
      </div>

      {/* Clinical Safety Disclaimer Modal */}
      {showDisclaimer && (
        <div className="modal-overlay" onClick={() => setShowDisclaimer(false)}>
          <div className="disclaimer-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-row">
              <h3>
                <Shield size={20} style={{ color: 'var(--accent-cyan)' }} />
                <span>Clinical & Safety Disclaimer</span>
              </h3>
              <button
                className="panel-close-btn"
                onClick={() => setShowDisclaimer(false)}
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>

            <div className="modal-content-body">
              <p>
                <strong>OncoAgent Multi-Agent Assistant</strong> is an advanced clinical research and patient education interface designed to synthesize evidence from grounded faculty oncology materials and peer-reviewed medical publications.
              </p>
              <p>
                <strong>Not a Substitute for Professional Medical Advice:</strong> All responses, including synthesis and verification statuses, are provided for informational and research reference purposes only. They do not constitute formal diagnostic decisions, medical prescriptions, or clinical treatment plans.
              </p>
              <p>
                <strong>Emergency Protocol:</strong> If you or someone you know is experiencing sudden severe physical distress (such as acute respiratory distress, sudden chest pain, or anaphylaxis) or a crisis, please contact local emergency services or seek immediate medical care.
              </p>
            </div>

            <button
              className="modal-close-action-btn"
              onClick={() => setShowDisclaimer(false)}
            >
              I Understand
            </button>
          </div>
        </div>
      )}
    </>
  );
}
