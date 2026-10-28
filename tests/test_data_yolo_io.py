from pathlib import Path

import pytest

from traffic_intelligence_system.data.stats import compute_split_stats
from traffic_intelligence_system.data.yolo_io import (
    get_split_dirs,
    load_class_names,
    match_images_to_labels,
    parse_label_line,
    read_label_file,
)


def test_parse_valid_line():
    box = parse_label_line("2 0.5 0.4 0.1 0.2")

    assert box.class_id == 2
    assert box.w == 0.1


@pytest.mark.parametrize(
    "bad",
    [
        "0 0.5 0.4 0.1",
        "0 0.5 0.4 0.1 0.2 0.3",
        "abc 0.5 0.4 0.1 0.2",
        "0.5 0.4 0.1 0.2 0.3",
        "-1 0.5 0.4 0.1 0.2",
        "1 1.2 0.4 0.1 0.2",
        "0 0.3 0.2 0.0 0.3",
        "0 0.3 0.2 0.4 -0.1",
        "0 nan 0.4 0.1 0.2",
    ],
)
def test_parse_invalid_line_raises(bad):
    with pytest.raises(ValueError):
        parse_label_line(bad)


def test_parse_label_line_invalid_x_reports_field_value_and_range():
    with pytest.raises(ValueError) as excinfo:
        parse_label_line("1 1.2 0.4 0.1 0.2")

    assert "x must be in [0, 1], got 1.2" == str(excinfo.value)


def test_read_label_file_with_valid_lines(tmp_path: Path):
    file_path = tmp_path / "good.txt"

    file_path.write_text("1 0.5 0.4 0.1 0.2\n2 0.5 0.4 0.1 0.2", encoding="utf-8")

    boxes, errors = read_label_file(file_path)

    assert len(boxes) == 2
    assert len(errors) == 0
    assert boxes[0].class_id == 1
    assert boxes[1].class_id == 2


def test_read_label_file_empty(tmp_path: Path):
    file_path = tmp_path / "empty.txt"

    file_path.write_text("", encoding="utf-8")

    boxes, errors = read_label_file(file_path)

    assert len(boxes) == 0
    assert len(errors) == 0


def test_read_label_file_skips_blank_lines(tmp_path: Path):
    file_path = tmp_path / "blank_lines.txt"

    file_path.write_text("1 0.5 0.4 0.1 0.2\n\n2 0.5 0.4 0.1 0.2", encoding="utf-8")

    boxes, errors = read_label_file(file_path)

    assert len(boxes) == 2
    assert len(errors) == 0
    assert boxes[0].class_id == 1
    assert boxes[1].class_id == 2


def test_read_label_file_collects_invalid_line_error(tmp_path: Path):
    file_path = tmp_path / "mixed.txt"

    file_path.write_text(
        "0 0.5 0.4 0.1 0.2\ninvalid label\n1 0.3 0.6 0.2 0.1", encoding="utf-8"
    )

    boxes, errors = read_label_file(file_path)

    assert len(boxes) == 2
    assert len(errors) == 1
    assert "mixed.txt:2:" in errors[0]
    assert "line='invalid label\\n'" in errors[0]


def test_load_class_names_from_list(tmp_path: Path):
    file_path = tmp_path / "data.yaml"

    file_path.write_text("names:\n  - car\n  - bus\n  - person", encoding="utf-8")

    names = load_class_names(file_path)

    assert names == ["car", "bus", "person"]


def test_load_class_names_from_dict(tmp_path: Path):
    file_path = tmp_path / "data.yaml"

    file_path.write_text("names:\n  0: person", encoding="utf-8")

    names = load_class_names(file_path)

    assert names == ["person"]


def test_load_class_names_from_unsorted_dict(tmp_path: Path):
    file_path = tmp_path / "data.yaml"

    file_path.write_text("names:\n  1: bus\n  0: car", encoding="utf-8")

    names = load_class_names(file_path)

    assert names == ["car", "bus"]


def test_load_class_names_missing_names_key(tmp_path: Path):
    file_path = tmp_path / "data.yaml"
    file_path.write_text("nc: 1\n", encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        load_class_names(file_path)

    assert str(file_path) in str(excinfo.value)
    assert "names" in str(excinfo.value)


def test_load_class_names_dict_non_contiguous_ids(tmp_path: Path):
    file_path = tmp_path / "data.yaml"
    file_path.write_text("names:\n  1: a\n  3: b\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_class_names(file_path)


def test_load_class_names_accepts_str_path(tmp_path: Path):
    file_path = tmp_path / "data.yaml"
    file_path.write_text("names:\n  - car\n  - bus\n", encoding="utf-8")

    assert load_class_names(str(file_path)) == ["car", "bus"]


def test_get_split_dirs_split_first(tmp_path: Path):
    root = tmp_path / "dataset"

    images_dir, labels_dir = get_split_dirs(
        root=root, split="train", layout="split-first"
    )

    assert images_dir == root / "train" / "images"
    assert labels_dir == root / "train" / "labels"


def test_get_split_dirs_type_first(tmp_path: Path):
    root = tmp_path / "dataset"

    images_dir, labels_dir = get_split_dirs(root=root, split="train", layout="type-first")

    assert images_dir == root / "images" / "train"
    assert labels_dir == root / "labels" / "train"


@pytest.mark.parametrize("layout", ["split", "type"])
def test_get_split_dirs_invalid_layout(tmp_path: Path, layout: str):
    with pytest.raises(ValueError):
        get_split_dirs(root=tmp_path / "dataset", split="train", layout=layout)


def test_match_images_to_labels_complete_pair(tmp_path: Path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"

    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    Path(images_dir / "car_1.jpg").touch()
    Path(labels_dir / "car_1.txt").touch()

    result = match_images_to_labels(images_dir, labels_dir)

    assert len(result.pairs) == 1
    assert len(result.images_without_label) == 0
    assert len(result.labels_without_image) == 0


def test_match_images_to_labels_unmatched_files(tmp_path: Path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"

    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    Path(images_dir / "car_1.jpg").touch()
    Path(labels_dir / "car_1.txt").touch()
    Path(images_dir / "car_2.jpg").touch()

    result = match_images_to_labels(images_dir, labels_dir)

    assert len(result.pairs) == 1
    assert len(result.images_without_label) == 1
    assert result.images_without_label[0].name == "car_2.jpg"
    assert len(result.labels_without_image) == 0


def test_match_images_to_labels_label_without_image(tmp_path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"

    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    Path(labels_dir / "car_2.txt").touch()

    result = match_images_to_labels(images_dir, labels_dir)

    assert len(result.pairs) == 0
    assert len(result.images_without_label) == 0
    assert len(result.labels_without_image) == 1
    assert result.labels_without_image[0].name == "car_2.txt"


def test_match_images_to_labels_missing_labels_dir(tmp_path: Path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"

    images_dir.mkdir(parents=True)

    Path(images_dir / "car_1.jpg").touch()
    Path(images_dir / "car_2.png").touch()

    result = match_images_to_labels(images_dir, labels_dir)

    assert len(result.pairs) == 0
    assert len(result.images_without_label) == 2
    assert len(result.labels_without_image) == 0


def test_match_images_to_labels_nested_directories(tmp_path: Path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"

    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    images_dir_nested = images_dir / "aachen"
    labels_dir_nested = labels_dir / "aachen"

    images_dir_nested.mkdir(parents=True)
    labels_dir_nested.mkdir(parents=True)

    (images_dir_nested / "x.png").touch()
    (labels_dir_nested / "x.txt").touch()

    result = match_images_to_labels(images_dir, labels_dir)

    assert len(result.pairs) == 1
    assert len(result.images_without_label) == 0
    assert len(result.labels_without_image) == 0


def test_match_images_to_labels_filename_with_dots(tmp_path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"

    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    (images_dir / "abc_jpg.rf.123.jpg").touch()
    (labels_dir / "abc_jpg.rf.123.txt").touch()

    result = match_images_to_labels(images_dir, labels_dir)

    assert len(result.pairs) == 1
    assert result.pairs[0][0].name == "abc_jpg.rf.123.jpg"
    assert len(result.images_without_label) == 0
    assert len(result.labels_without_image) == 0


def test_match_images_to_labels_ignores_cache_files(tmp_path: Path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"

    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    (images_dir / "car_1.jpg").touch()
    (labels_dir / "car_1.txt").touch()
    (labels_dir / "train.cache").touch()

    result = match_images_to_labels(images_dir, labels_dir)

    assert len(result.pairs) == 1
    assert len(result.images_without_label) == 0
    assert len(result.labels_without_image) == 0


def test_match_images_to_labels_duplicate_basename_raises(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    (images_dir / "cat.jpg").write_bytes(b"")
    (images_dir / "cat.png").write_bytes(b"")
    (labels_dir / "cat.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        match_images_to_labels(images_dir, labels_dir)

    message = str(excinfo.value)
    assert "duplicate key" in message
    assert "cat" in message


def test_match_images_to_labels_case_insensitive_extension(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    (images_dir / "a.JPG").write_bytes(b"")
    (labels_dir / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    result = match_images_to_labels(images_dir, labels_dir)

    assert len(result.pairs) == 1
    assert result.pairs[0][0].name == "a.JPG"
    assert len(result.images_without_label) == 0
    assert len(result.labels_without_image) == 0


@pytest.mark.parametrize(
    "line",
    [
        "0 0.0 0.0 0.1 0.1",
        "0 0.3 1.0 0.1 0.1",
        "0 0.3 0.3 1.0 0.1",
        "0 0.3 0.3 0.1 1.0",
    ],
)
def test_parse_label_line_accepts_valid_boundary_values(line: str) -> None:
    box = parse_label_line(line)
    assert box is not None


def test_compute_split_stats_instances_versus_images(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    (images_dir / "a.jpg").write_bytes(b"")
    (labels_dir / "a.txt").write_text(
        "0 0.5 0.5 0.1 0.1\n0 0.6 0.6 0.1 0.1\n", encoding="utf-8"
    )

    stats = compute_split_stats(images_dir, labels_dir)

    assert stats.instances_per_class.get(0) == 2
    assert stats.images_per_class.get(0) == 1


def test_compute_split_stats_samples_at_most_five_errors(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    (images_dir / "a.jpg").write_bytes(b"")
    invalid_lines = "\n".join(f"bad line number {i}" for i in range(8))
    (labels_dir / "a.txt").write_text(invalid_lines, encoding="utf-8")

    stats = compute_split_stats(images_dir, labels_dir)

    assert stats.n_invalid_lines == 8
    assert len(stats.sample_errors) <= 5
