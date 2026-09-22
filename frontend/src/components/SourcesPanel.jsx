import React from 'react';
import { BookOpen, Globe, ExternalLink, FileText, Calendar, Layers, Shield } from 'lucide-react';

/**
 * SourcesPanel renders the cited evidence grouped by category:
 * - Faculty Knowledge (Grounded clinical PDFs/curriculum)
 * - Current External Research (Live medical literature & trials)
 *
 * @param {Object} props
 * @param {Array} props.sources - Array of source objects from the backend
 */
export default function SourcesPanel({ sources = [] }) {
  if (!sources || sources.length === 0) {
    return (
      <div className="empty-state-card">
        <Shield size={36} />
        <p>No external citations retrieved for this response.</p>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Direct safety responses or internal triage workflows do not attach reference documents.
        </span>
      </div>
    );
  }

  // Categorize sources
  const facultySources = sources.filter(
    (s) => s.source_category === 'faculty_knowledge' || (!s.source_category && s.document)
  );

  const researchSources = sources.filter(
    (s) => s.source_category === 'current_external_research' || (!s.source_category && !s.document)
  );

  const otherSources = sources.filter(
    (s) =>
      s.source_category !== 'faculty_knowledge' &&
      s.source_category !== 'current_external_research' &&
      !facultySources.includes(s) &&
      !researchSources.includes(s)
  );

  return (
    <div className="sources-list-container">
      {/* Faculty Knowledge Group */}
      {facultySources.length > 0 && (
        <div className="source-category-group">
          <div className="category-group-header faculty">
            <BookOpen size={16} />
            <span>Faculty Knowledge Base ({facultySources.length})</span>
          </div>

          {facultySources.map((source, idx) => (
            <div key={`faculty-${idx}`} className="source-card">
              <div className="source-card-title-row">
                <span className="source-card-title">
                  {source.title || source.document || `Faculty Source #${idx + 1}`}
                </span>
                <span className="prompt-badge faculty">Faculty RAG</span>
              </div>

              <div className="source-meta-row">
                {source.document && (
                  <span className="source-meta-tag" title="Source Document">
                    <FileText size={11} style={{ display: 'inline', marginRight: 3 }} />
                    {source.document}
                  </span>
                )}
                {(source.page_start !== undefined || source.page_end !== undefined) && (
                  <span className="source-meta-tag" title="Page Range">
                    <Layers size={11} style={{ display: 'inline', marginRight: 3 }} />
                    Pages {source.page_start || '1'}–{source.page_end || source.page_start || '1'}
                  </span>
                )}
                {source.source_year && (
                  <span className="source-meta-tag" title="Publication Year">
                    <Calendar size={11} style={{ display: 'inline', marginRight: 3 }} />
                    {source.source_year}
                  </span>
                )}
              </div>

              {source.snippet && (
                <div className="source-snippet-box">
                  "{source.snippet}"
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Current External Research Group */}
      {researchSources.length > 0 && (
        <div className="source-category-group">
          <div className="category-group-header research">
            <Globe size={16} />
            <span>Current External Research ({researchSources.length})</span>
          </div>

          {researchSources.map((source, idx) => (
            <div key={`research-${idx}`} className="source-card">
              <div className="source-card-title-row">
                <span className="source-card-title">
                  {source.title || `Research Publication #${idx + 1}`}
                </span>
                <span className="prompt-badge research">Live Literature</span>
              </div>

              {source.snippet && (
                <div className="source-snippet-box">
                  "{source.snippet}"
                </div>
              )}

              {source.url && (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-link-btn"
                >
                  <ExternalLink size={12} />
                  <span>View External Source</span>
                </a>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Other Sources if present */}
      {otherSources.map((source, idx) => (
        <div key={`other-${idx}`} className="source-card">
          <div className="source-card-title-row">
            <span className="source-card-title">{source.title || `Evidence #${idx + 1}`}</span>
          </div>
          {source.snippet && (
            <div className="source-snippet-box">
              "{source.snippet}"
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
