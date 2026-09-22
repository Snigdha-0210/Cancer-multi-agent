import React, { useState } from 'react';
import {
  Activity,
  X,
  Compass,
  BookOpen,
  Globe,
  AlertTriangle,
  Cpu,
  ShieldCheck,
  ChevronDown,
  Layers,
  CheckCircle2,
  HelpCircle,
  FileCheck
} from 'lucide-react';
import SourcesPanel from './SourcesPanel';
import VerificationBadge from './VerificationBadge';

/**
 * AgentActivity displays the visual multi-agent workflow pipeline
 * and evidence inspection for the selected conversation turn.
 *
 * Pipeline Graph:
 * Router ➔ Faculty RAG / Research Agent / Emergency ➔ Synthesis Agent ➔ Verification Agent
 */
export default function AgentActivity({
  isOpen,
  onClose,
  selectedMessage,
  isLoading,
}) {
  const [activeTab, setActiveTab] = useState('pipeline'); // 'pipeline' | 'sources'

  if (!isOpen) return null;

  const agentsUsed = selectedMessage?.agents_used || [];
  const route = selectedMessage?.route || {};
  const sources = selectedMessage?.sources || [];
  const verificationStatus = selectedMessage?.verification_status || 'UNKNOWN';
  const attempts = selectedMessage?.verification_attempts || 1;
  const isEmergency =
    route?.intent === 'emergency' ||
    route?.emergency === true ||
    agentsUsed.includes('emergency');

  // Pipeline node definitions
  const isRouterActive = agentsUsed.includes('router') || isLoading;
  const isFacultyActive = agentsUsed.includes('faculty_rag') || route?.faculty_rag;
  const isResearchActive = agentsUsed.includes('research') || route?.current_research;
  const isEmergencyActive = isEmergency;
  const isSynthesisActive = agentsUsed.includes('synthesis') || (agentsUsed.length > 0 && !isLoading);
  const isVerificationActive = agentsUsed.includes('verification') || (agentsUsed.length > 0 && !isLoading);

  return (
    <aside className="agent-activity-panel" aria-label="Agent Activity and Evidence Panel">
      {/* Panel Header */}
      <div className="panel-header">
        <div className="panel-header-title">
          <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
          <span>Agent Workflow & Trace</span>
        </div>
        <button
          className="panel-close-btn"
          onClick={onClose}
          title="Close Panel"
          aria-label="Close Inspector"
        >
          <X size={18} />
        </button>
      </div>

      {/* Tabs */}
      <div className="panel-tabs-bar">
        <button
          className={`panel-tab-btn ${activeTab === 'pipeline' ? 'active' : ''}`}
          onClick={() => setActiveTab('pipeline')}
        >
          <Cpu size={14} />
          <span>Agent Pipeline</span>
        </button>
        <button
          className={`panel-tab-btn ${activeTab === 'sources' ? 'active' : ''}`}
          onClick={() => setActiveTab('sources')}
        >
          <Layers size={14} />
          <span>Evidence Sources</span>
          <span className="panel-tab-count">{sources.length}</span>
        </button>
      </div>

      {/* Panel Content */}
      <div className="panel-content-scroll">
        {activeTab === 'pipeline' && (
          <div className="workflow-graph-box">
            <div className="workflow-section-title">
              <span>Multi-Agent Orchestration Flow</span>
              {selectedMessage?.mode && (
                <span className={`prompt-badge ${selectedMessage.mode === 'mock' ? 'emergency' : 'faculty'}`}>
                  {selectedMessage.mode.toUpperCase()}
                </span>
              )}
            </div>

            {/* Pipeline Visual Graph */}
            <div className="workflow-nodes-container">
              {/* 1. ROUTER NODE */}
              <div
                className={`workflow-node-card ${
                  isRouterActive ? 'active' : 'bypassed'
                }`}
              >
                <div className="node-icon-box router">
                  <Compass size={18} />
                </div>
                <div className="node-details">
                  <div className="node-title-row">
                    <span className="node-name">1. Intent Router</span>
                    <span
                      className={`node-status-pill ${
                        isRouterActive ? 'completed' : 'bypassed'
                      }`}
                    >
                      {isRouterActive ? 'Executed' : 'Standby'}
                    </span>
                  </div>
                  <span className="node-desc">
                    Classifies clinical intent, urgency level, and determines routing path.
                  </span>
                </div>
              </div>

              {/* Connector */}
              <div className="workflow-connector-line">
                <ChevronDown size={14} />
              </div>

              {/* 2. BRANCH NODES (Faculty RAG / Research / Emergency) */}
              {isEmergencyActive ? (
                /* Emergency Agent Node */
                <div className="workflow-node-card active emergency">
                  <div className="node-icon-box emergency">
                    <AlertTriangle size={18} />
                  </div>
                  <div className="node-details">
                    <div className="node-title-row">
                      <span className="node-name">2. Emergency Agent</span>
                      <span className="node-status-pill active" style={{ color: '#f87171' }}>
                        Triggered
                      </span>
                    </div>
                    <span className="node-desc">
                      Immediate safety triage and urgent clinical escalation protocol.
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  {/* Faculty RAG Node */}
                  <div
                    className={`workflow-node-card ${
                      isFacultyActive ? 'active' : 'bypassed'
                    }`}
                  >
                    <div className="node-icon-box faculty_rag">
                      <BookOpen size={18} />
                    </div>
                    <div className="node-details">
                      <div className="node-title-row">
                        <span className="node-name">2a. Faculty RAG Agent</span>
                        <span
                          className={`node-status-pill ${
                            isFacultyActive ? 'completed' : 'bypassed'
                          }`}
                        >
                          {isFacultyActive ? 'Grounded' : 'Bypassed'}
                        </span>
                      </div>
                      <span className="node-desc">
                        Retrieves grounded evidence from institutional oncology PDFs & curriculum.
                      </span>
                    </div>
                  </div>

                  {/* Connector between branches if both or research */}
                  <div className="workflow-connector-line">
                    <ChevronDown size={14} />
                  </div>

                  {/* Research Agent Node */}
                  <div
                    className={`workflow-node-card ${
                      isResearchActive ? 'active' : 'bypassed'
                    }`}
                  >
                    <div className="node-icon-box research">
                      <Globe size={18} />
                    </div>
                    <div className="node-details">
                      <div className="node-title-row">
                        <span className="node-name">2b. Research Agent</span>
                        <span
                          className={`node-status-pill ${
                            isResearchActive ? 'completed' : 'bypassed'
                          }`}
                        >
                          {isResearchActive ? 'Queried' : 'Bypassed'}
                        </span>
                      </div>
                      <span className="node-desc">
                        Scrapes and extracts latest clinical trials and recent medical publications.
                      </span>
                    </div>
                  </div>
                </>
              )}

              {/* Connector */}
              <div className="workflow-connector-line">
                <ChevronDown size={14} />
              </div>

              {/* 3. SYNTHESIS NODE */}
              <div
                className={`workflow-node-card ${
                  isSynthesisActive ? 'active' : 'bypassed'
                }`}
              >
                <div className="node-icon-box synthesis">
                  <Cpu size={18} />
                </div>
                <div className="node-details">
                  <div className="node-title-row">
                    <span className="node-name">3. Synthesis Agent</span>
                    <span
                      className={`node-status-pill ${
                        isSynthesisActive ? 'completed' : 'bypassed'
                      }`}
                    >
                      {isSynthesisActive ? 'Synthesized' : 'Standby'}
                    </span>
                  </div>
                  <span className="node-desc">
                    Combines grounded evidence into patient-friendly clinical answers.
                  </span>
                </div>
              </div>

              {/* Connector */}
              <div className="workflow-connector-line">
                <ChevronDown size={14} />
              </div>

              {/* 4. VERIFICATION NODE */}
              <div
                className={`workflow-node-card ${
                  isVerificationActive ? 'active' : 'bypassed'
                }`}
              >
                <div className="node-icon-box verification">
                  <ShieldCheck size={18} />
                </div>
                <div className="node-details">
                  <div className="node-title-row">
                    <span className="node-name">4. Verification Agent</span>
                    <span
                      className={`node-status-pill ${
                        isVerificationActive ? 'completed' : 'bypassed'
                      }`}
                    >
                      {isVerificationActive ? (selectedMessage?.mode === 'mock' ? 'Simulated' : verificationStatus) : 'Pending'}
                    </span>
                  </div>
                  <span className="node-desc">
                    Cross-checks facts against retrieved literature to prevent hallucinations.
                  </span>
                </div>
              </div>
            </div>

            {/* Verification Status Card */}
            {selectedMessage && (
              <div className="verification-metric-box">
                <div className="workflow-section-title">
                  <span>Verification Metrics</span>
                  <FileCheck size={14} />
                </div>

                <div className="metric-row">
                  <span className="metric-label">Clinical Verdict:</span>
                  <VerificationBadge
                    status={verificationStatus}
                    attempts={attempts}
                    showAttempts={false}
                    mode={selectedMessage?.mode}
                  />
                </div>

                <div className="metric-row">
                  <span className="metric-label">Verification Attempts:</span>
                  <span className="metric-value">{attempts}</span>
                </div>

                <div className="metric-row">
                  <span className="metric-label">Active Agents:</span>
                  <span className="metric-value">
                    {agentsUsed.length > 0 ? agentsUsed.join(' → ') : 'None recorded'}
                  </span>
                </div>

                <div className="metric-row">
                  <span className="metric-label">Sources Cited:</span>
                  <span className="metric-value">{sources.length} items</span>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'sources' && (
          <SourcesPanel sources={sources} />
        )}
      </div>
    </aside>
  );
}
