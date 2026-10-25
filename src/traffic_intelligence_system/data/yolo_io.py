from dataclasses import dataclass
from pathlib import Path

import yaml

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class Box:
    class_id: int
    x: float
    y: float
    w: float
    h: float


@dataclass
class MatchResult:
    pairs: list[tuple[Path, Path]]
    images_without_label: list[Path]
    labels_without_image: list[Path]


def parse_label_line(line: str) -> Box:
    tokens = line.split()

    if len(tokens) != 5:
        raise ValueError(f"expected 5 values, got {len(tokens)}")

    try:
        class_id = int(tokens[0])
    except ValueError:
        raise ValueError("class id must be an integer")

    if class_id < 0:
        raise ValueError("class id must be positive")

    try:
        x = float(tokens[1])
        y = float(tokens[2])
        w = float(tokens[3])
        h = float(tokens[4])
    except ValueError:
        raise ValueError("coordinates must be numbers")

    if (
        not (0.0 <= x <= 1.0)
        or not (0.0 <= y <= 1.0)
        or not (0.0 < w <= 1.0)
        or not (0.0 < h <= 1.0)
    ):
        raise ValueError("value is not in the correct range")

    return Box(class_id, x, y, w, h)


def read_label_file(path: Path) -> tuple[list[Box], list[str]]:
    with open(path, mode="r", encoding="utf-8") as f:
        lines = f.readlines()

    boxes = []
    errors = []

    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if line == "":
            continue

        try:
            box = parse_label_line(line)
            boxes.append(box)
        except ValueError as e:
            errors.append(f"path: {path.name}\nline {i}: {e}\n{line}")

    return boxes, errors


def load_class_names(yaml_path: Path) -> list[str]:
    with open(yaml_path, mode="r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if isinstance(data["names"], list):
        return [name for name in data["names"]]
    elif isinstance(data["names"], dict):
        names = dict(sorted(data["names"].items()))
        return [name for name in names.values()]
    else:
        raise ValueError("names must be a list or a dictionary")


def get_split_dirs(root: Path, split: str, layout: str) -> tuple[Path, Path]:
    if layout == "split-first":
        return root / split / "images", root / split / "labels"

    elif layout == "type-first":
        return root / "images" / split, root / "labels" / split

    else:
        raise ValueError(f"invalid layout {layout}")


def match_images_to_labels(images_dir: Path, labels_dir: Path) -> MatchResult:
    image_paths = []
    if images_dir.exists():
        for p in images_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
                image_paths.append(p)

    label_paths = []
    if labels_dir.exists():
        for p in labels_dir.rglob("*.txt"):
            if p.is_file():
                label_paths.append(p)

    images_key = {}
    for p in image_paths:
        key = p.relative_to(images_dir).with_suffix("").as_posix()

        if key in images_key:
            raise ValueError(f"duplicate key {key} in {p}")

        images_key[key] = p

    labels_key = {}
    for p in label_paths:
        key = p.relative_to(labels_dir).with_suffix("").as_posix()
        labels_key[key] = p

    common_keys = sorted(set(images_key) & set(labels_key))

    pairs = []
    for key in common_keys:
        pairs.append((images_key[key], labels_key[key]))

    images_without_label = []
    for key in images_key:
        if key not in labels_key:
            images_without_label.append(images_key[key])
    images_without_label.sort()

    labels_without_image = []
    for key in labels_key:
        if key not in images_key:
            labels_without_image.append(labels_key[key])
    labels_without_image.sort()

    return MatchResult(pairs, images_without_label, labels_without_image)
