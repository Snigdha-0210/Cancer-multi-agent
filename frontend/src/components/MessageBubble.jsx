import React from 'react';
import {
  User,
  Activity,
  AlertTriangle,
  PhoneCall,
  Cpu,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import VerificationBadge from './VerificationBadge';

/**
 * MessageBubble renders an individual chat message.
 *
 * User messages: right-aligned, simple bubble.
 * Assistant messages: structured clinical card with header, answer, and footer.
 */
export default function MessageBubble({ message, onInspect, isSelected }) {
  const isUser = message.role === 'user';
  const isEmergency =
    message.route?.intent === 'emergency' ||
    message.route?.emergency === true ||
    message.agents_used?.includes('emergency') ||
    (message.answer && message.answer.toLowerCase().includes('sounds like an emergency'));

  const timeString = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  /* ── User message ── */
  if (isUser) {
    return (
      <div className="message-row user">
        <div className="message-avatar user" title="You">
          <User size={16} />
        </div>
        <div className="message-content-wrapper">
          <div className="message-card user">
            {message.question || message.content}
          </div>
          {timeString && (
            <span className="message-timestamp">{timeString}</span>
          )}
        </div>
      </div>
    );
  }

  /* ── Assistant message ── */
  const agentsUsed = message.agents_used || [];
  const sources    = message.sources || [];

  return (
    <div className="message-row assistant">
      {/* Avatar */}
      <div
        className={`message-avatar assistant ${isEmergency ? 'emergency' : ''}`}
        title={isEmergency ? 'Emergency Clinical Agent' : 'OncoAgent Clinical Assistant'}
      >
        {isEmergency ? <AlertTriangle size={16} /> : <Activity size={16} />}
      </div>

      {/* Card */}
      <div className="message-content-wrapper">
        <div className={`message-card assistant ${isEmergency ? 'emergency' : ''}`}>

          {/* Emergency header banner */}
          {isEmergency && (
            <div className="emergency-alert-header">
              <AlertTriangle size={16} />
              <span>SAFETY PROTOCOL ACTIVATED — IMMEDIATE ATTENTION RECOMMENDED</span>
            </div>
          )}

          {/* Card header: verification + mode + time */}
          <div className="card-header-bar">
            <div className="card-header-left">
              <VerificationBadge
                status={message.verification_status || 'PASS'}
                attempts={message.verification_attempts || 1}
                mode={message.mode}
              />
              {message.mode === 'mock' && (
                <span className="mode-pill-inline mock">
                  Dev Simulation
                </span>
              )}
            </div>
            <div className="card-header-right">
              {timeString && (
                <span className="message-timestamp">{timeString}</span>
              )}
            </div>
          </div>

          {/* Answer body */}
          <div className="card-answer-body">
            <div className="message-body-text">
              {message.answer || message.content}
            </div>
          </div>

          {/* Emergency helpline */}
          {isEmergency && (
            <div className="emergency-helpline-box">
              <div className="helpline-title">
                <PhoneCall size={13} />
                <span>Emergency &amp; Support Resources</span>
              </div>
              <div className="helpline-contacts">
                <div className="helpline-chip">
                  <span>Emergency:</span>
                  <strong>112</strong>
                </div>
                <div className="helpline-chip">
                  <span>Tele-MANAS:</span>
                  <strong>14416</strong>
                </div>
                <div className="helpline-chip">
                  <span>Tele-MANAS:</span>
                  <strong>1800-89-14416</strong>
                </div>
              </div>
            </div>
          )}

          {/* Card footer: agents chain + inspect button */}
          <div className="card-footer-bar">
            {/* Agent chain preview */}
            <div className="agents-chain-preview">
              <span className="agents-chain-label">Agents:</span>
              {agentsUsed.length > 0 ? (
                agentsUsed.map((agent, i) => (
                  <React.Fragment key={i}>
                    <span className="agent-mini-chip">{agent}</span>
                    {i < agentsUsed.length - 1 && (
                      <span className="agent-chain-arrow">›</span>
                    )}
                  </React.Fragment>
                ))
              ) : (
                <span className="agent-mini-chip">pipeline</span>
              )}
            </div>

            {/* Inspect button */}
            <button
              className={`inspect-trace-btn ${isSelected ? 'active' : ''}`}
              onClick={() => onInspect(message)}
              title="Inspect agent workflow trace and citation evidence"
            >
              <Cpu size={12} />
              <span>
                {sources.length ? `${sources.length} Sources · ` : ''}Workflow
              </span>
              <ChevronRight size={11} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * LoadingMessageBubble — shown while the multi-agent pipeline runs.
 * Steps appear sequentially via CSS animation-delay.
 */
export function LoadingMessageBubble() {
  return (
    <div className="message-row assistant">
      <div className="message-avatar assistant" title="Processing multi-agent pipeline">
        <Loader2 size={16} className="spinner-icon" />
      </div>

      <div className="message-content-wrapper">
        <div className="loading-card">
          <div className="loading-pipeline-header">
            <Loader2 size={15} className="spinner-icon" />
            <span>Multi-Agent Pipeline Active</span>
          </div>

          <div className="loading-steps-list">
            <div className="loading-step-item">
              <div className="step-indicator-circle">
                <Loader2 size={9} className="spinner-icon" />
              </div>
              <span>Intent Router — classifying clinical context &amp; urgency</span>
            </div>

            <div className="loading-step-item">
              <div className="step-indicator-circle">
                <Loader2 size={9} className="spinner-icon" />
              </div>
              <span>Faculty RAG — querying institutional oncology knowledge base</span>
            </div>

            <div className="loading-step-item">
              <div className="step-indicator-circle">
                <Loader2 size={9} className="spinner-icon" />
              </div>
              <span>Synthesis &amp; Verification — grounding and cross-checking response</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
