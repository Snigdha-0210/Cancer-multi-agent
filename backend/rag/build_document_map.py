from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from pypdf import PdfReader


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PATIENT_GUIDELINES_DIR = (
    PROJECT_ROOT / "data" / "source_documents" / "patient_guidelines"
)

ONCOLOGY_REFERENCES_DIR = (
    PROJECT_ROOT / "data" / "source_documents" / "oncology_references"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "document_map"
OUTPUT_FILE = OUTPUT_DIR / "document_map.json"


# ============================================================
# DOCUMENT TYPES
# ============================================================

PATIENT_GUIDELINE = "patient_guideline"
ONCOLOGY_REFERENCE = "oncology_reference"


# ============================================================
# PATTERNS
# ============================================================

# Examples:
# Chapter 1
# Chapter 2
# CHAPTER 3
CHAPTER_PATTERN = re.compile(
    r"^\s*Chapter\s+(\d+)\s*$",
    re.IGNORECASE,
)


# Running headers such as:
#
# 2 Chapter 1 Noninvasive Breast Cancer
# 3Chapter 1 Noninvasive Breast Cancer
#
# These are NOT sections.
RUNNING_HEADER_PATTERN = re.compile(
    r"^\s*\d+\s*Chapter\s+\d+\b",
    re.IGNORECASE,
)


# Page number + chapter header where spacing may be strange.
PAGE_CHAPTER_HEADER_PATTERN = re.compile(
    r"^\s*\d+\s*Chapter\s+\d+\s+.+$",
    re.IGNORECASE,
)


# NCCN-style sections:
#
# 1 About adrenal tumors
# 2 Testing for adrenal tumors
#
# We intentionally require a reasonably short heading.
NUMBERED_SECTION_PATTERN = re.compile(
    r"^\s*(\d+)\s+([A-Za-z][A-Za-z0-9 ,:;()'&/\-]{2,120})\s*$"
)


# Subsections commonly found in textbooks:
#
# 1.1 Epidemiology
# 2.3 Treatment
#
# We keep these separate from the simple numbered sections.
SUBSECTION_PATTERN = re.compile(
    r"^\s*(\d+\.\d+(?:\.\d+)*)\s+([A-Za-z][A-Za-z0-9 ,:;()'&/\-]{2,120})\s*$"
)


# ============================================================
# NOISE
# ============================================================

NOISE_EXACT = {
    "NATIONAL COMPREHENSIVE CANCER NETWORK",
    "NCCN",
    "NCCN GUIDELINES",
    "NCCN GUIDELINES FOR PATIENTS",
    "FOUNDATION",
}


def clean_line(line: str) -> str:
    """
    Normalize whitespace without changing the actual wording.
    """
    line = line.replace("\u00a0", " ")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def is_noise(line: str) -> bool:
    """
    Identify obvious boilerplate.
    """
    normalized = clean_line(line).upper()

    if not normalized:
        return True

    if normalized in NOISE_EXACT:
        return True

    if normalized.startswith("HTTP://"):
        return True

    if normalized.startswith("HTTPS://"):
        return True

    return False


def looks_like_page_number(line: str) -> bool:
    """
    Detect a line containing only a page number.
    """
    return bool(re.fullmatch(r"\d+", clean_line(line)))


def is_running_header(line: str) -> bool:
    """
    Detect textbook running headers.

    Examples:
        2 Chapter 1 Noninvasive Breast Cancer
        3Chapter 1 Noninvasive Breast Cancer
    """
    line = clean_line(line)

    if RUNNING_HEADER_PATTERN.match(line):
        return True

    if PAGE_CHAPTER_HEADER_PATTERN.match(line):
        return True

    return False


def extract_running_chapter(line: str) -> Optional[str]:
    """
    Extract chapter number from a running header.
    """
    line = clean_line(line)

    match = re.search(
        r"Chapter\s+(\d+)",
        line,
        re.IGNORECASE,
    )

    if match:
        return f"Chapter {match.group(1)}"

    return None


def is_chapter_heading(line: str) -> bool:
    """
    Detect standalone chapter headings.
    """
    line = clean_line(line)

    return bool(CHAPTER_PATTERN.match(line))


def extract_chapter_heading(line: str) -> Optional[str]:
    """
    Return normalized chapter heading.
    """
    match = CHAPTER_PATTERN.match(clean_line(line))

    if match:
        return f"Chapter {match.group(1)}"

    return None


def is_numbered_section(line: str) -> bool:
    """
    Detect NCCN-style numbered sections.

    Example:
        1 About adrenal tumors
        2 Testing for adrenal tumors

    Important:
    We reject lines that look like page numbers or running
    textbook headers.
    """
    line = clean_line(line)

    if is_noise(line):
        return False

    if looks_like_page_number(line):
        return False

    if is_running_header(line):
        return False

    match = NUMBERED_SECTION_PATTERN.match(line)

    if not match:
        return False

    title = match.group(2).strip()

    # Don't accept something that looks like ordinary prose.
    if len(title.split()) > 18:
        return False

    # Must contain alphabetic text.
    if not re.search(r"[A-Za-z]", title):
        return False

    return True


def is_subsection(line: str) -> bool:
    """
    Detect numbered textbook subsections.

    Example:
        1.1 Epidemiology
        1.2 Pathology
    """
    line = clean_line(line)

    if is_noise(line):
        return False

    match = SUBSECTION_PATTERN.match(line)

    if not match:
        return False

    title = match.group(2).strip()

    if len(title.split()) > 18:
        return False

    return True


def looks_like_heading(line: str) -> bool:
    """
    Detect non-numbered textbook headings.

    Examples:
        Epidemiology
        Pathology
        Treatment
        Multifocality

    We keep this conservative because normal prose can also
    appear on its own line in extracted PDFs.
    """
    line = clean_line(line)

    if is_noise(line):
        return False

    if looks_like_page_number(line):
        return False

    if is_running_header(line):
        return False

    if is_chapter_heading(line):
        return False

    if is_numbered_section(line):
        return False

    if is_subsection(line):
        return False

    # Too long to be a heading.
    if len(line) > 100:
        return False

    words = line.split()

    if len(words) > 10:
        return False

    # Must contain letters.
    if not re.search(r"[A-Za-z]", line):
        return False

    # Avoid sentences.
    if line.endswith((".", ",", ";", ":")):
        return False

    # Most textbook headings are short.
    return 1 <= len(words) <= 8


# ============================================================
# PAGE HEADING DETECTION
# ============================================================

def detect_page_structure(
    raw_text: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Detect chapter and section information from a single page.

    The function deliberately avoids assigning a section when
    confidence is low.
    """

    raw_lines = [
        clean_line(line)
        for line in raw_text.splitlines()
    ]

    lines = [
        line
        for line in raw_lines
        if line and not is_noise(line)
    ]

    detected_chapter: Optional[str] = None
    detected_section: Optional[str] = None

    # --------------------------------------------------------
    # First pass: chapter information
    # --------------------------------------------------------

    for line in lines[:30]:

        if is_chapter_heading(line):
            detected_chapter = extract_chapter_heading(line)
            break

        if is_running_header(line):
            chapter = extract_running_chapter(line)

            if chapter:
                detected_chapter = chapter
                break

    # --------------------------------------------------------
    # Second pass: numbered sections
    # --------------------------------------------------------

    for line in lines[:40]:

        if is_running_header(line):
            continue

        if looks_like_page_number(line):
            continue

        if is_numbered_section(line):
            detected_section = line
            break

        if is_subsection(line):
            detected_section = line
            break

    # --------------------------------------------------------
    # Third pass: simple textbook heading
    # --------------------------------------------------------

    if detected_section is None:

        # We don't treat the first line blindly as a heading.
        #
        # Look through the first several lines after removing
        # obvious page/header material.
        for line in lines[:25]:

            if is_running_header(line):
                continue

            if looks_like_page_number(line):
                continue

            if is_chapter_heading(line):
                continue

            if looks_like_heading(line):
                detected_section = line
                break

    return detected_chapter, detected_section


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_page_text(text: str) -> str:
    """
    Clean extracted PDF text while preserving paragraph
    boundaries as much as possible.
    """
    if not text:
        return ""

    cleaned_lines = []

    for raw_line in text.splitlines():

        line = clean_line(raw_line)

        if not line:
            continue

        # Remove common repeated PDF footer artifacts.
        if "LWBK" in line and ".indd" in line:
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# ============================================================
# DOCUMENT CLASSIFICATION
# ============================================================

def classify_document(path: Path) -> str:

    try:
        path.relative_to(PATIENT_GUIDELINES_DIR)
        return PATIENT_GUIDELINE
    except ValueError:
        pass

    return ONCOLOGY_REFERENCE


# ============================================================
# DOCUMENT PROCESSING
# ============================================================

def process_document(pdf_path: Path) -> dict:

    reader = PdfReader(str(pdf_path))

    document_type = classify_document(pdf_path)

    pages = []

    current_chapter: Optional[str] = None
    current_section: Optional[str] = None

    total_characters = 0
    pages_with_text = 0
    pages_without_text = 0

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        try:
            raw_text = page.extract_text() or ""

        except Exception as exc:

            print(
                f"    WARNING: page {page_number} "
                f"could not be extracted: {exc}"
            )

            raw_text = ""

        text = clean_page_text(raw_text)

        if text:
            pages_with_text += 1
            total_characters += len(text)
        else:
            pages_without_text += 1

        # ----------------------------------------------------
        # Detect structure
        # ----------------------------------------------------

        page_chapter, page_section = detect_page_structure(
            raw_text
        )

        if page_chapter:
            current_chapter = page_chapter

        if page_section:
            current_section = page_section

        # ----------------------------------------------------
        # Store page
        # ----------------------------------------------------

        pages.append(
            {
                "page": page_number,
                "chapter": current_chapter,
                "section": current_section,
                "has_text": bool(text),
                "character_count": len(text),
                "text": text,
            }
        )

    return {
        "document": pdf_path.name,
        "document_type": document_type,
        "status": "OK",
        "page_count": len(reader.pages),
        "pages_with_text": pages_with_text,
        "pages_without_text": pages_without_text,
        "total_characters": total_characters,
        "pages": pages,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("BUILDING STRUCTURED DOCUMENT MAP")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pdf_files = []

    if PATIENT_GUIDELINES_DIR.exists():
        pdf_files.extend(
            PATIENT_GUIDELINES_DIR.glob("*.pdf")
        )

    if ONCOLOGY_REFERENCES_DIR.exists():
        pdf_files.extend(
            ONCOLOGY_REFERENCES_DIR.glob("*.pdf")
        )

    pdf_files = sorted(set(pdf_files))

    print(f"\nPDFs found: {len(pdf_files)}")

    documents = []

    successful = 0
    failed = 0

    for index, pdf_path in enumerate(
        pdf_files,
        start=1,
    ):

        print(
            f"\n[{index}/{len(pdf_files)}] "
            f"{pdf_path.name}"
        )

        try:

            document = process_document(
                pdf_path
            )

            documents.append(document)

            successful += 1

            print(
                f"    Type: "
                f"{document['document_type']}"
            )

            print(
                f"    Pages: "
                f"{document['page_count']}"
            )

            print(
                f"    Text characters: "
                f"{document['total_characters']:,}"
            )

        except Exception as exc:

            failed += 1

            print(
                f"    FAILED: {exc}"
            )

            documents.append(
                {
                    "document": pdf_path.name,
                    "document_type": classify_document(
                        pdf_path
                    ),
                    "status": "FAILED",
                    "error": str(exc),
                    "page_count": 0,
                    "pages_with_text": 0,
                    "pages_without_text": 0,
                    "total_characters": 0,
                    "pages": [],
                }
            )

    result = {
        "project": "Cancer Multi-Agent Assistant",
        "document_count": len(documents),
        "successful": successful,
        "failed": failed,
        "documents": documents,
    }

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    total_pages = sum(
        d.get("page_count", 0)
        for d in documents
    )

    total_characters = sum(
        d.get("total_characters", 0)
        for d in documents
    )

    print("\n" + "=" * 70)
    print("DOCUMENT MAP COMPLETE")
    print("=" * 70)

    print(
        f"Documents processed: {len(documents)}"
    )

    print(
        f"Successful: {successful}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Total pages: {total_pages:,}"
    )

    print(
        f"Total characters: {total_characters:,}"
    )

    print("\nOutput:")
    print(OUTPUT_FILE)

    if failed:
        print(
            "\nWARNING: Some documents failed."
        )
    else:
        print(
            "\nAll documents processed successfully."
        )


if __name__ == "__main__":
    main()