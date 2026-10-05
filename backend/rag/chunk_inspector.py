import json
from collections import Counter
from pathlib import Path


INPUT_FILE = Path(
    "data/processed/knowledge_units/knowledge_units.json"
)


def load_knowledge_units():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Knowledge-unit file not found:\n{INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # ---------------------------------------------------------
    # The knowledge-unit builder stores metadata + chunks
    # inside a JSON object.
    #
    # Find the actual list of knowledge units automatically.
    # ---------------------------------------------------------

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        # Common possible keys
        possible_keys = [
            "chunks",
            "knowledge_units",
            "units",
            "documents",
            "data",
        ]

        for key in possible_keys:
            value = data.get(key)

            if isinstance(value, list):
                return value

        # If no known key works, look for the first list
        # containing dictionaries.
        for key, value in data.items():

            if isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    return value

    raise ValueError(
        "Could not find the knowledge-unit list inside "
        "knowledge_units.json."
    )


def main():

    print("Loading knowledge units...")

    chunks = load_knowledge_units()

    print()
    print("=" * 80)
    print("KNOWLEDGE UNIT QUALITY INSPECTION")
    print("=" * 80)

    print(f"Total knowledge units: {len(chunks)}")

    if not chunks:
        print("No knowledge units were found.")
        return

    # ---------------------------------------------------------
    # TEXT SIZE
    # ---------------------------------------------------------

    sizes = [
        len(chunk.get("text", ""))
        for chunk in chunks
    ]

    average_size = sum(sizes) / len(sizes)

    print()
    print("TEXT SIZE")
    print("-" * 80)

    print(f"Smallest unit: {min(sizes)} characters")
    print(f"Largest unit:  {max(sizes)} characters")
    print(f"Average unit:  {average_size:.0f} characters")

    # ---------------------------------------------------------
    # VERY SMALL UNITS
    # ---------------------------------------------------------

    small_units = [
        chunk
        for chunk in chunks
        if len(chunk.get("text", "")) < 300
    ]

    print()
    print("VERY SMALL UNITS")
    print("-" * 80)

    print(
        f"Units below 300 characters: "
        f"{len(small_units)}"
    )

    # ---------------------------------------------------------
    # LARGE UNITS
    # ---------------------------------------------------------

    large_units = [
        chunk
        for chunk in chunks
        if len(chunk.get("text", "")) > 2600
    ]

    print()
    print("LARGE UNITS")
    print("-" * 80)

    print(
        f"Units above 2600 characters: "
        f"{len(large_units)}"
    )

    # ---------------------------------------------------------
    # DOCUMENT INFORMATION
    # ---------------------------------------------------------

    documents = Counter(
        chunk.get("document", "Unknown")
        for chunk in chunks
    )

    print()
    print("DOCUMENT INFORMATION")
    print("-" * 80)

    print(
        f"Unique documents: {len(documents)}"
    )

    print()
    print("Top 15 documents by knowledge-unit count:")

    for document, count in documents.most_common(15):
        print(f"{count:6}  {document}")

    # ---------------------------------------------------------
    # DOCUMENT TYPES
    # ---------------------------------------------------------

    document_types = Counter(
        chunk.get("document_type", "Unknown")
        for chunk in chunks
    )

    print()
    print("DOCUMENT TYPES")
    print("-" * 80)

    for document_type, count in document_types.items():
        print(f"{document_type}: {count}")

    # ---------------------------------------------------------
    # SECTION INFORMATION
    # ---------------------------------------------------------

    sections = Counter(
        chunk.get("section") or "Unknown"
        for chunk in chunks
    )

    unknown_sections = sections.get("Unknown", 0)

    print()
    print("SECTION INFORMATION")
    print("-" * 80)

    print(
        f"Unique section values: {len(sections)}"
    )

    print(
        f"Units without useful section: "
        f"{unknown_sections}"
    )

    print()
    print("Top 20 section values:")

    for section, count in sections.most_common(20):
        print(f"{count:6}  {section}")

    # ---------------------------------------------------------
    # CHAPTER INFORMATION
    # ---------------------------------------------------------

    chapters = Counter(
        chunk.get("chapter") or "Unknown"
        for chunk in chunks
    )

    print()
    print("CHAPTER INFORMATION")
    print("-" * 80)

    print(
        f"Unique chapter values: {len(chapters)}"
    )

    print()
    print("Top 15 chapter values:")

    for chapter, count in chapters.most_common(15):
        print(f"{count:6}  {chapter}")

    # ---------------------------------------------------------
    # PAGE METADATA
    # ---------------------------------------------------------

    missing_pages = [
        chunk
        for chunk in chunks
        if chunk.get("page_start") is None
        or chunk.get("page_end") is None
    ]

    print()
    print("PAGE METADATA")
    print("-" * 80)

    print(
        f"Units missing page metadata: "
        f"{len(missing_pages)}"
    )

    # ---------------------------------------------------------
    # ID UNIQUENESS
    # ---------------------------------------------------------

    ids = [
        chunk.get("chunk_id")
        for chunk in chunks
    ]

    unique_ids = set(ids)

    print()
    print("ID CHECK")
    print("-" * 80)

    print(f"Total IDs:  {len(ids)}")
    print(f"Unique IDs: {len(unique_ids)}")

    if len(ids) == len(unique_ids):
        print("Result: PASS - all chunk IDs are unique.")
    else:
        print("Result: WARNING - duplicate chunk IDs found.")

    # ---------------------------------------------------------
    # REPRESENTATIVE SAMPLES
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("REPRESENTATIVE KNOWLEDGE UNITS")
    print("=" * 80)

    sample_indexes = [
        0,
        len(chunks) // 4,
        len(chunks) // 2,
        (len(chunks) * 3) // 4,
        len(chunks) - 1,
    ]

    already_seen = set()

    for index in sample_indexes:

        if index in already_seen:
            continue

        already_seen.add(index)

        chunk = chunks[index]

        print()
        print("-" * 80)
        print(f"Sample #{index + 1}")
        print("-" * 80)

        print(
            f"Chunk ID:      "
            f"{chunk.get('chunk_id')}"
        )

        print(
            f"Document:      "
            f"{chunk.get('document')}"
        )

        print(
            f"Document type: "
            f"{chunk.get('document_type')}"
        )

        print(
            f"Pages:         "
            f"{chunk.get('page_start')} - "
            f"{chunk.get('page_end')}"
        )

        print(
            f"Chapter:       "
            f"{chunk.get('chapter')}"
        )

        print(
            f"Section:       "
            f"{chunk.get('section')}"
        )

        print(
            f"Characters:    "
            f"{len(chunk.get('text', ''))}"
        )

        print()
        print("TEXT")
        print("-" * 80)

        text = chunk.get("text", "")

        print(text[:1500])

        if len(text) > 1500:
            print()
            print("[...text truncated...]")

    # ---------------------------------------------------------
    # FINAL
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)

    print(
        f"Knowledge units inspected: {len(chunks)}"
    )


if __name__ == "__main__":
    main()