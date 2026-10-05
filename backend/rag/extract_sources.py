from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_SOURCE_DIR = PROJECT_ROOT / "data" / "raw_pdfs"

SOURCE_DOCUMENTS_DIR = PROJECT_ROOT / "data" / "source_documents"

PATIENT_GUIDELINES_DIR = SOURCE_DOCUMENTS_DIR / "patient_guidelines"
ONCOLOGY_REFERENCES_DIR = SOURCE_DOCUMENTS_DIR / "oncology_references"


CANCER_TYPE_ZIP = RAW_SOURCE_DIR / "Cancer_Type.zip"
PDFS_ZIP = RAW_SOURCE_DIR / "pdfs.zip"


def prepare_directories() -> None:
    """Create the clean source-document directories."""

    PATIENT_GUIDELINES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ONCOLOGY_REFERENCES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def extract_zip(
    zip_path: Path,
    destination: Path,
) -> int:
    """
    Extract PDF files from a ZIP archive.

    Returns the number of extracted PDFs.

    Existing files are not overwritten automatically.
    """

    if not zip_path.exists():
        print(f"WARNING: ZIP not found: {zip_path}")
        return 0

    extracted_count = 0

    with zipfile.ZipFile(zip_path, "r") as archive:

        for member in archive.infolist():

            if member.is_dir():
                continue

            member_name = Path(member.filename)

            # We only want PDF source documents.
            if member_name.suffix.lower() != ".pdf":
                continue

            output_path = destination / member_name.name

            if output_path.exists():
                print(
                    f"SKIP existing file: {output_path.name}"
                )
                continue

            with archive.open(member) as source:
                with output_path.open("wb") as target:
                    shutil.copyfileobj(source, target)

            extracted_count += 1

            print(
                f"EXTRACTED: {output_path.name}"
            )

    return extracted_count


def copy_loose_pdf(
    filename: str,
    destination: Path,
) -> None:
    """Copy an existing loose PDF into the appropriate source directory."""

    source = RAW_SOURCE_DIR / filename
    target = destination / filename

    if not source.exists():
        print(f"WARNING: Loose file not found: {source}")
        return

    if target.exists():
        print(f"SKIP existing file: {target.name}")
        return

    shutil.copy2(source, target)

    print(f"COPIED: {target.name}")


def main() -> None:

    print("=" * 70)
    print("FACULTY SOURCE EXTRACTION")
    print("=" * 70)

    prepare_directories()

    print()
    print("1. Extracting patient guidelines...")
    print("-" * 70)

    patient_count = extract_zip(
        CANCER_TYPE_ZIP,
        PATIENT_GUIDELINES_DIR,
    )

    print()
    print("2. Extracting oncology references...")
    print("-" * 70)

    reference_count = extract_zip(
        PDFS_ZIP,
        ONCOLOGY_REFERENCES_DIR,
    )

    print()
    print("3. Adding loose source PDFs...")
    print("-" * 70)

    # These were already present outside the ZIP archive.
    # We place them in the appropriate reference collection.
    copy_loose_pdf(
        "a-practical-guide-to-skin-cancer-2018.pdf",
        ONCOLOGY_REFERENCES_DIR,
    )

    copy_loose_pdf(
        "managing-skin-cancer-2010.pdf",
        ONCOLOGY_REFERENCES_DIR,
    )

    print()
    print("=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)

    print(
        f"Patient-guideline PDFs extracted: {patient_count}"
    )

    print(
        f"Oncology-reference PDFs extracted: {reference_count}"
    )

    print()
    print(
        "Original ZIP files were NOT modified."
    )

    print()
    print(
        f"Patient sources: {PATIENT_GUIDELINES_DIR}"
    )

    print(
        f"Reference sources: {ONCOLOGY_REFERENCES_DIR}"
    )


if __name__ == "__main__":
    main()