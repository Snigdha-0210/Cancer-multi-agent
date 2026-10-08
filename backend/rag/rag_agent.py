import json
import urllib.request

from backend.rag.retriever import SemanticRetriever


# ============================================================
# SETTINGS
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


# ============================================================
# RETRIEVER
# ============================================================

retriever = SemanticRetriever()


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

12. Do not treat the similarity score as medical evidence.
    It is only an indication of semantic relevance.

Your response should contain:

- A concise answer.
- A "Sources" section listing the relevant document and page(s).

Remember:

You are a retrieval-grounded knowledge agent, not a diagnostic
or treatment-prescribing system.

Return a normal patient-friendly answer, not JSON.
"""


# ============================================================
# OLLAMA CALL
# ============================================================

def ask_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["response"]


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
# RETRIEVE EVIDENCE
# ============================================================

def retrieve_evidence(
    question: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve relevant evidence from the complete faculty
    knowledge base.

    This uses the current NumPy-based semantic retriever
    instead of Qdrant.
    """

    return retriever.search(
        query=question,
        top_k=top_k,
    )


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
    # Validate question
    # --------------------------------------------------------

    if not question or not question.strip():

        return {
            "question": question,
            "answer": "Please provide a question.",
            "sources": [],
            "retrieved_chunks": [],
        }

    # --------------------------------------------------------
    # Retrieve evidence
    # --------------------------------------------------------

    retrieved_chunks = retrieve_evidence(
        question,
        top_k=top_k,
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
    # Print retrieved context for debugging
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("GENERATED CONTEXT")
    print("=" * 70)

    try:
        print(user_prompt)
    except UnicodeEncodeError:
        print(
            user_prompt.encode(
                "ascii",
                errors="replace",
            ).decode("ascii")
        )

    # --------------------------------------------------------
    # Call local Qwen model
    # --------------------------------------------------------

    try:

        answer = ask_ollama(user_prompt)

    except Exception as e:

        print()
        print("=" * 70)
        print("RAG RETRIEVAL SUCCESSFUL — LLM GENERATION FAILED")
        print("=" * 70)
        print(f"Reason: {e}")

        answer = (
            "[LLM GENERATION UNAVAILABLE]\n\n"
            "The relevant faculty evidence was successfully "
            "retrieved, but the local language model could not "
            "generate the answer."
        )

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
                "chunk_id": chunk.get(
                    "chunk_id"
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

    questions = [
        "What are the established risk factors for melanoma?",
        "What is ductal carcinoma in situ?",
        "What are the symptoms of lung cancer?",
    ]

    for question in questions:

        result = answer_with_rag(
            question,
            top_k=5,
        )

        print()
        print("=" * 70)
        print("QUESTION")
        print("=" * 70)
        print(question)

        print()
        print("=" * 70)
        print("RAG ANSWER")
        print("=" * 70)
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