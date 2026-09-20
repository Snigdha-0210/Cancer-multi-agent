import re
from typing import Any


# ---------------------------------------------------------
# Chunk configuration
# ---------------------------------------------------------

TARGET_CHUNK_SIZE = 1400
MAX_CHUNK_SIZE = 2200
MIN_CHUNK_SIZE = 300


# ---------------------------------------------------------
# Basic text cleaning
# ---------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Clean PDF-extracted text while preserving useful sentence
    and paragraph boundaries.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove repeated spaces/tabs.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_standalone_page_numbers(text: str) -> str:
    """
    Remove lines that contain only a page number.

    PDF extraction frequently places printed page numbers
    inside the extracted text.
    """

    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        if re.fullmatch(r"\d{1,4}", stripped):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# ---------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------

def split_into_sentences(text: str) -> list[str]:
    """
    Split text into reasonably sized sentences.

    This is intentionally simple and deterministic. We will
    later evaluate whether an LLM-based semantic chunker
    improves retrieval.
    """

    text = clean_text(text)

    if not text:
        return []

    # Protect common medical abbreviations from being split.
    protected = {
        "e.g.": "e<PERIOD>g<PERIOD>",
        "i.e.": "i<PERIOD>e<PERIOD>",
        "Fig.": "Fig<PERIOD>",
        "Dr.": "Dr<PERIOD>",
        "vs.": "vs<PERIOD>",
        "etc.": "etc<PERIOD>",
    }

    for original, replacement in protected.items():
        text = text.replace(original, replacement)

    # Treat line breaks as spaces.
    text = re.sub(r"\s+", " ", text).strip()

    # Split after sentence-ending punctuation.
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


# ---------------------------------------------------------
# Detect likely non-knowledge pages
# ---------------------------------------------------------

def looks_like_index(text: str) -> bool:
    """
    Detect obvious index pages.

    We don't want an index entry such as:
        Melanoma, 79-103

    to become a medical knowledge chunk.
    """

    lowered = text.lower()

    if "index" in lowered[:150]:
        # Count patterns that look like index entries.
        index_patterns = re.findall(
            r"\b[a-zA-Z][a-zA-Z\s\-']+,\s*\d+(?:[-–]\d+)?",
            text,
        )

        if len(index_patterns) >= 5:
            return True

    return False


def looks_like_front_matter(text: str) -> bool:
    """
    Detect very short title/copyright/front-matter pages.
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


# ---------------------------------------------------------
# Heading detection
# ---------------------------------------------------------

def detect_section(text: str) -> str:
    """
    Try to identify a section heading from the beginning
    of the page.

    This is deliberately conservative.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines[:8]:

        if len(line) < 120 and len(line) > 3:

            # Chapter / section style.
            if re.match(
                r"^(chapter|section|part)\s+",
                line,
                flags=re.IGNORECASE,
            ):
                return line

            # Numbered heading.
            if re.match(
                r"^\d+(\.\d+)*\.?\s+[A-Z]",
                line,
            ):
                return line

            # Mostly uppercase heading.
            letters = [
                char
                for char in line
                if char.isalpha()
            ]

            if letters:
                uppercase_ratio = (
                    sum(char.isupper() for char in letters)
                    / len(letters)
                )

                if (
                    uppercase_ratio > 0.85
                    and len(line) < 100
                ):
                    return line

    return "Unknown"


# ---------------------------------------------------------
# Chunk creation
# ---------------------------------------------------------

def build_chunks_from_sentences(
    sentences: list[str],
    document: str,
    page_number: int,
    section: str,
) -> list[dict[str, Any]]:

    chunks = []

    current_sentences: list[str] = []
    current_size = 0

    def save_chunk():
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

        # Extremely long sentence.
        # We have no good semantic boundary, so split it
        # conservatively by words.
        if sentence_size > MAX_CHUNK_SIZE:

            words = sentence.split()

            current_words = []

            for word in words:

                proposed = (
                    " ".join(current_words + [word])
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

        # Would exceed maximum?
        if (
            current_sentences
            and current_size + sentence_size + 1
            > MAX_CHUNK_SIZE
        ):
            save_chunk()

        current_sentences.append(sentence)
        current_size += sentence_size + 1

        # Reach our target.
        if current_size >= TARGET_CHUNK_SIZE:
            save_chunk()

    save_chunk()

    return chunks


# ---------------------------------------------------------
# Process one page
# ---------------------------------------------------------

def create_chunks_for_page(
    page: dict[str, Any],
) -> list[dict[str, Any]]:

    document = page["document"]
    page_number = page["page"]

    text = clean_text(page["text"])

    text = remove_standalone_page_numbers(text)

    if not text:
        return []

    # Skip obvious index pages.
    if looks_like_index(text):
        return []

    # Skip very short front matter.
    if looks_like_front_matter(text):
        return []

    section = detect_section(text)

    sentences = split_into_sentences(text)

    return build_chunks_from_sentences(
        sentences=sentences,
        document=document,
        page_number=page_number,
        section=section,
    )


# ---------------------------------------------------------
# Add deterministic chunk IDs
# ---------------------------------------------------------

def add_chunk_ids(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):

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


# ---------------------------------------------------------
# Main chunking function
# ---------------------------------------------------------

def chunk_pages(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    all_chunks = []

    for page in pages:

        page_chunks = create_chunks_for_page(page)

        all_chunks.extend(page_chunks)

    return add_chunk_ids(all_chunks)


# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    from backend.rag.pdf_loader import load_all_pdfs

    print("Loading PDFs...")
    pages = load_all_pdfs()

    print()
    print("Creating V2 chunks...")

    chunks = chunk_pages(pages)

    print()
    print("=" * 70)
    print("CHUNKER V2 TEST")
    print("=" * 70)

    print(f"Pages loaded:  {len(pages)}")
    print(f"Chunks created: {len(chunks)}")

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
        print()
        print(first["text"][:1500])

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
        print()
        print(last["text"][:1500])