from openai import OpenAI

from backend.config import OPENAI_API_KEY
from backend.rag.retrieve import retrieve_chunks


# ============================================================
# OPENAI CLIENT
# ============================================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ============================================================
# RAG SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are the knowledge-based RAG agent for a cancer information
assistant.

Your job is to answer the user's question using ONLY the
retrieved evidence provided to you.

IMPORTANT RULES:

1. Do not invent information that is not supported by the
   retrieved evidence.

2. Do not use your general medical knowledge to fill gaps.

3. If the retrieved evidence is insufficient to answer the
   question, clearly say that the provided faculty material
   does not contain enough information.

4. The faculty documents may be old. Do not describe information
   from them as the latest or current medical guidance.

5. If the user asks for the latest, current, recently updated,
   or currently recommended information, explain that the
   provided faculty material alone cannot establish that.
   This question should be handled by the current-research
   component later in the system.

6. Answer clearly and in a patient-friendly way.

7. Do not diagnose the patient.

8. Do not prescribe treatment or medication.

9. When making factual claims from the retrieved evidence,
   include source references using the document name and page
   number.

10. If multiple retrieved sources support the answer, you may
    use multiple sources.

11. If retrieved sources contain conflicting information,
    explicitly mention the conflict rather than choosing
    information arbitrarily.

Your response should contain:

- A concise answer.
- A "Sources" section listing the relevant document and page(s).

Remember:
You are a retrieval-grounded knowledge agent, not a diagnostic
or treatment-prescribing system.
"""


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(chunks: list[dict]) -> str:
    """
    Convert retrieved chunks into a text context for the LLM.
    """

    context_parts = []

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):

        document = chunk.get(
            "document",
            "Unknown document",
        )

        page_start = chunk.get(
            "page_start",
            "Unknown",
        )

        page_end = chunk.get(
            "page_end",
            page_start,
        )

        section = chunk.get(
            "section",
            "Unknown section",
        )

        score = chunk.get(
            "score",
            0.0,
        )

        text = chunk.get(
            "text",
            "",
        )

        context_parts.append(
            f"""
--- SOURCE {index} ---

Document: {document}
Pages: {page_start}-{page_end}
Section: {section}
Similarity score: {score:.4f}

Text:
{text}
"""
        )

    return "\n".join(context_parts)


# ============================================================
# NORMALIZE RETRIEVAL RESULTS
# ============================================================

def normalize_results(
    results: list,
) -> list[dict]:
    """
    Convert Qdrant retrieval results into ordinary dictionaries.

    Keeping this conversion here makes the RAG agent independent
    from the internal Qdrant result object.
    """

    normalized = []

    for result in results:

        payload = result.payload or {}

        normalized.append(
            {
                "chunk_id": payload.get(
                    "chunk_id"
                ),
                "document": payload.get(
                    "document"
                ),
                "page_start": payload.get(
                    "page_start"
                ),
                "page_end": payload.get(
                    "page_end"
                ),
                "section": payload.get(
                    "section"
                ),
                "text": payload.get(
                    "text",
                    "",
                ),
                "source_type": payload.get(
                    "source_type"
                ),
                "source_year": payload.get(
                    "source_year"
                ),
                "source_id": payload.get(
                    "source_id"
                ),
                "embedding_model": payload.get(
                    "embedding_model"
                ),
                "score": float(
                    result.score
                ),
            }
        )

    return normalized


# ============================================================
# RAG ANSWER
# ============================================================

def answer_with_rag(
    question: str,
    top_k: int = 5,
) -> dict:
    """
    Retrieve faculty evidence and generate a grounded answer.
    """

    # --------------------------------------------------------
    # Retrieve evidence
    # --------------------------------------------------------

    raw_results = retrieve_chunks(
        question,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # Normalize Qdrant results
    # --------------------------------------------------------

    retrieved_chunks = normalize_results(
        raw_results
    )

    # --------------------------------------------------------
    # Handle no results
    # --------------------------------------------------------

    if not retrieved_chunks:

        return {
            "question": question,
            "answer": (
                "I could not find relevant information in "
                "the provided faculty material."
            ),
            "sources": [],
            "retrieved_chunks": [],
        }

    # --------------------------------------------------------
    # Build evidence context
    # --------------------------------------------------------

    context = build_context(
        retrieved_chunks
    )

    # --------------------------------------------------------
    # Build model input
    # --------------------------------------------------------

    user_prompt = f"""
USER QUESTION:

{question}


RETRIEVED FACULTY EVIDENCE:

{context}


Using ONLY the retrieved faculty evidence, answer the user's
question according to your system instructions.

Do not add medical facts from outside the retrieved evidence.
"""

    # --------------------------------------------------------
    # Call LLM
    # --------------------------------------------------------

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
    )

    answer = response.output_text

    # --------------------------------------------------------
    # Build source list
    # --------------------------------------------------------

    sources = []

    for chunk in retrieved_chunks:

        sources.append(
            {
                "document": chunk.get(
                    "document"
                ),
                "page_start": chunk.get(
                    "page_start"
                ),
                "page_end": chunk.get(
                    "page_end"
                ),
                "section": chunk.get(
                    "section"
                ),
                "source_year": chunk.get(
                    "source_year"
                ),
                "score": chunk.get(
                    "score"
                ),
            }
        )

    # --------------------------------------------------------
    # Return structured RAG result
    # --------------------------------------------------------

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": retrieved_chunks,
    }


# ============================================================
# TEST
# ============================================================

def main():

    question = (
        "What are the established risk factors for melanoma?"
    )

    result = answer_with_rag(
        question
    )

    print()
    print("=" * 70)
    print("RAG ANSWER")
    print("=" * 70)

    print()
    print(result["answer"])

    print()
    print("=" * 70)
    print("SOURCES")
    print("=" * 70)

    for source in result["sources"]:

        print(
            f"- {source['document']} "
            f"pages {source['page_start']}-"
            f"{source['page_end']} "
            f"(score: {source['score']:.4f})"
        )


if __name__ == "__main__":
    main()