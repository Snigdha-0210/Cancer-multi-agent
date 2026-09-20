# 📊 Project State & Roadmap

**Last Updated:** September 2026  
**Current Phase:** Phase 1 – Architecture Design & Core Documentation  
**Repository Version:** `v0.1.0-alpha`

---

## 🚦 Status Summary

| Area | Status | Progress | Notes |
| :--- | :--- | :--- | :--- |
| **Repository Setup** | ✅ Completed | 100% | GitHub remote linked, gitignore, docs initialized |
| **Architecture Specification** | 🔄 In Progress | 80% | Agent hierarchy, tools & flow defined |
| **Prompt Registry** | 🔄 In Progress | 60% | Initial agent prompts cataloged |
| **Agent Implementation** | ⏳ Planned | 0% | Core orchestrator and agent classes |
| **Medical RAG & PubMed Tool**| ⏳ Planned | 0% | PubMed API integration & embeddings |
| **Evaluation Suite** | ⏳ Planned | 0% | Benchmark test cases & scoring scripts |

---

## 🎯 Current Sprint Goals
- [x] Initialize Git repository and link to GitHub remote.
- [x] Create project documentation hierarchy in `docs/`:
  - `PROJECT_HANDOFF.md`
  - `PROJECT_STATE.md`
  - `ARCHITECTURE.md`
  - `DECISIONS.md`
  - `PROMPT_REGISTRY.md`
  - `EVALUATION.md`
- [ ] Implement base agent classes and orchestration framework (e.g. LangGraph / CrewAI).
- [ ] Build PubMed literature search and NCBI fetching tools.
- [ ] Create synthetic test patient cases for clinical pathway validation.

---

## 🛣️ Development Roadmap

### Phase 1: Foundations & Architecture (Current)
- Establish documentation and ADRs.
- Select multi-agent orchestration framework.
- Define data contracts and communication protocols between agents.

### Phase 2: Agent Tooling & RAG Pipelines
- Literature Research Agent with PubMed, PMC, and ClinicalTrials.gov query capabilities.
- Oncology Knowledge Base ingestion (NCCN/ESMO guideline embeddings).
- Pathology & Genomic report parsing tools.

### Phase 3: Collaborative Multi-Agent Consensus
- Orchestration loop: Chief Medical Officer / Orchestrator delegating to Specialist Agents.
- Consensus mechanism and differential diagnosis debate protocol.
- Clinical Safety and Hallucination Checker Agent.

### Phase 4: UI, API & Evaluation
- Fast-API backend for asynchronous multi-agent runs.
- Interactive dashboard for research visualization and trace inspection.
- Automated evaluation pipeline measuring citation accuracy and reasoning fidelity.

---

## ⚠️ Known Issues & Blockers
- None at this stage.
