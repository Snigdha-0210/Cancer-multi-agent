from pathlib import Path
import json
import re
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "clean_chunks.jsonl"


# ============================================================================
# FILE I/O
# ============================================================================

def load_chunks() -> list[dict]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    chunks = []

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                chunks.append(json.loads(line))

    return chunks


def save_chunks(chunks: list[dict]) -> None:
    OUTPUT_FILE.parent.mkdir(
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


# ============================================================================
# TEXT NORMALIZATION
# ============================================================================

def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================================
# ACKNOWLEDGMENTS
# ============================================================================

def looks_like_acknowledgment(text: str) -> bool:

    lower = text.lower()

    patterns = [
        r"\backnowledg(e)?ments?\b",
        r"\bwe thank\b",
        r"\bthe authors thank\b",
        r"\bgrateful to\b",
    ]

    return any(
        re.search(pattern, lower)
        for pattern in patterns
    )


# ============================================================================
# COPYRIGHT
# ============================================================================

def looks_like_copyright(text: str) -> bool:

    lower = text.lower()

    patterns = [
        r"all rights reserved",
        r"copyright\s+\d{4}",
        r"©\s*\d{4}",
    ]

    matches = sum(
        bool(
            re.search(
                pattern,
                lower,
            )
        )
        for pattern in patterns
    )

    return matches >= 2


# ============================================================================
# INDEX
# ============================================================================

def looks_like_index(text: str) -> bool:

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) < 3:
        return False

    lower = text.lower()

    index_word_count = len(
        re.findall(
            r"\b(?:index|see also)\b",
            lower,
        )
    )

    page_number_count = len(
        re.findall(
            r"\b\d{1,3}\b",
            text,
        )
    )

    short_lines = sum(
        len(line) < 80
        for line in lines
    )

    return (
        index_word_count >= 2
        and short_lines >= len(lines) * 0.5
        and page_number_count >= len(lines) * 0.4
    )


# ============================================================================
# TABLE OF CONTENTS
# ============================================================================

def looks_like_table_of_contents(text: str) -> bool:

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) < 5:
        return False

    toc_signals = 0

    for line in lines:

        if re.search(
            r"\.{3,}\s*\d+$",
            line,
        ):
            toc_signals += 1

        elif re.search(
            r"\bcontents\b",
            line,
            re.IGNORECASE,
        ):
            toc_signals += 1

        elif re.search(
            r"\bchapter\s+\d+\b",
            line,
            re.IGNORECASE,
        ):
            toc_signals += 1

    return toc_signals >= 3


# ============================================================================
# CONTRIBUTOR / AUTHOR PAGE DETECTION
# ============================================================================

def looks_like_contributors(text: str) -> bool:

    lower = text.lower()

    institutional_terms = [
        "department of",
        "division of",
        "school of medicine",
        "medical center",
        "university",
        "institute",
        "hospital",
        "clinic",
        "faculty of",
        "medical school",
    ]

    degree_patterns = [
        r"\bMD\b",
        r"\bPhD\b",
        r"\bMPH\b",
        r"\bMBBS\b",
        r"\bDO\b",
        r"\bRN\b",
        r"\bMS\b",
        r"\bMSc\b",
    ]

    institution_count = sum(
        lower.count(term)
        for term in institutional_terms
    )

    degree_count = sum(
        len(
            re.findall(
                pattern,
                text,
            )
        )
        for pattern in degree_patterns
    )

    if institution_count >= 5 and degree_count >= 5:
        return True

    if institution_count >= 4 and degree_count >= 8:
        return True

    if degree_count >= 8 and institution_count >= 3:
        return True

    return False


# ============================================================================
# NUMBERED REFERENCE LIST DETECTION
# ============================================================================

def looks_like_numbered_reference_list(
    text: str,
) -> bool:
    """
    Detects chunks that are predominantly numbered bibliography entries.

    This is intentionally conservative.

    It should remove:

        140. Ye JN, Rhew DC, Yip F...
        141. ...
        142. ...
        143. ...

    but preserve normal medical prose such as:

        Singluff et al. reviewed 185 patients with ALM...
    """

    reference_starts = re.findall(
        r"(?:^|\s)"
        r"\d{1,3}\.\s+"
        r"[A-Z][A-Za-z'’-]+",
        text,
    )

    # A small number of numbered citations is not enough.
    if len(reference_starts) < 5:
        return False

    journal_patterns = [
        r"\b(?:19|20)\d{2}\b\s*;\s*\d+\s*:",
        r"\b\d+\s*\(\s*\d+\s*\)\s*:\s*\d+",
        r"\bet al\.",
        r"\bdoi\b",
    ]

    journal_signals = sum(
        len(
            re.findall(
                pattern,
                text,
                re.IGNORECASE,
            )
        )
        for pattern in journal_patterns
    )

    # Five or more numbered references plus
    # multiple bibliography signals.
    if len(reference_starts) >= 5 and journal_signals >= 4:
        return True

    # A very large number of numbered references
    # is strong evidence of a bibliography.
    if len(reference_starts) >= 8:
        return True

    return False


# ============================================================================
# REFERENCE / BIBLIOGRAPHY DETECTION
# ============================================================================

def looks_like_reference_chunk(
    text: str,
) -> bool:
    """
    Removes only chunks that are strongly identifiable
    as bibliography/reference lists.

    Ordinary medical prose containing citations should remain.
    """

    # ------------------------------------------------------------
    # 1. Numbered bibliography
    # ------------------------------------------------------------

    if looks_like_numbered_reference_list(text):
        return True

    # ------------------------------------------------------------
    # 2. Look for repeated numbered references
    # ------------------------------------------------------------

    numbered_references = re.findall(
        r"(?:^|\s)"
        r"\d{1,3}\.\s+"
        r"[A-Z][A-Za-z'’-]+",
        text,
    )

    # Three or four numbered entries alone are NOT enough.
    # They need strong bibliography evidence.
    if len(numbered_references) >= 3:

        bibliography_signals = 0

        bibliography_signals += len(
            re.findall(
                r"\b(?:19|20)\d{2}\b\s*;\s*\d+\s*:",
                text,
            )
        )

        bibliography_signals += len(
            re.findall(
                r"\b\d+\s*\(\s*\d+\s*\)\s*:\s*\d+",
                text,
            )
        )

        bibliography_signals += len(
            re.findall(
                r"\bet al\.",
                text,
                re.IGNORECASE,
            )
        )

        bibliography_signals += len(
            re.findall(
                r"\bdoi\s*:\s*10\.",
                text,
                re.IGNORECASE,
            )
        )

        # Require substantial bibliography density.
        if (
            len(numbered_references) >= 4
            and bibliography_signals >= 5
        ):
            return True

    # ------------------------------------------------------------
    # 3. Repeated year + journal structures
    #
    # Example:
    #
    # 2006;154(2):375–6.
    # 2005;32(8):632–7.
    # 2003;42(6):575–9.
    #
    # This is useful when PDF extraction collapses
    # references into a single paragraph.
    # ------------------------------------------------------------

    year_journal_patterns = re.findall(
        r"\b(?:19|20)\d{2}\b"
        r"\s*;\s*"
        r"\d+"
        r"\s*(?:\(\s*\d+\s*\))?"
        r"\s*:\s*\d+",
        text,
    )

    # Three or more repeated journal records strongly
    # suggests bibliography material.
    if len(year_journal_patterns) >= 3:

        # Make sure the chunk also contains several
        # author-like/reference signals.
        author_signals = len(
            re.findall(
                r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+[A-Z][A-Za-z.-]+",
                text,
            )
        )

        if author_signals >= 3:
            return True

    # ------------------------------------------------------------
    # 4. Multiple DOI records
    #
    # Multiple DOI entries in one chunk are extremely
    # unlikely to represent ordinary medical prose.
    # ------------------------------------------------------------

    doi_count = len(
        re.findall(
            r"\bdoi\s*:\s*10\.\d{4,9}/",
            text,
            re.IGNORECASE,
        )
    )

    if doi_count >= 2:
        return True

    # ------------------------------------------------------------
    # 5. Multiple "Available from" / URL records
    #
    # Only trigger when there are several.
    # A single URL can occur in legitimate chapter prose.
    # ------------------------------------------------------------

    available_from_count = len(
        re.findall(
            r"\bavailable\s+from\b",
            text,
            re.IGNORECASE,
        )
    )

    url_count = len(
        re.findall(
            r"https?://|www\.",
            text,
            re.IGNORECASE,
        )
    )

    if (
        available_from_count >= 3
        and url_count >= 2
    ):
        return True

    return False


# ============================================================================
# LOW INFORMATION
# ============================================================================

def looks_like_low_information(
    text: str,
) -> bool:

    cleaned = normalize_text(text)

    if len(cleaned) < 300:
        return True

    words = cleaned.split()

    if len(words) < 45:
        return True

    return False


# ============================================================================
# CLASSIFICATION
# ============================================================================

def classify_chunk(
    chunk: dict,
) -> str | None:

    text = normalize_text(
        chunk.get(
            "text",
            "",
        )
    )

    if not text:
        return "empty"

    if looks_like_acknowledgment(text):
        return "acknowledgments"

    if looks_like_index(text):
        return "index"

    if looks_like_table_of_contents(text):
        return "table_of_contents"

    if looks_like_contributors(text):
        return "contributors"

    if looks_like_reference_chunk(text):
        return "references"

    if looks_like_copyright(text):
        return "copyright"

    if looks_like_low_information(text):
        return "low_information"

    return None


# ============================================================================
# FILTER
# ============================================================================

def filter_chunks(
    chunks: list[dict],
) -> tuple[list[dict], Counter]:

    kept = []

    removed_reasons = Counter()

    for chunk in chunks:

        reason = classify_chunk(chunk)

        if reason is not None:

            removed_reasons[reason] += 1

            continue

        chunk["text"] = normalize_text(
            chunk["text"]
        )

        kept.append(chunk)

    return (
        kept,
        removed_reasons,
    )


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:

    chunks = load_chunks()

    print()
    print("=" * 70)
    print("CONTENT FILTER V6")
    print("=" * 70)

    print(
        f"Input chunks: {len(chunks)}"
    )

    clean_chunks, removed_reasons = filter_chunks(
        chunks
    )

    print(
        f"Kept chunks: {len(clean_chunks)}"
    )

    print(
        f"Removed chunks: "
        f"{len(chunks) - len(clean_chunks)}"
    )

    print()
    print("REMOVAL REASONS")
    print("-" * 70)

    if removed_reasons:

        for reason, count in (
            removed_reasons.most_common()
        ):

            print(
                f"{reason:<22} {count}"
            )

    else:

        print(
            "No chunks removed."
        )

    save_chunks(
        clean_chunks
    )

    print()
    print("=" * 70)
    print("OUTPUT")
    print("=" * 70)

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    if clean_chunks:

        first = clean_chunks[0]

        print()
        print("FIRST CLEAN CHUNK")
        print("-" * 70)

        print(
            f"Chunk ID:      "
            f"{first.get('chunk_id')}"
        )

        print(
            f"Document:      "
            f"{first.get('document')}"
        )

        print(
            f"Page start:    "
            f"{first.get('page_start')}"
        )

        print(
            f"Page end:      "
            f"{first.get('page_end')}"
        )

        print(
            f"Section:       "
            f"{first.get('section')}"
        )

        print(
            f"Source type:   "
            f"{first.get('source_type')}"
        )

        print(
            f"Source year:   "
            f"{first.get('source_year')}"
        )

        print()

        print(
            first.get(
                "text",
                "",
            )[:1200]
        )


if __name__ == "__main__":
    main()