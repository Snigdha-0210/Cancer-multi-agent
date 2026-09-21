import json
import sys


INPUT_FILE = "data/processed/chunks.jsonl"
CLEAN_FILE = "data/processed/clean_chunks.jsonl"


def load_chunks(path):
    chunks = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                chunks.append(json.loads(line))

    return chunks


def main():
    original = load_chunks(INPUT_FILE)
    clean = load_chunks(CLEAN_FILE)

    clean_ids = {
        chunk["chunk_id"]
        for chunk in clean
    }

    removed = [
        chunk
        for chunk in original
        if chunk["chunk_id"] not in clean_ids
    ]

    # Batch number supplied from command line.
    # Example:
    # python -m backend.rag.inspect_removed_chunks 2
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    batch_size = 20

    start = (batch - 1) * batch_size
    end = min(start + batch_size, len(removed))

    selected = removed[start:end]

    print("=" * 70)
    print("REMOVED CHUNK INSPECTION")
    print("=" * 70)

    print(f"Total removed chunks: {len(removed)}")
    print(f"Batch: {batch}")
    print(f"Showing: {start + 1}-{end}")

    for index, chunk in enumerate(selected, start=start + 1):

        print()
        print("=" * 70)
        print(f"REMOVED #{index}")
        print("=" * 70)

        print(f"Chunk ID: {chunk.get('chunk_id')}")
        print(f"Document: {chunk.get('document')}")
        print(
            f"Page: "
            f"{chunk.get('page_start')}-"
            f"{chunk.get('page_end')}"
        )
        print(f"Section: {chunk.get('section', 'Unknown')}")

        print()
        print(chunk.get("text", "")[:1500])


if __name__ == "__main__":
    main()