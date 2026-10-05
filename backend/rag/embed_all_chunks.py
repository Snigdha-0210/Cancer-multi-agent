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

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embeddings"
)

OUTPUT_PATH = OUTPUT_DIR / "all_embeddings.npz"


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

BATCH_SIZE = 32


# ============================================================
# LOAD KNOWLEDGE UNITS
# ============================================================

def load_knowledge_units():

    print("Loading knowledge units...")

    with open(KNOWLEDGE_UNITS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

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
                "Could not find knowledge-unit list."
            )

    else:
        raise ValueError(
            "Unexpected knowledge-unit JSON structure."
        )

    print(f"Knowledge units loaded: {len(units)}")

    return units


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FULL KNOWLEDGE-BASE EMBEDDING")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD KNOWLEDGE UNITS
    # --------------------------------------------------------

    units = load_knowledge_units()

    texts = []

    for unit in units:

        text = unit.get("text", "").strip()

        if not text:
            text = " "

        texts.append(text)

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    print()
    print(f"Loading embedding model:")
    print(MODEL_NAME)

    model = SentenceTransformer(MODEL_NAME)

    print("Embedding model loaded successfully.")

    # --------------------------------------------------------
    # GENERATE EMBEDDINGS
    # --------------------------------------------------------

    print()
    print("Generating embeddings...")
    print(f"Total chunks : {len(texts)}")
    print(f"Batch size   : {BATCH_SIZE}")

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("EMBEDDING VALIDATION")
    print("=" * 70)

    print(f"Number of vectors : {embeddings.shape[0]}")
    print(f"Dimensions        : {embeddings.shape[1]}")
    print(f"Dtype             : {embeddings.dtype}")

    print(
        f"Contains NaN      : {np.isnan(embeddings).any()}"
    )

    print(
        f"Contains infinity : {np.isinf(embeddings).any()}"
    )

    norms = np.linalg.norm(
        embeddings,
        axis=1
    )

    print(
        f"Minimum norm      : {norms.min():.4f}"
    )

    print(
        f"Maximum norm      : {norms.max():.4f}"
    )

    # --------------------------------------------------------
    # CHECK EXPECTED SHAPE
    # --------------------------------------------------------

    if embeddings.shape[0] != len(units):

        raise ValueError(
            "Number of embeddings does not match "
            "number of knowledge units."
        )

    if embeddings.shape[1] != 384:

        raise ValueError(
            f"Unexpected embedding dimension: "
            f"{embeddings.shape[1]}"
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save chunk IDs separately so retrieval can map vectors
    # back to knowledge units.
    chunk_ids = np.array(
        [
            unit.get("chunk_id", "")
            for unit in units
        ],
        dtype=str
    )

    np.savez_compressed(
        OUTPUT_PATH,
        embeddings=embeddings,
        chunk_ids=chunk_ids
    )

    print()
    print("=" * 70)
    print("EMBEDDINGS SAVED")
    print("=" * 70)

    print(f"Output: {OUTPUT_PATH}")

    print()
    print("FULL EMBEDDING PROCESS COMPLETE")


if __name__ == "__main__":
    main()