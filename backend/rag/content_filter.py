from pathlib import Path
import json
import re
from collections import Counter
from typing import Any


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.jsonl"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clean_chunks.jsonl"
)


# ============================================================
# BASIC TEXT HELPERS
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize whitespace without destroying paragraph structure.
    """

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


# ============================================================
# CONTRIBUTORS / FRONT MATTER
# ============================================================

def looks_like_contributor_chunk(text: str) -> bool:
    """
    Detect contributor/author biography and affiliation pages.

    We intentionally use multiple signals because contributor
    pages may continue onto pages that no longer contain the
    word 'contributors'.
    """

    lower = text.lower()
    words = word_count(text)

    institutional_terms = [
        "department of",
        "division of",
        "medical center",
        "school of medicine",
        "university",
        "college of medicine",
        "hospital",
        "faculty of",
    ]

    institutional_count = sum(
        1 for term in institutional_terms
        if term in lower
    )

    author_degree_count = len(
        re.findall(
            r"\b(?:md|do|phd|mph|rn|msc|ms|mbbs)\b",
            text,
            flags=re.IGNORECASE,
        )
    )

    # Strong signal:
    # many institutional affiliations + medical degrees
    if institutional_count >= 4 and author_degree_count >= 4:
        return True

    # Contributor continuation pages often have many names,
    # affiliations and very little normal prose.
    capitalized_name_pattern = re.findall(
        r"\b[A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+\b",
        text,
    )

    if (
        institutional_count >= 5
        and len(capitalized_name_pattern) >= 5
        and words < 700
    ):
        return True

    return False


# ============================================================
# ACKNOWLEDGMENTS
# ============================================================

def looks_like_acknowledgment_chunk(text: str) -> bool:
    lower = text.lower()

    acknowledgment_terms = [
        "acknowledgment",
        "acknowledgements",
        "acknowledgments",
        "we thank",
        "the authors thank",
        "special thanks",
    ]

    return any(term in lower[:700] for term in acknowledgment_terms)


# ============================================================
# COPYRIGHT / PUBLISHER MATERIAL
# ============================================================

def looks_like_copyright_chunk(text: str) -> bool:
    lower = text.lower()

    signals = [
        "all rights reserved",
        "copyright",
        "springer international publishing",
        "elsevier",
        "humana press",
        "isbn",
        "no part of this publication",
    ]

    signal_count = sum(
        1 for signal in signals
        if signal in lower
    )

    return signal_count >= 2 and word_count(text) < 300


# ============================================================
# INDEX
# ============================================================

def looks_like_index_chunk(text: str) -> bool:
    lower = text.lower()

    if not lower.startswith("index"):
        return False

    page_number_patterns = re.findall(
        r"\b[A-Za-z][A-Za-z\s-]{2,40}\s+\d{1,3}\b",
        text,
    )

    return len(page_number_patterns) >= 4


# ============================================================
# REFERENCES
# ============================================================

def looks_like_reference_chunk(text: str) -> bool:
    """
    Conservative reference detection.

    We do NOT remove normal medical prose merely because it
    contains citations or years.
    """

    stripped = text.strip()
    lower = stripped.lower()

    # Explicit references heading
    if re.match(
        r"^(references|bibliography|selected references)\b",
        lower,
    ):
        return word_count(text) < 1800

    # Numbered reference-heavy block
    numbered_entries = re.findall(
        r"(?:^|\n)\s*\d{1,3}[\.\)]\s+[A-Z][^\n]{20,}",
        text,
    )

    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        text,
    )

    doi_count = len(
        re.findall(
            r"\bdoi\b|10\.\d{4,9}/",
            lower,
        )
    )

    if (
        len(numbered_entries) >= 6
        and len(years) >= 4
    ):
        return True

    if (
        doi_count >= 3
        and len(years) >= 3
    ):
        return True

    return False


# ============================================================
# TABLE OF CONTENTS
# ============================================================

def looks_like_toc_chunk(text: str) -> bool:
    lower = text.lower()

    if re.match(
        r"^(table of contents|contents)\b",
        lower,
    ):
        return True

    toc_patterns = re.findall(
        r"(?m)^[^\n]{3,100}\s+\.{2,}\s*\d{1,3}\s*$",
        text,
    )

    return len(toc_patterns) >= 5


# ============================================================
# LOW INFORMATION CONTENT
# ============================================================

def content_quality_score(text: str) -> int:
    """
    Gives a rough score to help identify extremely low-value
    chunks without aggressively removing legitimate medical text.
    """

    score = 0

    words = word_count(text)

    if words >= 100:
        score += 2

    if words >= 250:
        score += 1

    # Normal sentence structure
    sentence_count = len(
        re.findall(
            r"[.!?](?:\s|$)",
            text,
        )
    )

    if sentence_count >= 3:
        score += 2

    if sentence_count >= 8:
        score += 1

    # Medical terminology is a positive signal
    medical_terms = [
        "patient",
        "diagnosis",
        "treatment",
        "tumor",
        "cancer",
        "melanoma",
        "carcinoma",
        "lesion",
        "biopsy",
        "therapy",
        "clinical",
        "pathology",
    ]

    medical_hits = sum(
        1 for term in medical_terms
        if term in text.lower()
    )

    if medical_hits >= 2:
        score += 2

    return score


# ============================================================
# MAIN FILTER
# ============================================================

def should_keep_chunk(chunk: dict[str, Any]) -> tuple[bool, str]:

    text = normalize_text(
        chunk.get("text", "")
    )

    if not text:
        return False, "empty"

    words = word_count(text)

    if words < 25:
        return False, "too_short"

    if looks_like_contributor_chunk(text):
        return False, "contributors"

    if looks_like_acknowledgment_chunk(text):
        return False, "acknowledgments"

    if looks_like_copyright_chunk(text):
        return False, "copyright"

    if looks_like_index_chunk(text):
        return False, "index"

    if looks_like_reference_chunk(text):
        return False, "references"

    if looks_like_toc_chunk(text):
        return False, "table_of_contents"

    # Only remove extremely weak chunks.
    # We deliberately keep this threshold conservative.
    if words < 50 and content_quality_score(text) <= 1:
        return False, "low_information"

    return True, "kept"


# ============================================================
# LOAD / SAVE
# ============================================================

def load_chunks() -> list[dict[str, Any]]:
    chunks = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            chunks.append(json.loads(line))

    return chunks


def save_chunks(chunks: list[dict[str, Any]]) -> None:

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


# ============================================================
# MAIN
# ============================================================

def main():

    chunks = load_chunks()

    kept_chunks = []
    removal_reasons = Counter()

    for chunk in chunks:

        keep, reason = should_keep_chunk(chunk)

        if keep:
            kept_chunks.append(chunk)
        else:
            removal_reasons[reason] += 1

    save_chunks(kept_chunks)

    print()
    print("=" * 70)
    print("CONTENT FILTER V3")
    print("=" * 70)

    print(f"Input chunks: {len(chunks)}")
    print()

    print("FILTER RESULTS")
    print("-" * 70)

    print(f"Kept chunks:    {len(kept_chunks)}")
    print(f"Removed chunks: {len(chunks) - len(kept_chunks)}")

    print()

    print("REMOVAL REASONS")
    print("-" * 70)

    for reason, count in sorted(
        removal_reasons.items()
    ):
        print(
            f"{reason:<22} {count}"
        )

    print()

    print("OUTPUT")
    print("-" * 70)

    print(OUTPUT_FILE)

    if kept_chunks:

        first = kept_chunks[0]

        print()

        print("FIRST CLEAN CHUNK")
        print("-" * 70)

        print(
            f"Chunk ID:     "
            f"{first.get('chunk_id')}"
        )

        print(
            f"Document:     "
            f"{first.get('document')}"
        )

        print(
            f"Page start:   "
            f"{first.get('page_start')}"
        )

        print(
            f"Page end:     "
            f"{first.get('page_end')}"
        )

        print(
            f"Section:      "
            f"{first.get('section')}"
        )

        print(
            f"Source type:  "
            f"{first.get('source_type')}"
        )

        print(
            f"Source year:  "
            f"{first.get('source_year')}"
        )

        print()

        print(first.get("text", "")[:2500])


if __name__ == "__main__":
    main()