from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

KNOWLEDGE_UNITS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "knowledge_units"
    / "knowledge_units.json"
)

EMBEDDINGS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embeddings"
    / "embedding_test.npz"
)


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 5


# ============================================================
# LOAD KNOWLEDGE UNITS
# ============================================================

def load_knowledge_units():
    print("Loading knowledge units...")

    with open(KNOWLEDGE_UNITS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The JSON may contain the list under one of these keys.
    if isinstance(data, list):
        units = data

    elif isinstance(data, dict):
        units = None

        for key in ["chunks", "knowledge_units", "units", "data"]:
            if isinstance(data.get(key), list):
                units = data[key]
                break

        if units is None:
            for value in data.values():
                if (
                    isinstance(value, list)
                    and value
                    and isinstance(value[0], dict)
                ):
                    units = value
                    break

        if units is None:
            raise ValueError(
                "Could not find knowledge-unit list in JSON file."
            )

    else:
        raise ValueError("Unexpected JSON structure.")

    print(f"Knowledge units loaded: {len(units)}")

    return units


# ============================================================
# LOAD TEST EMBEDDINGS
# ============================================================

def load_embeddings():
    print("Loading test embeddings...")

    data = np.load(EMBEDDINGS_PATH)

    # Find the stored array.
    if "embeddings" in data:
        embeddings = data["embeddings"]
    else:
        # Fallback: use the first array in the NPZ file.
        first_key = data.files[0]
        embeddings = data[first_key]

    print(f"Embeddings loaded: {embeddings.shape}")

    return embeddings


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(query_vector, document_vectors):
    """
    Because both query and document vectors are normalized,
    cosine similarity is simply the dot product.
    """

    return np.dot(document_vectors, query_vector)


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(rank, unit, score):
    print()
    print("=" * 70)
    print(f"RESULT #{rank}")
    print("=" * 70)

    print(f"Similarity score : {score:.4f}")
    print(f"Chunk ID          : {unit.get('chunk_id', 'N/A')}")
    print(f"Document          : {unit.get('document', 'N/A')}")
    print(f"Document type     : {unit.get('document_type', 'N/A')}")
    print(f"Page start        : {unit.get('page_start', 'N/A')}")
    print(f"Page end          : {unit.get('page_end', 'N/A')}")
    print(f"Chapter           : {unit.get('chapter', 'N/A')}")
    print(f"Section           : {unit.get('section', 'N/A')}")

    text = unit.get("text", "")

    print()
    print("TEXT")
    print("-" * 70)
    print(text[:1500])

    if len(text) > 1500:
        print("...")


# ============================================================
# RETRIEVE
# ============================================================

def retrieve(query, units, embeddings, model):
    print()
    print("=" * 70)
    print("QUERY")
    print("=" * 70)
    print(query)

    # Convert patient question into an embedding.
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype=np.float32
    )

    # Calculate similarity against all test vectors.
    scores = cosine_similarity(
        query_embedding,
        embeddings
    )

    # Highest scores first.
    top_indices = np.argsort(scores)[::-1][:TOP_K]

    print()
    print("=" * 70)
    print(f"TOP {TOP_K} RESULTS")
    print("=" * 70)

    for rank, index in enumerate(top_indices, start=1):
        display_result(
            rank,
            units[index],
            scores[index]
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SEMANTIC RETRIEVAL TEST")
    print("=" * 70)

    # Load knowledge units.
    units = load_knowledge_units()

    # IMPORTANT:
    # The embedding test used the FIRST 100 knowledge units.
    # Therefore we must use exactly those same 100 units here.
    test_units = units[:100]

    # Load embeddings.
    embeddings = load_embeddings()

    if len(test_units) != len(embeddings):
        raise ValueError(
            f"Mismatch: {len(test_units)} knowledge units "
            f"but {len(embeddings)} embeddings."
        )

    print(f"Testing retrieval on {len(test_units)} chunks.")

    # Load model.
    print()
    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("Embedding model loaded successfully.")

    # --------------------------------------------------------
    # TEST QUESTIONS
    # --------------------------------------------------------

    questions = [
        "What is noninvasive breast cancer?",
        "What is ductal carcinoma in situ?",
        "How is DCIS diagnosed?",
        "What are the treatment options for noninvasive breast cancer?",
        "What is lymph node involvement in breast cancer?"
    ]

    # --------------------------------------------------------
    # RUN RETRIEVAL TESTS
    # --------------------------------------------------------

    for question in questions:
        retrieve(
            question,
            test_units,
            embeddings,
            model
        )

    print()
    print("=" * 70)
    print("SEMANTIC RETRIEVAL TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()