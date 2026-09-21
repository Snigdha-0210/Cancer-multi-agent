import json
import re
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_CHUNK_SIZE = 1400
MAX_CHUNK_SIZE = 2200
MIN_CHUNK_SIZE = 300

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIRECTORY / "chunks.jsonl"


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """
    Normalize extracted PDF text.

    This removes unnecessary whitespace while preserving
    enough structure for sentence and section detection.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_standalone_page_numbers(text: str) -> str:
    """
    Remove lines that contain only a page number.
    """

    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        if re.fullmatch(r"\d{1,4}", stripped):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# ============================================================
# DOCUMENT FILTERING
# ============================================================

def looks_like_table_of_contents(text: str) -> bool:
    """
    Detect table-of-contents pages.

    TOC pages often contain many chapter titles followed by
    page numbers.
    """

    lowered = text.lower()

    toc_terms = [
        "contents",
        "table of contents",
    ]

    toc_term_found = any(
        term in lowered[:500]
        for term in toc_terms
    )

    page_reference_patterns = re.findall(
        r"\.\s*\.{2,}\s*\d+",
        text,
    )

    numbered_entries = re.findall(
        r"\b\d+\s+[A-Z][A-Za-z\s:-]{3,}",
        text,
    )

    if toc_term_found and len(page_reference_patterns) >= 2:
        return True

    if len(page_reference_patterns) >= 4:
        return True

    if toc_term_found and len(numbered_entries) >= 5:
        return True

    return False


def looks_like_references(text: str) -> bool:
    """
    Detect bibliography/reference pages.

    We do not want ordinary reference lists to dominate
    retrieval results.
    """

    lowered = text.lower()

    reference_terms = [
        "references",
        "bibliography",
        "references and suggested reading",
        "selected references",
    ]

    reference_heading = any(
        term in lowered[:250]
        for term in reference_terms
    )

    citation_patterns = re.findall(
        r"\(\d{4}\)",
        text,
    )

    journal_patterns = re.findall(
        r"\b(?:journal|jama|nejm|lancet|dermatol|cancer)\b",
        lowered,
    )

    if reference_heading and len(citation_patterns) >= 3:
        return True

    if reference_heading and len(journal_patterns) >= 3:
        return True

    return False


def looks_like_index(text: str) -> bool:
    """
    Detect index pages.

    Index entries often look like:

        melanoma, 35, 48, 92
        biopsy, 12-14
    """

    lowered = text.lower()

    if "index" not in lowered[:150]:
        return False

    index_patterns = re.findall(
        r"\b[a-zA-Z][a-zA-Z\s\-']+,\s*\d+(?:[-–]\d+)?",
        text,
    )

    return len(index_patterns) >= 5


def looks_like_front_matter(text: str) -> bool:
    """
    Detect copyright/publisher/front-matter pages.
    """

    cleaned = text.strip()

    if len(cleaned) < 150:
        return True

    lowered = cleaned.lower()

    front_matter_terms = [
        "copyright",
        "all rights reserved",
        "isbn",
        "published by",
        "library of congress",
    ]

    matches = sum(
        term in lowered
        for term in front_matter_terms
    )

    return matches >= 2


def should_skip_page(text: str) -> tuple[bool, str]:
    """
    Decide whether an entire page should be excluded.

    Returns:

        (True, reason)

    or:

        (False, "")
    """

    if not text.strip():
        return True, "empty"

    if looks_like_front_matter(text):
        return True, "front_matter"

    if looks_like_table_of_contents(text):
        return True, "table_of_contents"

    if looks_like_references(text):
        return True, "references"

    if looks_like_index(text):
        return True, "index"

    return False, ""


# ============================================================
# SECTION DETECTION
# ============================================================

def clean_section_title(line: str) -> str:
    """
    Clean a possible section/chapter heading.
    """

    line = line.strip()

    # Remove long sequences of dots often found in TOCs.
    line = re.sub(r"\.{2,}", " ", line)

    # Remove trailing page numbers.
    line = re.sub(
        r"\s+\d+(?:[-–]\d+)?$",
        "",
        line,
    )

    # Collapse whitespace.
    line = re.sub(r"\s+", " ", line)

    return line.strip()


def detect_section(text: str) -> str:
    """
    Try to identify a meaningful section heading.

    We deliberately avoid treating arbitrary first lines as
    section names.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines[:12]:

        if len(line) < 4:
            continue

        if len(line) > 120:
            continue

        cleaned = clean_section_title(line)

        # Chapter heading.
        if re.match(
            r"^(chapter|section|part)\s+",
            cleaned,
            flags=re.IGNORECASE,
        ):
            return cleaned

        # Numbered heading such as:
        # 1. Melanoma
        # 2.1 Diagnosis
        if re.match(
            r"^\d+(\.\d+)*\.?\s+[A-Z]",
            cleaned,
        ):
            return cleaned

        # Uppercase heading.
        letters = [
            char
            for char in cleaned
            if char.isalpha()
        ]

        if letters:
            uppercase_ratio = (
                sum(char.isupper() for char in letters)
                / len(letters)
            )

            if uppercase_ratio > 0.85:
                return cleaned

    return "Unknown"


# ============================================================
# SENTENCE SPLITTING
# ============================================================

def split_into_sentences(text: str) -> list[str]:
    """
    Split text into approximate sentences.

    This is intentionally lightweight. We are not using an
    external NLP package yet.
    """

    text = clean_text(text)

    if not text:
        return []

    protected = {
        "e.g.": "e<PERIOD>g<PERIOD>",
        "i.e.": "i<PERIOD>e<PERIOD>",
        "Fig.": "Fig<PERIOD>",
        "Dr.": "Dr<PERIOD>",
        "vs.": "vs<PERIOD>",
        "etc.": "etc<PERIOD>",
    }

    for original, replacement in protected.items():
        text = text.replace(
            original,
            replacement,
        )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text,
    )

    restored = []

    for sentence in sentences:

        sentence = sentence.strip()

        for original, replacement in protected.items():
            sentence = sentence.replace(
                replacement,
                original,
            )

        if sentence:
            restored.append(sentence)

    return restored


# ============================================================
# CHUNK BUILDING
# ============================================================

def build_chunks_from_sentences(
    sentences: list[str],
    document: str,
    page_number: int,
    section: str,
) -> list[dict[str, Any]]:

    chunks = []

    current_sentences: list[str] = []
    current_size = 0

    def save_chunk() -> None:
        nonlocal current_sentences
        nonlocal current_size

        if not current_sentences:
            return

        chunk_text = " ".join(
            current_sentences
        ).strip()

        if len(chunk_text) >= MIN_CHUNK_SIZE:

            chunks.append(
                {
                    "document": document,
                    "page_start": page_number,
                    "page_end": page_number,
                    "section": section,
                    "text": chunk_text,
                }
            )

        current_sentences = []
        current_size = 0

    for sentence in sentences:

        sentence_size = len(sentence)

        # Handle exceptionally long sentences.
        if sentence_size > MAX_CHUNK_SIZE:

            words = sentence.split()

            current_words = []

            for word in words:

                proposed = " ".join(
                    current_words + [word]
                )

                if (
                    current_words
                    and len(proposed) > MAX_CHUNK_SIZE
                ):
                    current_sentences.append(
                        " ".join(current_words)
                    )

                    current_size += len(
                        current_sentences[-1]
                    )

                    save_chunk()

                    current_words = []

                current_words.append(word)

            if current_words:
                sentence = " ".join(current_words)
                sentence_size = len(sentence)

        # If adding this sentence would exceed the
        # maximum, save the current chunk first.
        if (
            current_sentences
            and current_size + sentence_size + 1
            > MAX_CHUNK_SIZE
        ):
            save_chunk()

        current_sentences.append(sentence)

        current_size += sentence_size + 1

        # Once we reach the target size, finish the chunk.
        if current_size >= TARGET_CHUNK_SIZE:
            save_chunk()

    save_chunk()

    return chunks


# ============================================================
# PAGE → CHUNKS
# ============================================================

def create_chunks_for_page(
    page: dict[str, Any],
) -> tuple[list[dict[str, Any]], str | None]:

    document = page["document"]
    page_number = page["page"]

    text = clean_text(
        page["text"]
    )

    text = remove_standalone_page_numbers(
        text
    )

    should_skip, reason = should_skip_page(
        text
    )

    if should_skip:
        return [], reason

    section = detect_section(text)

    sentences = split_into_sentences(
        text
    )

    chunks = build_chunks_from_sentences(
        sentences=sentences,
        document=document,
        page_number=page_number,
        section=section,
    )

    return chunks, None


# ============================================================
# METADATA
# ============================================================

def infer_document_year(document: str) -> int | None:
    """
    Infer publication year from the current faculty PDF names.

    Later this will be replaced by a document registry so
    filenames do not determine metadata.
    """

    year_match = re.search(
        r"(19|20)\d{2}",
        document,
    )

    if year_match:
        return int(year_match.group())

    return None


def add_chunk_metadata(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):

        document = chunk["document"]

        safe_document = re.sub(
            r"[^a-zA-Z0-9]+",
            "-",
            document,
        ).strip("-")

        chunk["chunk_id"] = (
            f"{safe_document}"
            f"-p{chunk['page_start']}"
            f"-c{index}"
        )

        chunk["source_type"] = "FACULTY_KB"

        chunk["source_year"] = (
            infer_document_year(document)
        )

        chunk["source_id"] = safe_document

    return chunks


# ============================================================
# SAVE CHUNKS
# ============================================================

def save_chunks_jsonl(
    chunks: list[dict[str, Any]],
) -> None:

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        for chunk in chunks:

            file.write(
                json.dumps(
                    chunk,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(
        f"Saved chunks to: {OUTPUT_FILE}"
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def chunk_pages(
    pages: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    dict[str, int],
]:

    all_chunks = []

    skipped_pages = {
        "empty": 0,
        "front_matter": 0,
        "table_of_contents": 0,
        "references": 0,
        "index": 0,
    }

    for page in pages:

        page_chunks, skip_reason = (
            create_chunks_for_page(page)
        )

        if skip_reason:
            skipped_pages[skip_reason] += 1

        all_chunks.extend(
            page_chunks
        )

    all_chunks = add_chunk_metadata(
        all_chunks
    )

    return all_chunks, skipped_pages


# ============================================================
# TEST / CLI
# ============================================================

if __name__ == "__main__":

    from backend.rag.pdf_loader import (
        load_all_pdfs,
    )

    print()
    print("Loading PDFs...")
    print()

    pages = load_all_pdfs()

    print()
    print("Creating V3 chunks...")
    print()

    chunks, skipped_pages = chunk_pages(
        pages
    )

    print()
    print("=" * 70)
    print("CHUNKER V3 TEST")
    print("=" * 70)

    print(
        f"Pages loaded:   {len(pages)}"
    )

    print(
        f"Chunks created:  {len(chunks)}"
    )

    print()
    print("SKIPPED PAGES")
    print("-" * 70)

    for reason, count in skipped_pages.items():
        print(
            f"{reason:20} {count}"
        )

    if chunks:

        sizes = [
            len(chunk["text"])
            for chunk in chunks
        ]

        print()
        print("TEXT SIZE")
        print("-" * 70)

        print(
            f"Smallest: {min(sizes)} characters"
        )

        print(
            f"Largest:  {max(sizes)} characters"
        )

        print(
            f"Average:  "
            f"{sum(sizes) / len(sizes):.0f} characters"
        )

        print()
        print("FIRST CHUNK")
        print("-" * 70)

        first = chunks[0]

        print(
            f"Chunk ID: {first['chunk_id']}"
        )

        print(
            f"Document: {first['document']}"
        )

        print(
            f"Page: {first['page_start']}"
        )

        print(
            f"Section: {first['section']}"
        )

        print(
            f"Source type: {first['source_type']}"
        )

        print(
            f"Source year: {first['source_year']}"
        )

        print()

        print(
            first["text"][:1500]
        )

        print()
        print("LAST CHUNK")
        print("-" * 70)

        last = chunks[-1]

        print(
            f"Chunk ID: {last['chunk_id']}"
        )

        print(
            f"Document: {last['document']}"
        )

        print(
            f"Page: {last['page_start']}"
        )

        print(
            f"Section: {last['section']}"
        )

        print(
            f"Source type: {last['source_type']}"
        )

        print(
            f"Source year: {last['source_year']}"
        )

        print()

        print(
            last["text"][:1500]
        )

        # Save final chunks.
        save_chunks_jsonl(chunks)

    else:

        print()
        print("No chunks were created.")