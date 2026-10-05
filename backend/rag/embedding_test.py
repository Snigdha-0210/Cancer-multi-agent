import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/knowledge_units/knowledge_units.json"
)

OUTPUT_FILE = Path(
    "data/processed/embeddings/embedding_test.npz"
)


# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

TEST_SIZE = 100


# ---------------------------------------------------------
# Load knowledge units
# ---------------------------------------------------------

def load_knowledge_units():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Knowledge-unit file not found:\n{INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    # knowledge_units.json is a dictionary
    # containing the actual list.

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        for key in [
            "chunks",
            "knowledge_units",
            "units",
            "data",
        ]:

            if isinstance(data.get(key), list):
                return data[key]

        # Fallback: find the first list of dictionaries.
        for value in data.values():

            if isinstance(value, list) and value:

                if isinstance(value[0], dict):
                    return value

    raise ValueError(
        "Could not find knowledge units in the JSON file."
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("EMBEDDING TEST")
    print("=" * 70)

    print()
    print("Loading knowledge units...")

    chunks = load_knowledge_units()

    print(
        f"Total knowledge units available: {len(chunks)}"
    )

    if len(chunks) < TEST_SIZE:
        raise ValueError(
            f"Only {len(chunks)} knowledge units found. "
            f"Need at least {TEST_SIZE}."
        )

    # -----------------------------------------------------
    # Select test chunks
    # -----------------------------------------------------

    test_chunks = chunks[:TEST_SIZE]

    texts = [
        chunk["text"]
        for chunk in test_chunks
    ]

    print(
        f"Testing embeddings on {len(texts)} chunks..."
    )

    # -----------------------------------------------------
    # Load embedding model
    # -----------------------------------------------------

    print()
    print("Loading embedding model:")
    print(MODEL_NAME)

    model = SentenceTransformer(
        MODEL_NAME
    )

    print("Embedding model loaded successfully.")

    # -----------------------------------------------------
    # Generate embeddings
    # -----------------------------------------------------

    print()
    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    # -----------------------------------------------------
    # Inspect vectors
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("EMBEDDING RESULTS")
    print("=" * 70)

    print(
        f"Number of vectors: {embeddings.shape[0]}"
    )

    print(
        f"Embedding dimensions: {embeddings.shape[1]}"
    )

    print(
        f"Embedding dtype: {embeddings.dtype}"
    )

    print(
        f"Expected vectors: {TEST_SIZE}"
    )

    # -----------------------------------------------------
    # Basic numerical checks
    # -----------------------------------------------------

    print()
    print("VECTOR CHECKS")
    print("-" * 70)

    print(
        f"Contains NaN: "
        f"{np.isnan(embeddings).any()}"
    )

    print(
        f"Contains infinite values: "
        f"{np.isinf(embeddings).any()}"
    )

    norms = np.linalg.norm(
        embeddings,
        axis=1
    )

    print(
        f"Minimum vector norm: "
        f"{norms.min():.4f}"
    )

    print(
        f"Maximum vector norm: "
        f"{norms.max():.4f}"
    )

    # -----------------------------------------------------
    # Save test embeddings
    # -----------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    np.savez_compressed(
        OUTPUT_FILE,
        embeddings=embeddings,
        chunk_ids=np.array(
            [
                chunk["chunk_id"]
                for chunk in test_chunks
            ],
            dtype=str,
        ),
    )

    print()
    print("Saved test embeddings to:")

    print(
        OUTPUT_FILE
    )

    # -----------------------------------------------------
    # Show first vector
    # -----------------------------------------------------

    print()
    print("FIRST VECTOR")
    print("-" * 70)

    print(
        embeddings[0][:10]
    )

    print(
        "... "
        f"({embeddings.shape[1]} dimensions total)"
    )

    # -----------------------------------------------------
    # Finish
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("EMBEDDING TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()