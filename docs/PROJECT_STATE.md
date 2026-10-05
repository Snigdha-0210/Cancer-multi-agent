# Cancer Multi-Agent RAG Assistant — Project State / Handoff

Last updated: 2026-10-06

## Project aim
Build a faculty-assigned multi-agent AI assistant for cancer patients.

Faculty requirements:
1. Question/conversation agent.
2. Knowledge/RAG agent grounded in the complete faculty cancer PDF collection.
3. Emergency/distress agent for serious emotional crisis.
4. Combining/orchestrator agent.
5. Verification agent for evidence/currentness.
6. External research/tool calling for questions outside the PDF knowledge base.
7. Faculty mentioned agentic chunking, Agentic RAG, and multi-agent architecture.

Safety framing:
- Research/educational prototype, not a diagnostic or treatment-prescribing system.
- Emergency handling is safety-critical.
- Old faculty references must not automatically be presented as current clinical guidance.
- Current/latest questions require current trusted external validation.

## User development preferences
- Beginner in agentic AI.
- Wants backend/agents built manually and understood step-by-step.
- Wants complete files and exact commands, not tiny snippets.
- Uses Antigravity.
- Frontend can be generated/polished with Antigravity/Claude.
- Under time pressure; avoid unnecessary detours.
- This file is the canonical handoff for continuing in a new chat.

Project folder:
C:\Users\misty\OneDrive\Documents\cancer-multi-agent

## Current stack
Python 3.12.10.
Important packages include FastAPI, Uvicorn, OpenAI SDK, Pydantic, pypdf, Qdrant client, sentence-transformers, PyTorch, scikit-learn, SciPy, LangGraph/LangChain.

Known issues:
- PyTorch import can hit Windows Application Control / WinError 4551 DLL blocking.
- qdrant_client can hit a grpc DLL Windows Application Control issue.
- Do not blindly reinstall these.
- Earlier live OpenAI tests encountered 429 TPM limits; avoid unnecessary repeated live calls.
- backend/config.py requires OPENAI_API_KEY.
- APP_MODE mock/live exists.
- Do not assume old OpenAI model names are valid without checking current API documentation.

## Source collection
Raw collection:
data/raw_pdfs/

Includes:
- a-practical-guide-to-skin-cancer-2018.pdf
- managing-skin-cancer-2010.pdf
- Cancer_Type.zip
- pdfs.zip
- skin_cancer.json
- .gitkeep

Cancer_Type.zip: 74 patient-guideline PDFs.
pdfs.zip: 29 oncology/reference PDFs.

Current extracted corpus: 103 PDFs total:
- 74 patient guidelines
- 29 oncology references

Important archive finding:
Older copies of two books were 0 bytes, while valid copies exist in the current pdfs.zip. Do not reintroduce the empty versions.

## Completed: source extraction
Script:
backend/rag/extract_sources.py

Output folders:
data/source_documents/patient_guidelines
data/source_documents/oncology_references

Result:
103 PDFs extracted/available.

## Completed: PDF audit
Script:
backend/rag/pdf_audit.py

Output:
data/processed/audit/pdf_audit.json

Latest audit:
- PDFs: 103
- Successful: 103
- Failed: 0
- Empty: 0
- Low-text: 0
- Total pages: 17,830
- Pages with text: 17,765
- Pages without text: 65
- Raw characters: 62,825,074

pypdf fontTools messages were warnings only; all PDFs succeeded.

## Completed: document map
Script:
backend/rag/build_document_map.py

Output:
data/processed/document_map/document_map.json

Latest run:
- 103 successful
- 0 failed
- 17,830 pages
- 61,888,702 cleaned characters

The map preserves page text and structural chapter/section hints.

Important decision:
- Chapter/section detection is only a hint.
- Some PDFs have running headers, page numbers, indexes, references, and other artifacts.
- Do not spend more time trying to make regex heading detection perfect unless retrieval tests show a real problem.
- Actual text + page metadata matter more.

## Completed: knowledge-unit chunking
Script:
backend/rag/knowledge_units.py

Input:
data/processed/document_map/document_map.json

Output:
data/processed/knowledge_units/knowledge_units.json

Latest successful run:
- Documents processed: 103
- Successful: 103
- Failed: 0
- Total knowledge units: 31,498

Chunk behavior:
- cleans text
- splits paragraph-like units
- splits long text at sentence boundaries
- hard-splits only as last resort
- target around 1800 chars
- max 2600 chars
- preserves document/chapter/section/page metadata

## Completed: chunk inspection
Script:
backend/rag/chunk_inspector.py

Latest results:
- Total units: 31,498
- Smallest: 5 chars
- Largest: 2,600 chars
- Average: 1,963 chars
- Under 300 chars: 1,148
- Over 2,600 chars: 0
- Documents: 103
- oncology_reference units: 27,153
- patient_guideline units: 4,345
- Units without useful section: 6
- Units missing page metadata: 0
- IDs: 31,498 total / 31,498 unique

Representative samples were generally coherent:
- 116.pdf: coherent noninvasive breast cancer/DCIS content.
- cancer-principles-and-practice-of-oncology-6e.pdf: coherent surgical/gastric/colon content, with normal PDF extraction artifacts.
- head and neck tumors.pdf: coherent pathology/diagnostic content.
- MD Anderson sample: one short tail fragment, illustrating small-fragment cases.
- waldenstrom-patient.pdf: an index page; not primary explanatory evidence, but potentially useful for navigation.

Decision:
Chunking is good enough to proceed. Do not redesign it just because some small chunks exist.

## Exact current position

103 PDFs
→ extraction COMPLETE
→ PDF audit COMPLETE
→ document map COMPLETE
→ 31,498 knowledge units COMPLETE
→ chunk quality inspection COMPLETE
→ NEXT: SMALL EMBEDDING TEST
→ vector storage/retrieval
→ retrieval evaluation
→ RAG agent
→ Agentic RAG
→ multi-agent orchestration
→ verification/currentness
→ emergency/safety integration
→ 1000+ grounded QA dataset
→ frontend integration
→ final testing/demo

## Immediate next step: embedding test

Do NOT embed all 31,498 units immediately.

First:
1. Select a small test batch, around 100 units.
2. Generate embeddings.
3. Confirm embedding model works.
4. Confirm vector dimensions.
5. Save test embeddings locally.
6. Run similarity search for real patient-style questions.
7. Inspect retrieved document/page/chunk/text.
8. Only after retrieval is acceptable, embed all 31,498 units.

Qdrant has a known Windows/grpc DLL issue. If it blocks local Qdrant, test embeddings/retrieval locally with NumPy first rather than derailing the project.

## Planned RAG architecture

Query
→ Router
→ retrieve
→ evaluate evidence sufficiency
→ refine/retrieve again if needed
→ external research if PDF evidence is insufficient/currentness is required
→ synthesize
→ verify
→ final answer

Evidence should retain:
- chunk_id
- source document
- page_start/page_end
- section/chapter when useful
- source year when available
- document type
- text

## Freshness rule

Faculty KB contains older textbooks/references as well as newer patient guidelines.

- “According to the provided PDFs” → faculty RAG.
- “Latest/current” → current trusted external research + verification.
- Never present old textbook claims as current 2026 clinical guidance without validation.

## QA dataset plan

Existing sample:
skin_cancer_sample_dataset_27QA (1).json

Sample fields:
id, category, cancer_type, topic_seed, question, gold_answer, empathy_opening, warmth_closing.

Eventually build 1000+ questions grounded in actual PDF chunks.

Keep richer internal provenance:
- source_document
- source_pages
- source_section
- evidence_chunk_ids
- question
- gold_answer

Do not generate the full QA dataset before retrieval quality is validated.

## Emergency/safety plan

Emergency/distress handling must be safety-first and should not depend only on normal RAG.

Prototype is not diagnostic/treatment-prescribing.

India resources planned for UI:
- 112 pan-India emergency response
- Tele-MANAS 14416 / 1800-89-14416

Verify current details before final deployment.

## Frontend

A polished dark OncoAgent frontend already exists via Antigravity/Claude, including agent inspector, pipeline/evidence/workflow UI, and emergency UI.

Frontend is not the current bottleneck. Focus on knowledge → embeddings → retrieval → RAG → agents.

## Important files

Scripts:
- backend/rag/extract_sources.py
- backend/rag/pdf_audit.py
- backend/rag/build_document_map.py
- backend/rag/knowledge_units.py
- backend/rag/chunk_inspector.py

Generated data:
- data/processed/inventory/source_inventory.json
- data/processed/audit/pdf_audit.json
- data/processed/document_map/document_map.json
- data/processed/knowledge_units/knowledge_units.json

## Do not lose these decisions

- Do not pretend to have read inaccessible files.
- Complete source corpus matters more than whether it came from Drive, ZIP, or local files.
- Do not endlessly perfect section detection.
- Do not embed everything before testing a small batch.
- Do not generate 1000+ QA before retrieval is validated.
- Preserve source provenance.
- Old sources require freshness validation before being presented as current.
- Emergency handling is safety-first.
- Work around known DLL/tooling problems rather than repeatedly reinstalling packages.
- Give the user complete files and exact commands.

## How to resume in a new chat

Upload this PROJECT_STATE.md.

Tell the new chat:

“I am continuing my cancer multi-agent RAG project. Read PROJECT_STATE.md first. Do not restart completed work. Continue from the CURRENT EXACT PROJECT POSITION / NEXT STEP.”

The new chat should start at:
SMALL EMBEDDING TEST

Do not redo extraction, PDF audit, document map, or knowledge-unit generation unless the source corpus changes or a concrete test shows a problem.
