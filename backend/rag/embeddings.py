from pathlib import Path
import json

from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLEAN_CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clean_chunks.jsonl"
)

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print()
print("=" * 70)
print("LOADING LOCAL EMBEDDING MODEL")
print("=" * 70)

model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("Embedding model loaded successfully.")


# ============================================================
# LOAD CLEAN CHUNKS
# ============================================================

def load_clean_chunks() -> list[dict]:
    """
    Load the filtered chunks produced by content_filter.py.
    """

    if not CLEAN_CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"Clean chunks file not found: {CLEAN_CHUNKS_FILE}"
        )

    chunks = []

    with CLEAN_CHUNKS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            chunks.append(
                json.loads(line)
            )

    return chunks


# ============================================================
# CREATE EMBEDDING
# ============================================================

def create_embedding(text: str) -> list[float]:
    """
    Convert text into a local embedding vector.
    """

    embedding = model.encode(
        text,
        normalize_embeddings=True,
    )

    return embedding.tolist()


# ============================================================
# TEST
# ============================================================

def main():

    chunks = load_clean_chunks()

    print()
    print("=" * 70)
    print("LOCAL EMBEDDING TEST")
    print("=" * 70)

    print(
        f"Clean chunks available: {len(chunks)}"
    )

    if not chunks:
        raise RuntimeError(
            "No clean chunks were found."
        )

    first_chunk = chunks[0]

    print()
    print("CHUNK")
    print("-" * 70)

    print(
        f"Chunk ID:     "
        f"{first_chunk.get('chunk_id')}"
    )

    print(
        f"Document:     "
        f"{first_chunk.get('document')}"
    )

    print(
        f"Page:         "
        f"{first_chunk.get('page_start')}"
    )

    print()
    print("Creating local embedding...")

    embedding = create_embedding(
        first_chunk["text"]
    )

    print()
    print("EMBEDDING RESULT")
    print("-" * 70)

    print(
        f"Model:        {EMBEDDING_MODEL}"
    )

    print(
        f"Dimensions:   {len(embedding)}"
    )

    print(
        "First 10 values:"
    )

    print(
        embedding[:10]
    )

    print()
    print("Local embedding test successful.")


if __name__ == "__main__":
    main()