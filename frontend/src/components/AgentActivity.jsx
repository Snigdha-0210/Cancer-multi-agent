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
  Layers,
  FileCheck,
  CheckCircle2,
  Circle,
  MinusCircle,
  Loader2,
} from 'lucide-react';
import SourcesPanel from './SourcesPanel';
import VerificationBadge from './VerificationBadge';

/**
 * AgentActivity — multi-agent workflow inspector and evidence panel.
 *
 * Pipeline:
 *   Router → Faculty RAG / Research / Emergency → Synthesis → Verification
 *
 * Node states: 'loading' | 'completed' | 'skipped' | 'default'
 */
export default function AgentActivity({
  isOpen,
  onClose,
  selectedMessage,
  isLoading,
}) {
  const [activeTab, setActiveTab] = useState('pipeline');

  /* ── derive data from the selected response ── */
  const agentsUsed      = selectedMessage?.agents_used || [];
  const route           = selectedMessage?.route || {};
  const sources         = selectedMessage?.sources || [];
  const verificationStatus = selectedMessage?.verification_status || 'UNKNOWN';
  const attempts        = selectedMessage?.verification_attempts || 1;
  const isEmergency     =
    route?.intent === 'emergency' ||
    route?.emergency === true ||
    agentsUsed.includes('emergency');

  /* ── node state helpers ── */
  // When isLoading=true and no agents used yet, router is active.
  // When response arrives, derive states from agentsUsed.
  const hasResponse  = agentsUsed.length > 0 && !isLoading;
  const hasAnything  = agentsUsed.length > 0 || isLoading;

  function nodeState(isActive, loadingDefault = false) {
    if (isLoading) {
      // During loading: router is "loading", rest are "queued"
      return loadingDefault ? 'loading' : 'queued';
    }
    if (!hasResponse) return 'default';
    return isActive ? 'completed' : 'skipped';
  }

  const routerState        = isLoading ? 'loading' : (hasResponse ? 'completed' : 'default');
  const facultyState       = nodeState(agentsUsed.includes('faculty_rag') || route?.faculty_rag);
  const researchState      = nodeState(agentsUsed.includes('research') || route?.current_research);
  const synthesisState     = nodeState(
    agentsUsed.includes('synthesis') || (agentsUsed.length > 0 && !isLoading)
  );
  const verificationState  = nodeState(
    agentsUsed.includes('verification') || (agentsUsed.length > 0 && !isLoading)
  );
  const emergencyState     = isEmergency
    ? (isLoading ? 'loading' : 'completed')
    : 'skipped';

  /* ── connector state ── */
  function connectorState(fromState) {
    if (fromState === 'loading') return 'active';
    if (fromState === 'completed') return 'completed';
    return '';
  }

  return (
    <>
      <aside
        className={`agent-activity-panel ${isOpen ? 'open' : ''}`}
        aria-label="Agent Activity and Evidence Panel"
      >
        {/* ── Panel Header ── */}
        <div className="panel-header">
          <div className="panel-header-title">
            <Activity size={16} style={{ color: 'var(--accent-cyan)' }} />
            <span>Agent Inspector</span>
          </div>
          <button
            className="panel-close-btn"
            onClick={onClose}
            title="Close Panel"
            aria-label="Close Inspector"
          >
            <X size={16} />
          </button>
        </div>

        {/* ── Tabs ── */}
        <div className="panel-tabs-bar">
          <button
            className={`panel-tab-btn ${activeTab === 'pipeline' ? 'active' : ''}`}
            onClick={() => setActiveTab('pipeline')}
          >
            <Cpu size={13} />
            <span>Workflow</span>
          </button>
          <button
            className={`panel-tab-btn ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
          >
            <Layers size={13} />
            <span>Evidence</span>
            <span className="panel-tab-count">{sources.length}</span>
          </button>
        </div>

        {/* ── Panel Body ── */}
        <div className="panel-content-scroll">

          {/* ══ PIPELINE TAB ══ */}
          {activeTab === 'pipeline' && (
            <div className="workflow-graph-box">
              {/* Section header */}
              <div className="workflow-section-title">
                <span>Multi-Agent Orchestration</span>
                {selectedMessage?.mode && (
                  <span className={`prompt-badge ${selectedMessage.mode === 'mock' ? 'mock' : 'faculty'}`}>
                    {selectedMessage.mode.toUpperCase()}
                  </span>
                )}
              </div>

              {/* ── No activity yet ── */}
              {!hasAnything && (
                <div className="pipeline-empty-state">
                  <Circle size={32} />
                  <p>Submit a question to activate the pipeline</p>
                </div>
              )}

              {/* ── Pipeline Nodes ── */}
              {hasAnything && (
                <div className="workflow-nodes-container">

                  {/* 1. ROUTER */}
                  <AgentNode
                    icon={<Compass size={16} />}
                    type="router"
                    name="Intent Router"
                    desc="Classifies clinical intent, urgency level, and determines routing path"
                    state={routerState}
                    statusLabel={{
                      loading: 'Analyzing',
                      completed: 'Routed',
                      queued: 'Queued',
                      skipped: 'Skipped',
                      default: 'Standby',
                    }}
                  />

                  {/* Connector 1 → 2 */}
                  <PipelineConnector
                    state={connectorState(routerState)}
                  />

                  {/* 2a/2b/2c — Branch nodes */}
                  {isEmergency ? (
                    /* Emergency branch */
                    <AgentNode
                      icon={<AlertTriangle size={16} />}
                      type="emergency"
                      name="Emergency Agent"
                      desc="Immediate safety triage and urgent clinical escalation protocol"
                      state={emergencyState}
                      isEmergency
                      statusLabel={{
                        loading: 'Triaging',
                        completed: 'Triggered',
                        skipped: 'Not activated',
                      }}
                    />
                  ) : (
                    <>
                      <AgentNode
                        icon={<BookOpen size={16} />}
                        type="faculty_rag"
                        name="Faculty RAG Agent"
                        desc="Retrieves grounded evidence from institutional oncology PDFs & curriculum"
                        state={facultyState}
                        statusLabel={{
                          loading: 'Retrieving',
                          completed: 'Grounded',
                          skipped: 'Bypassed',
                          queued: 'Queued',
                          default: 'Standby',
                        }}
                      />

                      <PipelineConnector
                        state={connectorState(facultyState)}
                      />

                      <AgentNode
                        icon={<Globe size={16} />}
                        type="research"
                        name="Research Agent"
                        desc="Scrapes and extracts latest clinical trials and peer-reviewed publications"
                        state={researchState}
                        statusLabel={{
                          loading: 'Querying',
                          completed: 'Queried',
                          skipped: 'Bypassed',
                          queued: 'Queued',
                          default: 'Standby',
                        }}
                      />
                    </>
                  )}

                  {/* Connector → Synthesis */}
                  <PipelineConnector
                    state={connectorState(isEmergency ? emergencyState : researchState)}
                  />

                  {/* 3. SYNTHESIS */}
                  <AgentNode
                    icon={<Cpu size={16} />}
                    type="synthesis"
                    name="Synthesis Agent"
                    desc="Combines grounded evidence into a structured clinical answer"
                    state={synthesisState}
                    statusLabel={{
                      loading: 'Synthesizing',
                      completed: 'Synthesized',
                      skipped: 'Standby',
                      queued: 'Queued',
                      default: 'Standby',
                    }}
                  />

                  {/* Connector → Verification */}
                  <PipelineConnector
                    state={connectorState(synthesisState)}
                  />

                  {/* 4. VERIFICATION */}
                  <AgentNode
                    icon={<ShieldCheck size={16} />}
                    type="verification"
                    name="Verification Agent"
                    desc="Cross-checks facts against retrieved literature to prevent hallucinations"
                    state={verificationState}
                    statusLabel={{
                      loading: 'Verifying',
                      completed: selectedMessage?.mode === 'mock'
                        ? 'Simulated'
                        : (verificationStatus || 'Done'),
                      skipped: 'Pending',
                      queued: 'Queued',
                      default: 'Pending',
                    }}
                  />
                </div>
              )}

              {/* ── Verification Metrics ── */}
              {selectedMessage && hasResponse && (
                <div className="verification-metric-box">
                  <div className="workflow-section-title">
                    <span>Verification Metrics</span>
                    <FileCheck size={13} />
                  </div>

                  <div className="metric-row">
                    <span className="metric-label">Clinical Verdict</span>
                    <VerificationBadge
                      status={verificationStatus}
                      attempts={attempts}
                      showAttempts={false}
                      mode={selectedMessage?.mode}
                    />
                  </div>

                  <div className="metric-row">
                    <span className="metric-label">Verification Attempts</span>
                    <span className="metric-value">{attempts}</span>
                  </div>

                  <div className="metric-row" style={{ alignItems: 'flex-start' }}>
                    <span className="metric-label">Agent Chain</span>
                    <div className="metric-agents-chain">
                      {agentsUsed.length > 0 ? (
                        agentsUsed.map((a, i) => (
                          <React.Fragment key={i}>
                            <span className="agent-mini-chip">{a}</span>
                            {i < agentsUsed.length - 1 && (
                              <span className="agent-chain-arrow">›</span>
                            )}
                          </React.Fragment>
                        ))
                      ) : (
                        <span className="metric-value" style={{ color: 'var(--text-muted)' }}>
                          —
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="metric-row">
                    <span className="metric-label">Sources Retrieved</span>
                    <span className="metric-value">{sources.length} items</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ══ EVIDENCE TAB ══ */}
          {activeTab === 'sources' && (
            <SourcesPanel sources={sources} />
          )}
        </div>
      </aside>
    </>
  );
}

/* ────────────────────────────────────────────
   AgentNode — individual pipeline step card
   ──────────────────────────────────────────── */
function AgentNode({ icon, type, name, desc, state, statusLabel = {}, isEmergency = false }) {
  const label = statusLabel[state] || state;

  const statusPillClass = {
    loading:   'loading',
    completed: 'completed',
    skipped:   'skipped',
    queued:    'queued',
    default:   'queued',
  }[state] || 'queued';

  const isSpinning = state === 'loading';
  const cardClass  = isEmergency && state === 'completed'
    ? 'emergency'
    : state;

  return (
    <div className={`agent-node ${cardClass}`}>
      <div className={`node-icon-circle ${type} ${isSpinning ? 'spinning' : ''}`}>
        {icon}
      </div>

      <div className="node-details">
        <div className="node-title-row">
          <span className="node-name">{name}</span>
          <span className={`node-status-pill ${statusPillClass} ${isEmergency && state === 'completed' ? 'emergency' : ''}`}>
            {state === 'loading' && (
              <Loader2 size={8} style={{ display: 'inline', marginRight: 3, animation: 'spin 1s linear infinite' }} />
            )}
            {state === 'completed' && !isEmergency && (
              <CheckCircle2 size={8} style={{ display: 'inline', marginRight: 3 }} />
            )}
            {state === 'skipped' && (
              <MinusCircle size={8} style={{ display: 'inline', marginRight: 3 }} />
            )}
            {label}
          </span>
        </div>
        <span className="node-desc">{desc}</span>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────
   PipelineConnector — animated vertical line
   ──────────────────────────────────────────── */
function PipelineConnector({ state }) {
  return (
    <div className={`pipeline-connector ${state}`}>
      <div className="pipeline-connector-line" />
    </div>
  );
}
