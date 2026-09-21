from pathlib import Path
import json
import time

from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clean_chunks.jsonl"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embedded_chunks.jsonl"
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

BATCH_SIZE = 32


# ============================================================
# HELPERS
# ============================================================

def load_chunks() -> list[dict]:
    """
    Load filtered chunks from clean_chunks.jsonl.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    chunks = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            chunks.append(json.loads(line))

    return chunks


def save_embedded_chunks(
    chunks: list[dict],
    embeddings,
) -> None:
    """
    Save chunks together with their embedding vectors.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):

            record = {
                **chunk,
                "embedding": embedding.tolist(),
                "embedding_model": MODEL_NAME,
                "embedding_dimensions": len(embedding),
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


# ============================================================
# MAIN EMBEDDING PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("LOCAL EMBEDDING PIPELINE")
    print("=" * 70)

    print()
    print(f"Input file:")
    print(INPUT_FILE)

    print()
    print("Loading chunks...")

    chunks = load_chunks()

    print(f"Chunks loaded: {len(chunks)}")

    if not chunks:
        raise RuntimeError(
            "No chunks were found in the input file."
        )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print()
    print("Loading embedding model...")
    print(f"Model: {MODEL_NAME}")

    start_time = time.time()

    model = SentenceTransformer(
        MODEL_NAME
    )

    model_load_time = time.time() - start_time

    print(
        f"Model loaded in {model_load_time:.2f} seconds."
    )

    # --------------------------------------------------------
    # Extract text
    # --------------------------------------------------------

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print()
    print("Generating embeddings...")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Texts to embed: {len(texts)}")

    start_time = time.time()

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    embedding_time = time.time() - start_time

    print()
    print(
        f"Embedding generation completed in "
        f"{embedding_time:.2f} seconds."
    )

    # --------------------------------------------------------
    # Validate dimensions
    # --------------------------------------------------------

    embedding_dimensions = len(
        embeddings[0]
    )

    print()
    print("Embedding validation")
    print("-" * 70)
    print(
        f"Number of embeddings: {len(embeddings)}"
    )
    print(
        f"Embedding dimensions: {embedding_dimensions}"
    )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Number of embeddings does not match "
            "number of chunks."
        )

    if embedding_dimensions != 384:
        raise RuntimeError(
            f"Expected 384 dimensions, "
            f"but received {embedding_dimensions}."
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    print()
    print("Saving embedded chunks...")

    save_embedded_chunks(
        chunks,
        embeddings,
    )

    print()
    print("=" * 70)
    print("EMBEDDING COMPLETE")
    print("=" * 70)

    print()
    print(f"Input chunks:       {len(chunks)}")
    print(f"Embeddings:         {len(embeddings)}")
    print(f"Dimensions:         {embedding_dimensions}")
    print(f"Model:              {MODEL_NAME}")
    print()
    print(f"Output file:")
    print(OUTPUT_FILE)
    print()


if __name__ == "__main__":
    main()