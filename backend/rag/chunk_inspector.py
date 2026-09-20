from collections import Counter

from backend.rag.pdf_loader import load_all_pdfs
from backend.rag.chunker import chunk_pages


def main():
    print("Loading PDF pages...")
    pages = load_all_pdfs()

    print("Creating chunks...")
    chunks = chunk_pages(pages)

    print()
    print("=" * 70)
    print("CHUNK QUALITY INSPECTION")
    print("=" * 70)

    print(f"Total pages:  {len(pages)}")
    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        print("No chunks were created.")
        return

    # ---------------------------------------------------------
    # Basic size statistics
    # ---------------------------------------------------------

    sizes = [
        len(chunk["text"])
        for chunk in chunks
    ]

    average_size = sum(sizes) / len(sizes)

    print()
    print("TEXT SIZE")
    print("-" * 70)
    print(f"Smallest chunk: {min(sizes)} characters")
    print(f"Largest chunk:  {max(sizes)} characters")
    print(f"Average chunk:  {average_size:.0f} characters")

    # ---------------------------------------------------------
    # Section statistics
    # ---------------------------------------------------------

    sections = Counter(
        chunk["section"]
        for chunk in chunks
    )

    print()
    print("SECTION INFORMATION")
    print("-" * 70)
    print(f"Unique sections detected: {len(sections)}")

    unknown_count = sections.get("Unknown", 0)

    print(f"Chunks with 'Unknown' section: {unknown_count}")

    # ---------------------------------------------------------
    # Very small chunks
    # ---------------------------------------------------------

    small_chunks = [
        chunk
        for chunk in chunks
        if len(chunk["text"]) < 300
    ]

    print()
    print("VERY SMALL CHUNKS")
    print("-" * 70)
    print(f"Chunks below 300 characters: {len(small_chunks)}")

    # ---------------------------------------------------------
    # Print representative chunks
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("SAMPLE CHUNKS")
    print("=" * 70)

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
        print("-" * 70)
        print(f"Sample #{index + 1}")
        print("-" * 70)

        print(f"Chunk ID:   {chunk['chunk_id']}")
        print(f"Document:   {chunk['document']}")
        print(
            f"Pages:      "
            f"{chunk['page_start']} - {chunk['page_end']}"
        )
        print(f"Section:    {chunk['section']}")
        print(f"Characters: {len(chunk['text'])}")

        print()
        print(chunk["text"][:1000])


if __name__ == "__main__":
    main()