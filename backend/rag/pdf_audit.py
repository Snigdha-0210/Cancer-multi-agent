from pathlib import Path
from pypdf import PdfReader
import json


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIRS = [
    PROJECT_ROOT / "data" / "source_documents" / "patient_guidelines",
    PROJECT_ROOT / "data" / "source_documents" / "oncology_references",
]

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "audit"
OUTPUT_FILE = OUTPUT_DIR / "pdf_audit.json"


# ---------------------------------------------------------
# AUDIT ONE PDF
# ---------------------------------------------------------

def audit_pdf(pdf_path: Path) -> dict:

    result = {
        "document": pdf_path.name,
        "path": str(pdf_path),
        "status": "OK",
        "page_count": 0,
        "pages_with_text": 0,
        "pages_without_text": 0,
        "total_characters": 0,
        "error": None,
    }

    try:
        reader = PdfReader(str(pdf_path))

        result["page_count"] = len(reader.pages)

        for page in reader.pages:

            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            text = text.strip()

            if text:
                result["pages_with_text"] += 1
                result["total_characters"] += len(text)
            else:
                result["pages_without_text"] += 1

    except Exception as exc:

        result["status"] = "FAILED"
        result["error"] = str(exc)

    return result


# ---------------------------------------------------------
# FIND ALL PDFs
# ---------------------------------------------------------

def find_pdfs():

    pdfs = []

    for directory in SOURCE_DIRS:

        if not directory.exists():
            print(f"WARNING: directory does not exist: {directory}")
            continue

        pdfs.extend(directory.glob("*.pdf"))

    return sorted(pdfs)


# ---------------------------------------------------------
# MAIN AUDIT
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("PDF AUDIT")
    print("=" * 70)

    pdf_files = find_pdfs()

    print(f"\nPDFs found: {len(pdf_files)}")

    results = []

    for index, pdf_path in enumerate(pdf_files, start=1):

        print(
            f"[{index}/{len(pdf_files)}] "
            f"Auditing: {pdf_path.name}"
        )

        result = audit_pdf(pdf_path)
        results.append(result)

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    successful = [
        r for r in results
        if r["status"] == "OK"
    ]

    failed = [
        r for r in results
        if r["status"] == "FAILED"
    ]

    empty = [
        r for r in successful
        if r["total_characters"] == 0
    ]

    low_text = [
        r for r in successful
        if 0 < r["total_characters"] < 1000
    ]

    total_pages = sum(
        r["page_count"]
        for r in successful
    )

    total_characters = sum(
        r["total_characters"]
        for r in successful
    )

    total_pages_with_text = sum(
        r["pages_with_text"]
        for r in successful
    )

    total_pages_without_text = sum(
        r["pages_without_text"]
        for r in successful
    )

    # -----------------------------------------------------
    # SAVE JSON
    # -----------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    audit_data = {
        "project": "cancer-multi-agent",
        "pdf_count": len(pdf_files),
        "successful": len(successful),
        "failed": len(failed),
        "empty_documents": len(empty),
        "low_text_documents": len(low_text),
        "total_pages": total_pages,
        "total_characters": total_characters,
        "total_pages_with_text": total_pages_with_text,
        "total_pages_without_text": total_pages_without_text,
        "documents": results,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            audit_data,
            f,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # PRINT SUMMARY
    # -----------------------------------------------------

    print("\n")
    print("=" * 70)
    print("PDF AUDIT COMPLETE")
    print("=" * 70)

    print(f"PDFs found:              {len(pdf_files)}")
    print(f"Successful:              {len(successful)}")
    print(f"Failed:                  {len(failed)}")
    print(f"Empty documents:         {len(empty)}")
    print(f"Low-text documents:      {len(low_text)}")
    print(f"Total pages:             {total_pages}")
    print(f"Pages with text:         {total_pages_with_text}")
    print(f"Pages without text:      {total_pages_without_text}")
    print(f"Total characters:        {total_characters:,}")

    print("\nOutput:")
    print(OUTPUT_FILE)

    # -----------------------------------------------------
    # SHOW FAILED FILES
    # -----------------------------------------------------

    if failed:

        print("\nFAILED FILES:")

        for item in failed:
            print(
                f"- {item['document']}: "
                f"{item['error']}"
            )

    # -----------------------------------------------------
    # SHOW EMPTY FILES
    # -----------------------------------------------------

    if empty:

        print("\nEMPTY FILES:")

        for item in empty:
            print(f"- {item['document']}")

    # -----------------------------------------------------
    # SHOW LOW-TEXT FILES
    # -----------------------------------------------------

    if low_text:

        print("\nLOW-TEXT FILES:")

        for item in low_text:

            print(
                f"- {item['document']} "
                f"({item['total_characters']} characters)"
            )


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    main()