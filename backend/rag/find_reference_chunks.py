from pathlib import Path
import json
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clean_chunks.jsonl"
)


def looks_reference_like(text: str) -> bool:
    signals = 0

    # DOI
    doi_count = len(
        re.findall(
            r"\bdoi\s*:\s*10\.\d{4,9}/",
            text,
            re.IGNORECASE,
        )
    )

    if doi_count >= 1:
        signals += 3

    # Journal-style year/volume/pages
    journal_patterns = len(
        re.findall(
            r"\b(?:19|20)\d{2}\b\s*;\s*\d+\s*:",
            text,
        )
    )

    if journal_patterns >= 1:
        signals += 2

    # et al.
    et_al_count = len(
        re.findall(
            r"\bet al\.",
            text,
            re.IGNORECASE,
        )
    )

    if et_al_count >= 2:
        signals += 2

    # PubMed / PMID
    pubmed_count = len(
        re.findall(
            r"\b(?:pubmed|pmid)\b",
            text,
            re.IGNORECASE,
        )
    )

    if pubmed_count >= 1:
        signals += 2

    # Multiple year occurrences
    year_count = len(
        re.findall(
            r"\b(?:19|20)\d{2}\b",
            text,
        )
    )

    if year_count >= 4:
        signals += 2

    return signals >= 4


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    matches = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            if not line.strip():
                continue

            chunk = json.loads(line)

            text = chunk.get("text", "")

            if looks_reference_like(text):
                matches.append(chunk)

    print()
    print("=" * 70)
    print("REFERENCE-LIKE CHUNK INSPECTION")
    print("=" * 70)

    print(f"Total clean chunks: {sum(1 for _ in INPUT_FILE.open(encoding='utf-8'))}")
    print(f"Reference-like candidates: {len(matches)}")

    print()

    for index, chunk in enumerate(matches[:20], start=1):

        print("=" * 70)
        print(f"CANDIDATE #{index}")
        print("=" * 70)

        print(
            f"Chunk ID: {chunk.get('chunk_id')}"
        )

        print(
            f"Document: {chunk.get('document')}"
        )

        print(
            f"Page: "
            f"{chunk.get('page_start')}"
            f"-"
            f"{chunk.get('page_end')}"
        )

        print(
            f"Section: {chunk.get('section')}"
        )

        print()

        print(
            chunk.get("text", "")[:1800]
        )

        print()


if __name__ == "__main__":
    main()