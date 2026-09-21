from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"
CLEAN_FILE = PROJECT_ROOT / "data" / "processed" / "clean_chunks.jsonl"


def inspect_file(path: Path, count: int = 20):
    print()
    print("=" * 80)
    print(f"FILE: {path.name}")
    print("=" * 80)

    if not path.exists():
        print(f"File not found: {path}")
        return

    with path.open("r", encoding="utf-8") as file:
        for index, line in enumerate(file):
            if index >= count:
                break

            line = line.strip()

            if not line:
                continue

            chunk = json.loads(line)

            print()
            print("-" * 80)
            print(f"CHUNK #{index + 1}")
            print("-" * 80)

            print("Keys:")
            print(list(chunk.keys()))

            print()

            for key, value in chunk.items():
                if key == "text":
                    print(f"{key}:")
                    print(str(value)[:700])
                else:
                    print(f"{key}: {value}")


def main():
    inspect_file(INPUT_FILE, 20)
    inspect_file(CLEAN_FILE, 10)


if __name__ == "__main__":
    main()