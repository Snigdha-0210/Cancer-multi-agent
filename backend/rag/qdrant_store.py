from pathlib import Path
import json
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


PROJECT_ROOT = Path(__file__).resolve().parents[2]

EMBEDDED_CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embedded_chunks.jsonl"
)

QDRANT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "qdrant"
)

COLLECTION_NAME = "cancer_faculty_knowledge"
VECTOR_SIZE = 384
DISTANCE_METRIC = Distance.COSINE
BATCH_SIZE = 64


def load_embedded_chunks() -> list[dict]:

    if not EMBEDDED_CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"Embedded chunks file not found:\n"
            f"{EMBEDDED_CHUNKS_FILE}"
        )

    chunks = []

    with EMBEDDED_CHUNKS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            chunks.append(json.loads(line))

    return chunks


def create_qdrant_client() -> QdrantClient:

    QDRANT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    return QdrantClient(
        path=str(QDRANT_DIRECTORY)
    )


def create_collection(
    client: QdrantClient,
) -> None:

    if client.collection_exists(COLLECTION_NAME):

        print(
            f"Deleting existing collection: "
            f"{COLLECTION_NAME}"
        )

        client.delete_collection(
            collection_name=COLLECTION_NAME
        )

    print(
        f"Creating collection: "
        f"{COLLECTION_NAME}"
    )

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=DISTANCE_METRIC,
        ),
    )


def insert_chunks(
    client: QdrantClient,
    chunks: list[dict],
) -> int:

    total_inserted = 0

    for start in range(
        0,
        len(chunks),
        BATCH_SIZE,
    ):

        batch = chunks[
            start:start + BATCH_SIZE
        ]

        points = []

        for chunk in batch:

            embedding = chunk.get("embedding")

            if not embedding:
                raise ValueError(
                    f"Chunk has no embedding: "
                    f"{chunk.get('chunk_id')}"
                )

            chunk_id = chunk.get("chunk_id")

            if not chunk_id:
                raise ValueError(
                    "Chunk is missing chunk_id."
                )

            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    chunk_id,
                )
            )

            payload = {
                "chunk_id": chunk_id,
                "document": chunk.get("document"),
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "section": chunk.get("section"),
                "text": chunk.get("text"),
                "source_type": chunk.get("source_type"),
                "source_year": chunk.get("source_year"),
                "source_id": chunk.get("source_id"),
                "embedding_model": chunk.get("embedding_model"),
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

        total_inserted += len(points)

        print(
            f"Inserted "
            f"{total_inserted}/{len(chunks)}"
        )

    return total_inserted


def print_collection_info(
    client: QdrantClient,
) -> None:

    collection_info = client.get_collection(
        collection_name=COLLECTION_NAME
    )

    print()
    print("=" * 70)
    print("QDRANT COLLECTION")
    print("=" * 70)

    print(f"Collection: {COLLECTION_NAME}")
    print(f"Points: {collection_info.points_count}")
    print(f"Vector size: {VECTOR_SIZE}")
    print(f"Distance: {DISTANCE_METRIC}")


def main():

    print("=" * 70)
    print("QDRANT KNOWLEDGE BASE BUILD")
    print("=" * 70)

    print()
    print("Loading embedded chunks...")

    chunks = load_embedded_chunks()

    print(
        f"Embedded chunks loaded: "
        f"{len(chunks)}"
    )

    if not chunks:
        raise RuntimeError(
            "No embedded chunks were found."
        )

    first_embedding = chunks[0].get("embedding")

    if not first_embedding:
        raise RuntimeError(
            "First chunk does not contain an embedding."
        )

    actual_dimension = len(first_embedding)

    print(
        f"Embedding dimensions: "
        f"{actual_dimension}"
    )

    if actual_dimension != VECTOR_SIZE:
        raise RuntimeError(
            f"Expected {VECTOR_SIZE}-dimensional "
            f"vectors but found "
            f"{actual_dimension}."
        )

    print()
    print("Creating local Qdrant client...")

    client = create_qdrant_client()

    print()
    print("Rebuilding collection...")

    create_collection(client)

    print()
    print("Inserting vectors...")

    inserted = insert_chunks(
        client,
        chunks,
    )

    print()
    print("=" * 70)
    print("QDRANT BUILD COMPLETE")
    print("=" * 70)

    print(
        f"Chunks loaded:    {len(chunks)}"
    )

    print(
        f"Points inserted:  {inserted}"
    )

    print(
        f"Collection:       {COLLECTION_NAME}"
    )

    print(
        f"Database:         {QDRANT_DIRECTORY}"
    )

    print_collection_info(client)


if __name__ == "__main__":
    main()
