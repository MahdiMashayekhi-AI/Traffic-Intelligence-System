from dataclasses import dataclass, field
from pathlib import Path
from statistics import median

from traffic_intelligence_system.data.yolo_io import (
    match_images_to_labels,
    read_label_file,
)


@dataclass
class SplitStats:
    n_images: int = 0
    n_label_files: int = 0
    n_matched: int = 0
    n_images_without_label: int = 0
    n_labels_without_image: int = 0
    n_empty_labels: int = 0
    n_invalid_lines: int = 0
    instances_per_class: dict[int, int] = field(default_factory=dict)
    images_per_class: dict[int, int] = field(default_factory=dict)
    median_w_per_class: dict[int, float] = field(default_factory=dict)
    median_h_per_class: dict[int, float] = field(default_factory=dict)
    sample_errors: list[str] = field(default_factory=list)


def compute_split_stats(images_dir: Path, labels_dir: Path) -> SplitStats:
    result = match_images_to_labels(images_dir, labels_dir)

    n_invalid_lines = 0
    n_empty_labels = 0
    instances_per_class = {}
    images_per_class = {}
    widths_per_class = {}
    heights_per_class = {}
    sample_errors = []

    if labels_dir.exists():
        for label_path in labels_dir.rglob("*.txt"):
            boxes, errors = read_label_file(label_path)

            n_invalid_lines += len(errors)

            if len(boxes) == 0 and len(errors) == 0:
                n_empty_labels += 1

            for box in boxes:
                if box.class_id not in instances_per_class:
                    instances_per_class[box.class_id] = 1
                else:
                    instances_per_class[box.class_id] += 1

                widths_per_class.setdefault(box.class_id, []).append(box.w)
                heights_per_class.setdefault(box.class_id, []).append(box.h)

            classes_in_this_image = {box.class_id for box in boxes}
            for cid in classes_in_this_image:
                if cid not in images_per_class:
                    images_per_class[cid] = 1
                else:
                    images_per_class[cid] += 1

            sample_errors.extend(errors[: 5 - len(sample_errors)])

    return SplitStats(
        n_images=len(result.pairs) + len(result.images_without_label),
        n_label_files=len(result.pairs) + len(result.labels_without_image),
        n_matched=len(result.pairs),
        n_images_without_label=len(result.images_without_label),
        n_labels_without_image=len(result.labels_without_image),
        n_empty_labels=n_empty_labels,
        n_invalid_lines=n_invalid_lines,
        instances_per_class=instances_per_class,
        images_per_class=images_per_class,
        median_w_per_class={cid: median(ws) for cid, ws in widths_per_class.items()},
        median_h_per_class={cid: median(hs) for cid, hs in heights_per_class.items()},
        sample_errors=sample_errors,
    )


def count_instances(labels_dir: Path) -> dict[int, int]:
    counts = {}

    if labels_dir.exists():
        for label_path in labels_dir.rglob("*.txt"):
            boxes, _ = read_label_file(label_path)

            for box in boxes:
                if box.class_id not in counts:
                    counts[box.class_id] = 1
                else:
                    counts[box.class_id] += 1

    return counts


def stats_to_markdown(
    stats_by_split: dict[str, SplitStats],
    class_names: list[str],
    title: str = "Dataset Statistics",
) -> str:
    lines: list[str] = []

    lines.append(f"# {title}")
    lines.append("")
    lines.append(
        "| split | images | label files | matched | empty labels "
        "| images w/o label | labels w/o image | invalid lines |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")

    for split, stats in stats_by_split.items():
        lines.append(
            f"| {split} "
            f"| {stats.n_images} "
            f"| {stats.n_label_files} "
            f"| {stats.n_matched} "
            f"| {stats.n_empty_labels} "
            f"| {stats.n_images_without_label} "
            f"| {stats.n_labels_without_image} "
            f"| {stats.n_invalid_lines} |"
        )

    lines.append("")

    for split, stats in stats_by_split.items():
        lines.append(f"### {split}")
        lines.append("")
        lines.append(
            "| class | instances | % | images with class | median w | median h |"
        )
        lines.append("|---|---|---|---|---|---|")

        total_instances = sum(stats.instances_per_class.values())

        for class_id, n_inst in sorted(stats.instances_per_class.items()):
            if 0 <= class_id < len(class_names):
                class_label = class_names[class_id]
            else:
                class_label = f"class_{class_id}"

            if total_instances == 0:
                percent = 0.0
            else:
                percent = n_inst / total_instances * 100.0

            n_images_with_class = stats.images_per_class.get(class_id, 0)

            median_w = stats.median_w_per_class.get(class_id)
            median_h = stats.median_h_per_class.get(class_id)
            median_w_str = f"{median_w:.2f}" if median_w is not None else "-"
            median_h_str = f"{median_h:.2f}" if median_h is not None else "-"

            lines.append(
                f"| {class_label} "
                f"| {n_inst} "
                f"| {percent:.1f} "
                f"| {n_images_with_class} "
                f"| {median_w_str} "
                f"| {median_h_str} |"
            )

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
