# 🧪 Automated Test Suite

This directory is reserved for automated end-to-end evaluation, unit tests, and integration benchmarks for the Cancer Multi-Agent AI system.

## Test Scripts in Codebase:
- `backend/graph/emergency_node_test_offline.py`: Offline deterministic safety intercept test.
- `backend/graph/rag_node_test_offline.py`: Offline Faculty RAG retrieval node test.
- `backend/graph/research_node_test_offline.py`: Offline research agent test.
- `backend/graph/verification_retry_test_offline.py`: Multi-attempt verification retry loop test.
- `backend/graph/workflow_final_test_offline.py`: Full end-to-end LangGraph StateGraph test.
- `backend/rag/pdf_audit.py`: 103-PDF text extraction and readability audit.
- `backend/rag/chunk_inspector.py`: Knowledge unit distribution and ID uniqueness validator.
