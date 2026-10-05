# 🤝 Project Handoff Guide

## 📋 Overview
Welcome to the **Cancer Multi-Agent System** repository. This document serves as an onboarding and engineering handoff reference for developers, researchers, and AI collaborators working on this codebase.

---

## 🎯 Project Mission
To provide an autonomous, state-driven multi-agent AI assistant for cancer patients, caregivers, and oncology researchers. The system couples deterministic crisis/safety guardrails with a deep **103-document biomedical RAG engine** (17,830 pages, 31,498 knowledge units), real-time external research agents (2026 FDA approvals), and an independent factual verification agent with iterative retry loops.

---

## ⚡ Quick Start & Setup

### 1. Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: 18+ (for frontend)
- **Git**: Configured with your GitHub credentials
- **OpenAI API Key**: In `.env` (optional for local/mock development)

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Snigdha-0210/Cancer-multi-agent.git
cd Cancer-multi-agent

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install fastapi uvicorn pydantic openai sentence-transformers qdrant-client pypdf langgraph python-dotenv
```

### 3. Configuration (.env)
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
APP_MODE=mock  # Set to 'live' for OpenAI & Qdrant execution, 'mock' for local UI development
```

---

## 📂 Repository Navigation
- [`backend/agents/`](file:///c:/Users/misty/OneDrive/Documents/cancer-multi-agent/backend/agents): Specialized agent definitions (Router, Emergency, Research, Synthesis, Verifier).
- [`backend/graph/`](file:///c:/Users/misty/OneDrive/Documents/cancer-multi-agent/backend/graph): LangGraph StateGraph nodes, edge routers, and offline test runners.
- [`backend/rag/`](file:///c:/Users/misty/OneDrive/Documents/cancer-multi-agent/backend/rag): High-precision RAG pipeline (`extract_sources.py`, `pdf_audit.py`, `build_document_map.py`, `knowledge_units.py`, `chunk_inspector.py`, `qdrant_store.py`).
- [`frontend/`](file:///c:/Users/misty/OneDrive/Documents/cancer-multi-agent/frontend): Modern React 19 + Vite user interface with real-time agent trace activity visualizer.
- [`docs/`](file:///c:/Users/misty/OneDrive/Documents/cancer-multi-agent/docs): Architectural blueprints, ADRs, prompts, and evaluation criteria.
- [`data/`](file:///c:/Users/misty/OneDrive/Documents/cancer-multi-agent/data): 103 PDF source documents, document maps, and Qdrant vector database.

---

## 🛡️ Critical Guidelines for Contributors
1. **Medical Disclaimer & Safety**: All agent outputs are strictly for research and decision support. Crisis/distress queries must deterministically trigger emergency de-escalation protocols.
2. **Temporal Grounding**: Maintain clear differentiation between historical guideline standards (e.g. 2010/2018) and real-time external research (e.g. 2026 FDA approvals).
3. **Citation Integrity**: Ensure all responses provide traceable, verifiable page-level citations from the 31,498 indexed knowledge units.
4. **Zero-PHI Guarantee**: Never persist or transmit patient identifiable information.
