import React from 'react';
import {
  User,
  Activity,
  AlertTriangle,
  PhoneCall,
  Layers,
  ChevronRight,
  ShieldCheck,
  Cpu,
  Loader2,
  Sparkles,
  Info
} from 'lucide-react';
import VerificationBadge from './VerificationBadge';

/**
 * MessageBubble renders an individual message in the chat stream.
 *
 * @param {Object} props
 * @param {Object} props.message - The message data
 * @param {Function} props.onInspect - Callback to open agent activity inspector for this message
 * @param {boolean} props.isSelected - Whether this message is currently being inspected
 */
export default function MessageBubble({ message, onInspect, isSelected }) {
  const isUser = message.role === 'user';
  const isEmergency =
    message.route?.intent === 'emergency' ||
    message.route?.emergency === true ||
    message.agents_used?.includes('emergency') ||
    (message.answer && message.answer.toLowerCase().includes('sounds like an emergency'));

  // Format timestamp
  const timeString = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  if (isUser) {
    return (
      <div className="message-row user">
        <div className="message-avatar user" title="You">
          <User size={18} />
        </div>
        <div className="message-content-wrapper">
          <div className="message-card user">
            <div className="message-body-text">{message.question || message.content}</div>
          </div>
          {timeString && <span className="message-timestamp">{timeString}</span>}
        </div>
      </div>
    );
  }

  // Assistant Message
  return (
    <div className="message-row assistant">
      <div
        className={`message-avatar assistant ${isEmergency ? 'emergency' : ''}`}
        title={isEmergency ? 'Emergency Clinical Agent' : 'OncoAgent Clinical Assistant'}
      >
        {isEmergency ? <AlertTriangle size={18} /> : <Activity size={18} />}
      </div>

      <div className="message-content-wrapper" style={{ width: '100%' }}>
        <div className={`message-card assistant ${isEmergency ? 'emergency' : ''}`}>
          {/* Emergency Safety Protocol Header Banner */}
          {isEmergency && (
            <div className="emergency-alert-header">
              <AlertTriangle size={18} />
              <span>SAFETY PROTOCOL TRIGGERED: IMMEDIATE ATTENTION RECOMMENDED</span>
            </div>
          )}

          {/* Card Meta Header */}
          <div className="card-header-bar">
            <div className="card-header-left">
              <VerificationBadge
                status={message.verification_status || 'PASS'}
                attempts={message.verification_attempts || 1}
                mode={message.mode}
              />
              {message.mode === 'mock' && (
                <span className="mode-pill mock" title="Running in development mock workflow">
                  <span className="mode-dot" />
                  Mock Dev Mode
                </span>
              )}
            </div>

            <div className="card-header-right">
              {timeString && <span className="message-timestamp">{timeString}</span>}
            </div>
          </div>

          {/* Response Text */}
          <div className="message-body-text">
            {message.answer || message.content}
          </div>

          {/* Emergency Helpline Box */}
          {isEmergency && (
            <div className="emergency-helpline-box">
              <div className="helpline-title">
                <PhoneCall size={14} />
                <span>Emergency & Support Resources</span>
              </div>
              <div className="helpline-contacts">
                <div className="helpline-chip">
                  <span>Emergency Assistance:</span>
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

          {/* Card Footer Bar: Multi-Agent Chain Preview & Inspect Action */}
          <div className="card-footer-bar">
            <div className="agents-chain-preview">
              <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                Agents:
              </span>
              {message.agents_used && message.agents_used.length > 0 ? (
                message.agents_used.map((agent, i) => (
                  <span key={i} className="agent-mini-chip">
                    {agent}
                  </span>
                ))
              ) : (
                <span className="agent-mini-chip">pipeline</span>
              )}
            </div>

            <button
              className={`inspect-trace-btn ${isSelected ? 'active' : ''}`}
              onClick={() => onInspect(message)}
              title="Inspect agent workflow trace and citation evidence"
            >
              <Cpu size={13} />
              <span>
                {message.sources?.length ? `${message.sources.length} Sources & ` : ''}Workflow Trace
              </span>
              <ChevronRight size={12} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * LoadingMessageBubble shows the active pipeline processing state.
 */
export function LoadingMessageBubble() {
  return (
    <div className="message-row assistant">
      <div className="message-avatar assistant" title="Processing multi-agent pipeline">
        <Loader2 size={18} className="spinner-icon" />
      </div>

      <div className="message-content-wrapper">
        <div className="loading-card">
          <div className="loading-pipeline-header">
            <Loader2 size={16} className="spinner-icon" />
            <span>Multi-Agent Workflow Active...</span>
          </div>

          <div className="loading-steps-list">
            <div className="loading-step-item active">
              <div className="step-indicator-circle active">
                <Loader2 size={10} className="spinner-icon" />
              </div>
              <span>1. Intent Router evaluating clinical context & urgency...</span>
            </div>
            <div className="loading-step-item active">
              <div className="step-indicator-circle active">
                <Loader2 size={10} className="spinner-icon" />
              </div>
              <span>2. Querying grounded faculty literature & research databases...</span>
            </div>
            <div className="loading-step-item active">
              <div className="step-indicator-circle active">
                <Loader2 size={10} className="spinner-icon" />
              </div>
              <span>3. Cross-verifying clinical evidence & synthesizing response...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
