from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "PROJECT_CONTENTS.md"

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".idea",
    ".vscode",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "scratch",
    "dist",
    "build",
}

EXCLUDE_PATHS = {
    "data/raw",
    "data/processed",
}

EXCLUDE_FILES = {
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
    "PROJECT_CONTENTS.md",
}

INCLUDE_EXTENSIONS = {
    # Python
    ".py",
    ".pyi",
    # Markdown
    ".md",
    ".markdown",
    # Configuration
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
    # Scripts
    ".sh",
    ".ps1",
    ".bat",
    # Source code
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".html",
    ".css",
    ".sql",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".go",
    ".rs",
}

EXCLUDE_EXTENSIONS = {
    ".lock",
    ".txt",
    ".log",
    ".cache",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".tif",
    ".tiff",
    ".jfif",
    ".avif",
    ".pdf",
    ".zip",
    ".gz",
    ".whl",
    ".pt",
    ".pth",
    ".onnx",
    ".db",
    ".sqlite",
}


def is_excluded_path(path: Path) -> bool:
    """Check whether a path belongs to an excluded directory."""

    relative_path = path.relative_to(PROJECT_ROOT)

    if any(part in EXCLUDE_DIRS for part in relative_path.parts[:-1]):
        return True

    for excluded in EXCLUDE_PATHS:
        excluded_path = Path(excluded)

        if relative_path == excluded_path or excluded_path in relative_path.parents:
            return True

    return False


def should_include_file(path: Path) -> bool:
    """Determine whether a file should be included in the export."""

    if path.name in EXCLUDE_FILES:
        return False

    suffix = path.suffix.lower()

    if suffix in EXCLUDE_EXTENSIONS:
        return False

    return suffix in INCLUDE_EXTENSIONS


def make_fence(content: str) -> str:
    """Create a Markdown code fence that does not conflict with content."""

    longest = 0
    current = 0

    for char in content:
        if char == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return "`" * max(3, longest + 1)


def export_file_contents() -> None:
    """Export eligible project files into a single Markdown document."""

    output_lines = ["# Project Files Content\n"]
    included_files = []

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue

        if path.resolve() == OUTPUT_FILE.resolve():
            continue

        if is_excluded_path(path):
            continue

        if not should_include_file(path):
            continue

        included_files.append(path)

    included_files.sort(key=lambda path: path.relative_to(PROJECT_ROOT).as_posix())

    exported_count = 0

    for file_path in included_files:
        relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            print(f"Skipping {relative_path}: {error}")
            continue

        fence = make_fence(content)

        output_lines.append(f"## File: `{relative_path}`\n")
        output_lines.append(f"{fence}text")
        output_lines.append(content)

        if content and not content.endswith("\n"):
            output_lines.append("")

        output_lines.append(f"{fence}\n")
        exported_count += 1

    OUTPUT_FILE.write_text(
        "\n".join(output_lines),
        encoding="utf-8",
    )

    print(f"Exported {exported_count} files.")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    export_file_contents()
