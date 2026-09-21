from pathlib import Path

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

QDRANT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "qdrant"
)

COLLECTION_NAME = "cancer_faculty_knowledge"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 5


# ============================================================
# INITIALIZE
# ============================================================

def create_qdrant_client() -> QdrantClient:
    """
    Connect to the local persistent Qdrant database.
    """

    return QdrantClient(
        path=str(QDRANT_DIRECTORY)
    )


def load_embedding_model() -> SentenceTransformer:
    """
    Load the same embedding model used during ingestion.
    """

    return SentenceTransformer(
        MODEL_NAME
    )


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_chunks(
    question: str,
    top_k: int = TOP_K,
) -> list:
    """
    Convert the question into an embedding and
    retrieve the most semantically similar chunks.
    """

    client = create_qdrant_client()

    model = load_embedding_model()

    query_embedding = model.encode(
        question,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=top_k,
        with_payload=True,
    )

    return results.points


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(
    question: str,
    results: list,
) -> None:

    print()
    print("=" * 80)
    print("SEMANTIC RETRIEVAL TEST")
    print("=" * 80)

    print()
    print(f"Question:")
    print(question)

    print()
    print(f"Results returned: {len(results)}")

    print()

    for index, result in enumerate(
        results,
        start=1,
    ):

        payload = result.payload

        print("=" * 80)
        print(f"RESULT #{index}")
        print("=" * 80)

        print(
            f"Similarity score: {result.score:.4f}"
        )

        print(
            f"Document: "
            f"{payload.get('document')}"
        )

        print(
            f"Pages: "
            f"{payload.get('page_start')}"
            f"-"
            f"{payload.get('page_end')}"
        )

        print(
            f"Section: "
            f"{payload.get('section')}"
        )

        print(
            f"Source year: "
            f"{payload.get('source_year')}"
        )

        print()

        print("TEXT:")
        print(
            payload.get("text", "")
        )

        print()


# ============================================================
# TEST QUESTIONS
# ============================================================

def main():

    questions = [
        "What are the risk factors for melanoma?",
    ]

    for question in questions:

        results = retrieve_chunks(
            question,
            top_k=TOP_K,
        )

        display_results(
            question,
            results,
        )


if __name__ == "__main__":
    main()