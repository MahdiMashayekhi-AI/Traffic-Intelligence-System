import math
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


def _range_str(name: str) -> str:
    # x/y: [0, 1]  —  w/h: (0, 1]
    return "[0, 1]" if name in ("x", "y") else "(0, 1]"


def parse_label_line(line: str) -> Box:
    tokens = line.split()

    if len(tokens) != 5:
        raise ValueError(f"expected 5 values, got {len(tokens)}")

    try:
        class_id = int(tokens[0])
    except ValueError:
        raise ValueError(f"class id must be an integer, got {tokens[0]!r}")

    if class_id < 0:
        raise ValueError(f"class id must be non-negative, got {class_id}")

    values = {}
    for name, token in zip(("x", "y", "w", "h"), tokens[1:]):
        try:
            values[name] = float(token)
        except ValueError:
            raise ValueError(f"{name} must be a float, got {token!r}")

    ranges = {
        "x": (0.0, True),
        "y": (0.0, True),
        "w": (0.0, False),
        "h": (0.0, False),
    }

    for name, value in values.items():
        lower, lower_inclusive = ranges[name]
        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be a finite number in {_range_str(name)}, got {value}"
            )
        lower_ok = value >= lower if lower_inclusive else value > lower
        if not (lower_ok and value <= 1.0):
            raise ValueError(f"{name} must be in {_range_str(name)}, got {value}")

    return Box(class_id, values["x"], values["y"], values["w"], values["h"])


def read_label_file(path: Path) -> tuple[list[Box], list[str]]:
    with open(path, mode="r", encoding="utf-8") as f:
        lines = f.readlines()

    boxes = []
    errors = []

    for i, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if stripped == "":
            continue

        try:
            box = parse_label_line(stripped)
            boxes.append(box)
        except ValueError as e:
            errors.append(f"{path.name}:{i}: {e}; line={raw_line!r}")

    return boxes, errors


def load_class_names(yaml_path: Path | str) -> list[str]:
    with open(yaml_path, mode="r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"{yaml_path}: expected a mapping at top level")

    if "names" not in data:
        raise ValueError(f"{yaml_path}: missing 'names' key")

    names = data["names"]

    if not names:
        raise ValueError(f"{yaml_path}: names is empty")

    if isinstance(names, list):
        result = list(names)

    elif isinstance(names, dict):
        if not all(isinstance(k, int) and not isinstance(k, bool) for k in names):
            raise ValueError(f"{yaml_path}: names keys must be integers")

        keys = sorted(names.keys())
        if keys[0] != 0 or keys[-1] != len(keys) - 1:
            raise ValueError(f"{yaml_path}: names must be contiguous starting from 0")

        result = [names[k] for k in keys]

    else:
        raise ValueError(f"{yaml_path}: names must be a list or a dictionary")

    for idx, name in enumerate(result):
        if not isinstance(name, str):
            raise ValueError(
                f"{yaml_path}: name at index {idx} must be a string, "
                f"got {type(name).__name__}"
            )
        if name == "":
            raise ValueError(f"{yaml_path}: name at index {idx} must be non-empty")

    return result


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
