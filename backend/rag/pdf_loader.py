from pathlib import Path
from typing import Any

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PDF_DIRECTORY = PROJECT_ROOT / "data" / "raw_pdfs"


def extract_pdf_pages(pdf_path: Path) -> list[dict[str, Any]]:
    """
    Extract text from every page of a PDF.

    Each page is kept as a separate record so that we preserve
    the original page number for later citations.
    """

    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        text = text.strip()

        if not text:
            continue

        pages.append(
            {
                "document": pdf_path.name,
                "page": page_number,
                "text": text,
            }
        )

    return pages


def load_all_pdfs() -> list[dict[str, Any]]:
    """
    Load every PDF inside data/raw_pdfs/.
    """

    if not PDF_DIRECTORY.exists():
        raise FileNotFoundError(
            f"PDF directory does not exist: {PDF_DIRECTORY}"
        )

    pdf_files = sorted(PDF_DIRECTORY.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in: {PDF_DIRECTORY}"
        )

    all_pages = []

    for pdf_path in pdf_files:
        print(f"Reading: {pdf_path.name}")

        pages = extract_pdf_pages(pdf_path)

        print(f"  Extracted {len(pages)} pages with text.")

        all_pages.extend(pages)

    return all_pages


if __name__ == "__main__":
    pages = load_all_pdfs()

    print()
    print("=" * 60)
    print("PDF INGESTION TEST")
    print("=" * 60)
    print(f"Total pages extracted: {len(pages)}")

    if pages:
        first_page = pages[0]

        print()
        print("First extracted page:")
        print(f"Document: {first_page['document']}")
        print(f"Page: {first_page['page']}")
        print()
        print(first_page["text"][:1000])