"""Audit a YOLO dataset and write a Markdown statistics report.

Example invocations (run from the repository root):

    uv run --no-sync python scripts/audit_dataset.py
        --root data/raw/ua_detrac
        --layout split-first
        --splits train test
        --names-from data/raw/ua_detrac/data.yaml
        --out docs/data/audit_raw_ua_detrac.md
        --title "Dataset Statistics: UA-DETRAC"

    uv run --no-sync python scripts/audit_dataset.py
        --root data/raw/citypersons
        --layout type-first
        --splits train val test
        --names-from data/raw/citypersons/data.yaml
        --out docs/data/audit_raw_citypersons.md
        --title "Dataset Statistics: CityPersons"
"""

import argparse
import sys
from pathlib import Path

from traffic_intelligence_system.data.stats import compute_split_stats, stats_to_markdown
from traffic_intelligence_system.data.yolo_io import get_split_dirs, load_class_names


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a YOLO dataset")

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Root directory of the YOLO dataset",
    )

    parser.add_argument(
        "--layout",
        type=str,
        required=True,
        choices=["split-first", "type-first"],
        help="Layout of the YOLO dataset",
    )

    parser.add_argument(
        "--splits",
        type=str,
        required=True,
        nargs="+",
        help="List of splits to audit",
    )

    parser.add_argument(
        "--names-from",
        type=Path,
        required=True,
        help="Path to the YAML file containing class names",
    )

    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Path to the output markdown file",
    )

    parser.add_argument(
        "--title",
        type=str,
        default="Dataset Statistics",
        help="Title of the report",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    names = load_class_names(args.names_from)

    stats_by_split = {}
    for split in args.splits:
        images_dir, labels_dir = get_split_dirs(args.root, split, args.layout)

        if not images_dir.exists():
            print(
                f"Warning: image directory for split '{split}' does not exist: "
                f"{images_dir}; skipping split.",
                file=sys.stderr,
            )
            continue

        stats = compute_split_stats(images_dir, labels_dir)
        stats_by_split[split] = stats

    markdown = stats_to_markdown(stats_by_split, names, title=args.title)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    args.out.write_text(markdown, encoding="utf-8")

    print(f"Dataset audit saved to: {args.out}")


if __name__ == "__main__":
    main()
