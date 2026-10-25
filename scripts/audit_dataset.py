import argparse
from pathlib import Path

from traffic_intelligence_system.data.stats import compute_split_stats, stats_to_markdown
from traffic_intelligence_system.data.yolo_io import get_split_dirs, load_class_names


def parse_args():
    parser = argparse.ArgumentParser(description="Audit a YOLO dataset")

    parser.add_argument(
        "--root", type=Path, required=True, help="Root directory of the YOLO dataset"
    )

    parser.add_argument(
        "--layout",
        type=str,
        required=True,
        choices=["split-first", "type-first"],
        default="split-first",
        help="Layout of the YOLO dataset",
    )

    parser.add_argument(
        "--splits",
        type=str,
        required=True,
        nargs="+",
        default=["train", "val", "test"],
        help="List of splits to audit",
    )

    parser.add_argument(
        "--names-from",
        type=str,
        required=True,
        help="Path to the YAML file containing class names",
    )

    parser.add_argument(
        "--out", type=str, required=True, help="Path to the output markdown file"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    names = load_class_names(args.names_from)

    stats_by_split = {}
    for split in args.splits:
        images_dir, labels_dir = get_split_dirs(args.root, split, args.layout)
        stats = compute_split_stats(images_dir, labels_dir)
        stats_by_split[split] = stats

    markdown = stats_to_markdown(stats_by_split, names)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    Path(args.out).write_text(markdown, encoding="utf-8")

    print(f"Dataset audit saved to: {args.out}")


if __name__ == "__main__":
    main()
