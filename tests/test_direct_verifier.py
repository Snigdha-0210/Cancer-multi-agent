
from backend.rag.rag_agent import answer_with_rag
from backend.agents.verifier_agent import verify_answer
from backend.graph.verification_node import build_verification_evidence

QUESTION = "What are the risk factors for melanoma?"

print("\n" + "=" * 70)
print("DIRECT RAG + VERIFIER TEST")
print("=" * 70)

# 1. Retrieve evidence and generate the RAG answer
rag_result = answer_with_rag(QUESTION, top_k=5)

print("\nRAG ANSWER:")
print(rag_result["answer"])

# 2. Build evidence in the same format as the actual workflow
state = {
    "faculty_retrieved_chunks": rag_result["retrieved_chunks"],
    "faculty_evidence": "",
    "research_evidence": "",
    "emergency_response": "",
}

evidence = build_verification_evidence(state)

print("\nNUMBER OF RETRIEVED CHUNKS:")
print(len(rag_result["retrieved_chunks"]))

# 3. Verify the RAG answer against the original PDF evidence
print("\nRUNNING VERIFIER...")

verification = verify_answer(
    question=QUESTION,
    proposed_answer=rag_result["answer"],
    evidence=evidence,
)

print("\n" + "=" * 70)
print("VERIFICATION RESULT")
print("=" * 70)
print(verification)

print("\n" + "=" * 70)
print("CLAIM-SPECIFIC RETRIEVAL TEST")
print("=" * 70)

from backend.rag.rag_agent import retriever

test_claims = [
    "Melanoma risk increases with age.",
    "People with lighter skin, hair, and eyes have increased risk.",
    "A history of sunburn increases the risk of melanoma.",
]

for claim in test_claims:
    print("\nCLAIM:", claim)

    results = retriever.search(
        query=claim,
        top_k=3,
    )

    for result in results:
        print(
            f"\nScore: {result['score']:.4f}"
            f"\nDocument: {result['document']}"
            f"\nPages: {result['page_start']}-{result['page_end']}"
            f"\nText: {result['text'][:500]}"
        )