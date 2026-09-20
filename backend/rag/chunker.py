import re
from typing import Any


# Approximate character targets.
# We will tune these later using evaluation.
TARGET_CHUNK_SIZE = 1600
MAX_CHUNK_SIZE = 2200
OVERLAP_SIZE = 250


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text without destroying useful structure.
    """

    # Normalize whitespace while preserving paragraph breaks.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces.
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse more than two blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def looks_like_heading(text: str) -> bool:
    """
    Heuristic heading detector.

    This is intentionally conservative because medical text
    should not be incorrectly classified as a heading.
    """

    text = text.strip()

    if not text:
        return False

    # Very long paragraphs are unlikely to be headings.
    if len(text) > 120:
        return False

    # Common heading patterns.
    if re.match(
        r"^(chapter|section|part)\s+\d+",
        text,
        flags=re.IGNORECASE,
    ):
        return True

    # Numbered headings such as:
    # 1. Introduction
    # 2.3 Diagnosis
    if re.match(r"^\d+(\.\d+)*\.?\s+[A-Z]", text):
        return True

    # Short lines written mostly in uppercase.
    letters = [char for char in text if char.isalpha()]

    if letters:
        uppercase_ratio = sum(
            char.isupper() for char in letters
        ) / len(letters)

        if uppercase_ratio > 0.8 and len(text) < 100:
            return True

    return False


def split_into_paragraphs(text: str) -> list[str]:
    """
    Split page text into paragraphs.
    """

    text = clean_text(text)

    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


def create_chunks_for_page(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Create semantic-ish chunks from one PDF page.

    We keep document and page metadata attached to every chunk.
    """

    document = page["document"]
    page_number = page["page"]
    text = page["text"]

    paragraphs = split_into_paragraphs(text)

    chunks = []

    current_paragraphs: list[str] = []
    current_size = 0
    current_section = "Unknown"

    def save_current_chunk() -> None:
        nonlocal current_paragraphs
        nonlocal current_size

        if not current_paragraphs:
            return

        chunk_text = "\n\n".join(current_paragraphs).strip()

        chunks.append(
            {
                "document": document,
                "page_start": page_number,
                "page_end": page_number,
                "section": current_section,
                "text": chunk_text,
            }
        )

        current_paragraphs = []
        current_size = 0

    for paragraph in paragraphs:

        if looks_like_heading(paragraph):
            # If we already have content, save it before
            # starting a new section.
            save_current_chunk()

            current_section = paragraph

            continue

        paragraph_size = len(paragraph)

        # If adding this paragraph would make the chunk too large,
        # save the current chunk first.
        if (
            current_paragraphs
            and current_size + paragraph_size > MAX_CHUNK_SIZE
        ):
            save_current_chunk()

        current_paragraphs.append(paragraph)
        current_size += paragraph_size

        # Save naturally once we reach our target size.
        if current_size >= TARGET_CHUNK_SIZE:
            save_current_chunk()

    save_current_chunk()

    return chunks


def add_chunk_ids(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Add deterministic IDs to chunks.
    """

    for index, chunk in enumerate(chunks, start=1):
        safe_document = re.sub(
            r"[^a-zA-Z0-9]+",
            "-",
            chunk["document"],
        ).strip("-")

        chunk["chunk_id"] = (
            f"{safe_document}"
            f"-p{chunk['page_start']}"
            f"-c{index}"
        )

    return chunks


def chunk_pages(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert extracted PDF pages into structured chunks.
    """

    all_chunks = []

    for page in pages:
        page_chunks = create_chunks_for_page(page)
        all_chunks.extend(page_chunks)

    return add_chunk_ids(all_chunks)


if __name__ == "__main__":
    from backend.rag.pdf_loader import load_all_pdfs

    print("Loading PDFs...")
    pages = load_all_pdfs()

    print()
    print("Creating chunks...")

    chunks = chunk_pages(pages)

    print()
    print("=" * 60)
    print("CHUNKING TEST")
    print("=" * 60)

    print(f"Pages loaded: {len(pages)}")
    print(f"Chunks created: {len(chunks)}")

    if chunks:
        print()
        print("FIRST CHUNK")
        print("-" * 60)

        first_chunk = chunks[0]

        print(f"Chunk ID: {first_chunk['chunk_id']}")
        print(f"Document: {first_chunk['document']}")
        print(f"Page: {first_chunk['page_start']}")
        print(f"Section: {first_chunk['section']}")
        print()
        print(first_chunk["text"][:1500])