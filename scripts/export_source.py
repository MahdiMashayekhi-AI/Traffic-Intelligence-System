import os

EXCLUDE_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    ".idea",
    ".vscode",
    ".ruff_cache",
    "data",
    "scratch",
}
EXCLUDE_EXTENSIONS = {
    ".txt",
    ".md",
    ".lock",
    ".jpg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".tif",
    ".tiff",
    ".jfif",
    ".avif",
    ".cache",
}


def export_file_contents(start_path, output_file="PROJECT_CONTENTS.md"):
    output_lines = ["# Project Files Content\n"]

    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        files.sort()

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTENSIONS or file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, start_path)

            output_lines.append(f"## File: `{rel_path}`\n")
            output_lines.append("```text")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    output_lines.append(content)
            except Exception as e:
                output_lines.append(f"[Error while reading the file: {e}]")

            output_lines.append("```\n")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"Contents of files suceccfully saved in: '{output_file}'")


if __name__ == "__main__":
    export_file_contents(".")
