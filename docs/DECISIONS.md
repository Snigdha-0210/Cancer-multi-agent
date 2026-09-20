# 🏛️ Architecture Decision Records (ADRs)

This document records the key architectural and design decisions made throughout the lifecycle of the **Cancer Multi-Agent System**.

---

## 📑 Index of Decisions

- [ADR-001: Modular Multi-Agent Orchestration Framework](#adr-001-modular-multi-agent-orchestration-framework)
- [ADR-002: Dual-Layer Grounding & Citation Validation](#adr-002-dual-layer-grounding--citation-validation)
- [ADR-003: Hybrid RAG Strategy with Vector & Biomedical Knowledge Graphs](#adr-003-hybrid-rag-strategy-with-vector--biomedical-knowledge-graphs)
- [ADR-004: Strict Zero-PHI Data Ingestion Policy](#adr-004-strict-zero-phi-data-ingestion-policy)

---

## ADR-001: Modular Multi-Agent Orchestration Framework
- **Status**: Approved
- **Date**: 2026-09-20
- **Context**: The system requires multiple specialized agents (Literature, Genomics, Pathology, Therapeutics) collaborating on clinical cancer scenarios.
- **Decision**: Adopt a stateful graph-based orchestration pattern (e.g., LangGraph / state machine design) allowing dynamic routing, iterative critique loops, and parallel tool executions.
- **Consequences**:
  - *Pros*: Clear state management, debuggability, easy addition of new agent personas.
  - *Cons*: Slightly higher upfront structural boilerplate compared to simple linear chains.

---

## ADR-002: Dual-Layer Grounding & Citation Validation
- **Status**: Approved
- **Date**: 2026-09-20
- **Context**: Medical and oncology AI systems have near-zero tolerance for hallucinated facts, fake citations, or phantom clinical trials.
- **Decision**: Implement a dedicated **Clinical Safety & Verification Agent** that performs deterministic verification on all PubMed IDs (PMIDs), clinical trial identifiers (NCT numbers), and guideline references prior to output delivery.
- **Consequences**:
  - *Pros*: Guarantees high evidence integrity and trustworthiness.
  - *Cons*: Adds an additional latency step to final synthesis.

---

## ADR-003: Hybrid RAG Strategy with Vector & Biomedical Knowledge Graphs
- **Status**: Approved
- **Date**: 2026-09-20
- **Context**: Oncology data spans dense unstructured guidelines (NCCN/ESMO guidelines) as well as structured biomedical entities (genes, mutations, drug interactions).
- **Decision**: Combine semantic vector search (ChromaDB / Qdrant) with structured entity querying (OncoKB, ClinVar APIs) to provide both contextual literature and deterministic genetic variant interpretation.
- **Consequences**:
  - *Pros*: High precision for gene-drug pairings combined with broad conceptual understanding.
  - *Cons*: Requires maintaining API connections and vector embeddings.

---

## ADR-004: Strict Zero-PHI Data Ingestion Policy
- **Status**: Approved
- **Date**: 2026-09-20
- **Context**: Handling clinical notes and patient records carries privacy and regulatory risks (HIPAA/GDPR).
- **Decision**: All local storage, test fixtures, and external API payloads must be strictly synthetic or anonymized using automated de-identification pipelines prior to agent intake.
- **Consequences**:
  - *Pros*: Compliance with data privacy standards and zero risk of patient data exposure.
  - *Cons*: Synthetic data generators must be maintained for realistic testing.
