import React, { useState } from 'react';
import {
  BookOpen,
  Globe,
  ExternalLink,
  FileText,
  Calendar,
  Layers,
  Shield,
  ChevronDown,
} from 'lucide-react';

/**
 * SourcesPanel — categorised, collapsible evidence cards.
 *
 * Sources are grouped into:
 *  - Faculty Knowledge Base  (source_category === 'faculty_knowledge' or has document)
 *  - Current External Research (source_category === 'current_external_research')
 *  - Other
 */
export default function SourcesPanel({ sources = [] }) {
  if (!sources || sources.length === 0) {
    return (
      <div className="empty-state-card">
        <Shield size={36} />
        <p>No external citations for this response.</p>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          Direct safety responses and internal triage workflows do not attach reference documents.
        </span>
      </div>
    );
  }

  const facultySources = sources.filter(
    (s) =>
      s.source_category === 'faculty_knowledge' ||
      (!s.source_category && s.document)
  );

  const researchSources = sources.filter(
    (s) =>
      s.source_category === 'current_external_research' ||
      (!s.source_category && s.url && !s.document)
  );

  const otherSources = sources.filter(
    (s) => !facultySources.includes(s) && !researchSources.includes(s)
  );

  return (
    <div className="sources-list-container">
      {/* Faculty Knowledge */}
      {facultySources.length > 0 && (
        <div className="source-category-group">
          <div className="category-group-header faculty">
            <BookOpen size={14} />
            <span>Faculty Knowledge Base</span>
            <span className="group-count">{facultySources.length}</span>
          </div>
          {facultySources.map((source, idx) => (
            <EvidenceCard
              key={`faculty-${idx}`}
              source={source}
              type="faculty"
              index={idx}
            />
          ))}
        </div>
      )}

      {/* External Research */}
      {researchSources.length > 0 && (
        <div className="source-category-group">
          <div className="category-group-header research">
            <Globe size={14} />
            <span>Current External Research</span>
            <span className="group-count">{researchSources.length}</span>
          </div>
          {researchSources.map((source, idx) => (
            <EvidenceCard
              key={`research-${idx}`}
              source={source}
              type="research"
              index={idx}
            />
          ))}
        </div>
      )}

      {/* Other sources */}
      {otherSources.length > 0 && (
        <div className="source-category-group">
          <div className="category-group-header" style={{ color: 'var(--text-secondary)' }}>
            <Layers size={14} />
            <span>Other Sources</span>
            <span className="group-count">{otherSources.length}</span>
          </div>
          {otherSources.map((source, idx) => (
            <EvidenceCard
              key={`other-${idx}`}
              source={source}
              type="other"
              index={idx}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * EvidenceCard — individual collapsible source item.
 */
function EvidenceCard({ source, type, index }) {
  const [expanded, setExpanded] = useState(false);
  const hasSnippet = !!source.snippet;
  const hasUrl     = !!source.url;
  const hasExtra   = hasSnippet || hasUrl;

  const title =
    source.title ||
    source.document ||
    `${type === 'research' ? 'Research Publication' : 'Evidence Source'} #${index + 1}`;

  return (
    <div className="evidence-card">
      {/* Header row — always visible */}
      <div
        className="evidence-card-header"
        onClick={() => hasExtra && setExpanded((v) => !v)}
        style={{ cursor: hasExtra ? 'pointer' : 'default' }}
      >
        <div className="evidence-card-main">
          {/* Title + badge */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.45rem', justifyContent: 'space-between' }}>
            <span className="evidence-card-title">{title}</span>
            <span className={`prompt-badge ${type === 'faculty' ? 'faculty' : type === 'research' ? 'research' : ''}`}
              style={{ flexShrink: 0, marginTop: 1 }}>
              {type === 'faculty' ? 'Faculty' : type === 'research' ? 'Research' : 'Source'}
            </span>
          </div>

          {/* Meta tags */}
          <div className="evidence-meta-row">
            {source.document && source.document !== title && (
              <span className="evidence-meta-tag">
                <FileText size={10} />
                {source.document}
              </span>
            )}
            {(source.page_start !== undefined || source.page_end !== undefined) && (
              <span className="evidence-meta-tag">
                <Layers size={10} />
                {source.page_start !== undefined && source.page_end !== undefined && source.page_start !== source.page_end
                  ? `Pp. ${source.page_start}–${source.page_end}`
                  : `P. ${source.page_start ?? source.page_end}`}
              </span>
            )}
            {source.source_year && (
              <span className="evidence-meta-tag">
                <Calendar size={10} />
                {source.source_year}
              </span>
            )}
            {source.source_category && (
              <span className="evidence-meta-tag" style={{ textTransform: 'capitalize' }}>
                {source.source_category.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        </div>

        {/* Expand toggle */}
        {hasExtra && (
          <div className="evidence-card-actions">
            <button
              className={`evidence-expand-btn ${expanded ? 'open' : ''}`}
              onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v); }}
              aria-label={expanded ? 'Collapse evidence' : 'Expand evidence'}
            >
              <ChevronDown size={14} />
            </button>
          </div>
        )}
      </div>

      {/* Collapsible body */}
      {hasExtra && (
        <div className={`evidence-card-snippet ${expanded ? 'open' : ''}`}>
          <div className="evidence-snippet-inner">
            {hasSnippet && (
              <div className="snippet-text">"{source.snippet}"</div>
            )}
            {hasUrl && (
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="source-link-btn"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink size={11} />
                <span>View External Source</span>
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
