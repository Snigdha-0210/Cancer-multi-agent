import json
import re
from pathlib import Path
from typing import Any


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCUMENT_MAP_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "document_map"
    / "document_map.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "knowledge_units"
)

OUTPUT_PATH = OUTPUT_DIR / "knowledge_units.json"


# ============================================================
# CHUNK SETTINGS
# ============================================================

MIN_CHUNK_CHARS = 800
TARGET_CHUNK_CHARS = 1800
MAX_CHUNK_CHARS = 2600


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """
    Clean extracted PDF text without changing its meaning.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Fix spaces before punctuation
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    return text.strip()


# ============================================================
# PARAGRAPH SPLITTING
# ============================================================

def split_into_paragraphs(text: str) -> list[str]:
    """
    Split page text into paragraph-like units.

    We primarily trust blank lines. If a PDF has poor paragraph
    formatting, we keep the text together rather than aggressively
    guessing boundaries.
    """

    text = clean_text(text)

    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)

    result = []

    for paragraph in paragraphs:
        paragraph = clean_text(paragraph)

        if not paragraph:
            continue

        # Ignore extremely tiny fragments such as isolated page numbers.
        if len(paragraph) < 30 and paragraph.isdigit():
            continue

        result.append(paragraph)

    return result


# ============================================================
# SENTENCE SPLITTING
# ============================================================

def split_long_text(text: str, max_chars: int) -> list[str]:
    """
    Split oversized text at sentence boundaries when possible.
    """

    if len(text) <= max_chars:
        return [text]

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text
    )

    pieces = []
    current = ""

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        if not current:
            current = sentence
            continue

        candidate = current + " " + sentence

        if len(candidate) <= max_chars:
            current = candidate
        else:
            pieces.append(current)
            current = sentence

    if current:
        pieces.append(current)

    # Extremely long individual sentences
    # are hard-split as a last resort.
    final_pieces = []

    for piece in pieces:

        if len(piece) <= max_chars:
            final_pieces.append(piece)
            continue

        start = 0

        while start < len(piece):
            end = min(start + max_chars, len(piece))

            final_pieces.append(
                piece[start:end].strip()
            )

            start = end

    return [
        piece
        for piece in final_pieces
        if piece.strip()
    ]


# ============================================================
# CHUNK BUILDING
# ============================================================

def build_chunks_from_pages(
    document: dict[str, Any]
) -> list[dict[str, Any]]:

    document_name = document["document"]
    document_type = document.get("document_type", "unknown")

    chunks = []

    current_text_parts: list[str] = []

    current_page_start = None
    current_page_end = None

    current_chapter = None
    current_section = None

    chunk_number = 0

    def flush_chunk():

        nonlocal current_text_parts
        nonlocal current_page_start
        nonlocal current_page_end
        nonlocal chunk_number
        nonlocal current_chapter
        nonlocal current_section

        if not current_text_parts:
            return

        text = " ".join(
            part.strip()
            for part in current_text_parts
            if part.strip()
        ).strip()

        if not text:
            return

        chunk_number += 1

        chunk_id = (
            f"{document_name}"
            f"-p{current_page_start}"
            f"-c{chunk_number}"
        )

        chunks.append(
            {
                "chunk_id": chunk_id,
                "source_id": document_name,
                "document": document_name,
                "document_type": document_type,
                "title": document.get("title", document_name),
                "chapter": current_chapter,
                "section": current_section,
                "page_start": current_page_start,
                "page_end": current_page_end,
                "text": text,
                "char_count": len(text),
            }
        )

        current_text_parts = []
        current_page_start = None
        current_page_end = None

    for page in document.get("pages", []):

        page_number = page.get("page")

        page_text = clean_text(
            page.get("text", "")
        )

        if not page_text:
            continue

        # Only update structural metadata when present.
        # We don't force unreliable headings.
        page_chapter = page.get("chapter")
        page_section = page.get("section")

        if page_chapter:
            current_chapter = page_chapter

        if page_section:
            current_section = page_section

        paragraphs = split_into_paragraphs(page_text)

        if not paragraphs:
            continue

        for paragraph in paragraphs:

            pieces = split_long_text(
                paragraph,
                MAX_CHUNK_CHARS
            )

            for piece in pieces:

                # Start a new chunk if needed.
                if not current_text_parts:

                    current_page_start = page_number
                    current_page_end = page_number

                    current_text_parts.append(piece)

                    continue

                candidate = (
                    " ".join(current_text_parts)
                    + " "
                    + piece
                )

                # Keep related material together.
                if len(candidate) <= TARGET_CHUNK_CHARS:

                    current_text_parts.append(piece)
                    current_page_end = page_number

                else:

                    flush_chunk()

                    current_page_start = page_number
                    current_page_end = page_number

                    current_text_parts.append(piece)

        # If the current chunk is already reasonably large,
        # allow a natural page boundary to close it.
        current_size = len(
            " ".join(current_text_parts)
        )

        if current_size >= TARGET_CHUNK_CHARS:
            flush_chunk()

    # Final chunk
    flush_chunk()

    return chunks


# ============================================================
# DOCUMENT PROCESSING
# ============================================================

def build_knowledge_units():

    if not DOCUMENT_MAP_PATH.exists():
        raise FileNotFoundError(
            f"Document map not found:\n{DOCUMENT_MAP_PATH}"
        )

    print("=" * 70)
    print("KNOWLEDGE UNIT BUILDER")
    print("=" * 70)

    with open(
        DOCUMENT_MAP_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        document_map = json.load(f)

    documents = document_map.get(
        "documents",
        []
    )

    print(f"Documents found: {len(documents)}")

    all_chunks = []

    successful = 0
    failed = 0

    for index, document in enumerate(
        documents,
        start=1
    ):

        document_name = document.get(
            "document",
            f"document_{index}"
        )

        print(
            f"[{index}/{len(documents)}] "
            f"{document_name}"
        )

        try:

            chunks = build_chunks_from_pages(
                document
            )

            all_chunks.extend(chunks)

            successful += 1

            print(
                f"    Chunks created: {len(chunks)}"
            )

        except Exception as exc:

            failed += 1

            print(
                f"    ERROR: {exc}"
            )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output = {
        "metadata": {
            "documents_processed": len(documents),
            "documents_successful": successful,
            "documents_failed": failed,
            "total_chunks": len(all_chunks),
            "min_chunk_chars": MIN_CHUNK_CHARS,
            "target_chunk_chars": TARGET_CHUNK_CHARS,
            "max_chunk_chars": MAX_CHUNK_CHARS,
        },
        "chunks": all_chunks,
    }

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=" * 70)
    print("KNOWLEDGE UNIT BUILD COMPLETE")
    print("=" * 70)

    print(f"Documents processed: {len(documents)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total chunks: {len(all_chunks)}")

    print()
    print("Output:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    build_knowledge_units()