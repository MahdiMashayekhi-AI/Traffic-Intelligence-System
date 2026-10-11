from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT / "PROJECT_STRUCTURE.md"

EXCLUDED_DIRS = {
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp",
    ".tif",
    ".tiff",
    ".jfif",
    ".avif",
}

DATA_DIRS = {"raw", "processed"}


def should_skip_file(path: Path) -> bool:
    # Ignore this script and its output file
    if path.resolve() == Path(__file__).resolve():
        return True

    if path.resolve() == OUTPUT_FILE.resolve():
        return True

    # Ignore TXT and image files only inside data/raw and data/processed
    relative_path = path.relative_to(ROOT)
    parts = relative_path.parts

    if len(parts) >= 3 and parts[0] == "data" and parts[1] in DATA_DIRS:
        if path.suffix.lower() == ".txt":
            return True

        if path.suffix.lower() in IMAGE_EXTENSIONS:
            return True

    return False


def build_tree(directory: Path, prefix: str = "") -> list[str]:
    entries = sorted(
        directory.iterdir(),
        key=lambda p: (not p.is_dir(), p.name.lower()),
    )

    visible_entries = []

    for entry in entries:
        if entry.is_dir():
            if entry.name in EXCLUDED_DIRS:
                continue
        else:
            if should_skip_file(entry):
                continue

        visible_entries.append(entry)

    lines = []

    for index, entry in enumerate(visible_entries):
        is_last = index == len(visible_entries) - 1

        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(build_tree(entry, prefix + extension))

    return lines


def main():
    tree = build_tree(ROOT)

    content = (
        f"# Project Structure\n\n```text\n{ROOT.name}/\n" + "\n".join(tree) + "\n```\n"
    )

    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Project structure saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
