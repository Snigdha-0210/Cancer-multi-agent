from __future__ import annotations

import json
import zipfile
from collections import Counter
from pathlib import Path


# Project root:
# cancer-multi-agent/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Faculty source directory
RAW_SOURCE_DIR = PROJECT_ROOT / "data" / "raw_pdfs"

# ZIP collections
CANCER_TYPE_ZIP = RAW_SOURCE_DIR / "Cancer_Type.zip"
PDFS_ZIP = RAW_SOURCE_DIR / "pdfs.zip"

# Output directory
INVENTORY_DIR = PROJECT_ROOT / "data" / "processed" / "inventory"
INVENTORY_FILE = INVENTORY_DIR / "source_inventory.json"


def get_extension(filename: str) -> str:
    """Return a lowercase file extension."""
    suffix = Path(filename).suffix.lower()

    if suffix:
        return suffix

    return "[no extension]"


def inspect_zip(zip_path: Path) -> dict:
    """Inspect a ZIP file without extracting it."""

    print()
    print("=" * 70)
    print(f"ZIP COLLECTION: {zip_path.name}")
    print("=" * 70)

    if not zip_path.exists():
        print(f"WARNING: ZIP file not found: {zip_path}")
        return {
            "name": zip_path.name,
            "exists": False,
            "file_count": 0,
            "files": [],
        }

    with zipfile.ZipFile(zip_path, "r") as archive:
        members = [
            info
            for info in archive.infolist()
            if not info.is_dir()
        ]

    extensions = Counter(
        get_extension(info.filename)
        for info in members
    )

    print(f"Documents/files: {len(members)}")
    print()
    print("File types:")

    for extension, count in sorted(extensions.items()):
        print(f"  {extension}: {count}")

    print()
    print("Files:")

    for info in members:
        print(f"  {info.filename}")
        print(f"      size: {info.file_size:,} bytes")

    return {
        "name": zip_path.name,
        "exists": True,
        "file_count": len(members),
        "file_types": dict(sorted(extensions.items())),
        "files": [
            {
                "path": info.filename,
                "filename": Path(info.filename).name,
                "extension": get_extension(info.filename),
                "size_bytes": info.file_size,
            }
            for info in members
        ],
    }


def inspect_loose_files() -> dict:
    """Inspect files directly inside data/raw_pdfs."""

    print()
    print("=" * 70)
    print("LOOSE SOURCE FILES")
    print("=" * 70)

    files = [
        path
        for path in RAW_SOURCE_DIR.iterdir()
        if path.is_file()
    ]

    # Do not count the ZIP archives here as source documents.
    source_files = [
        path
        for path in files
        if path.name not in {
            "Cancer_Type.zip",
            "pdfs.zip",
        }
    ]

    extensions = Counter(
        path.suffix.lower() or "[no extension]"
        for path in source_files
    )

    print(f"Loose files: {len(source_files)}")
    print()
    print("File types:")

    for extension, count in sorted(extensions.items()):
        print(f"  {extension}: {count}")

    print()
    print("Files:")

    for path in source_files:
        print(f"  {path.name}")
        print(f"      size: {path.stat().st_size:,} bytes")

    return {
        "directory": str(RAW_SOURCE_DIR),
        "file_count": len(source_files),
        "file_types": dict(sorted(extensions.items())),
        "files": [
            {
                "filename": path.name,
                "extension": path.suffix.lower() or "[no extension]",
                "size_bytes": path.stat().st_size,
            }
            for path in source_files
        ],
    }


def find_duplicate_filenames(
    cancer_type_inventory: dict,
    pdfs_inventory: dict,
    loose_inventory: dict,
) -> list[dict]:
    """Find filenames appearing in multiple source collections."""

    locations: dict[str, list[str]] = {}

    def add(filename: str, location: str) -> None:
        key = filename.lower()

        if key not in locations:
            locations[key] = []

        locations[key].append(location)

    for file_info in cancer_type_inventory.get("files", []):
        add(
            file_info["filename"],
            f'Cancer_Type.zip::{file_info["path"]}',
        )

    for file_info in pdfs_inventory.get("files", []):
        add(
            file_info["filename"],
            f'pdfs.zip::{file_info["path"]}',
        )

    for file_info in loose_inventory.get("files", []):
        add(
            file_info["filename"],
            f'raw_pdfs::{file_info["filename"]}',
        )

    duplicates = []

    for filename, locations_list in sorted(locations.items()):
        if len(locations_list) > 1:
            duplicates.append(
                {
                    "filename": filename,
                    "locations": locations_list,
                }
            )

    return duplicates


def build_inventory() -> dict:
    """Build the complete source inventory."""

    if not RAW_SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"Source directory does not exist: {RAW_SOURCE_DIR}"
        )

    loose_inventory = inspect_loose_files()

    cancer_type_inventory = inspect_zip(CANCER_TYPE_ZIP)

    pdfs_inventory = inspect_zip(PDFS_ZIP)

    duplicates = find_duplicate_filenames(
        cancer_type_inventory,
        pdfs_inventory,
        loose_inventory,
    )

    inventory = {
        "project": "cancer-multi-agent",
        "source_directory": str(RAW_SOURCE_DIR),
        "collections": {
            "loose_files": loose_inventory,
            "Cancer_Type.zip": cancer_type_inventory,
            "pdfs.zip": pdfs_inventory,
        },
        "duplicate_filenames": duplicates,
        "summary": {
            "loose_file_count": loose_inventory["file_count"],
            "cancer_type_file_count": cancer_type_inventory["file_count"],
            "pdfs_zip_file_count": pdfs_inventory["file_count"],
            "duplicate_filename_count": len(duplicates),
        },
    }

    return inventory


def save_inventory(inventory: dict) -> None:
    """Save inventory as JSON."""

    INVENTORY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with INVENTORY_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            inventory,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 70)
    print("INVENTORY SAVED")
    print("=" * 70)
    print(INVENTORY_FILE)


def print_summary(inventory: dict) -> None:
    """Print a concise final summary."""

    summary = inventory["summary"]

    print()
    print("=" * 70)
    print("SOURCE INVENTORY SUMMARY")
    print("=" * 70)

    print(
        f'Loose source files:       '
        f'{summary["loose_file_count"]}'
    )

    print(
        f'Cancer_Type.zip files:    '
        f'{summary["cancer_type_file_count"]}'
    )

    print(
        f'pdfs.zip files:           '
        f'{summary["pdfs_zip_file_count"]}'
    )

    print(
        f'Duplicate filenames:      '
        f'{summary["duplicate_filename_count"]}'
    )

    print()
    print("No files were extracted or modified.")


def main() -> None:
    inventory = build_inventory()

    save_inventory(inventory)

    print_summary(inventory)


if __name__ == "__main__":
    main()