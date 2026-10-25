from pathlib import Path

import pytest

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
    assert "2" in errors[0]


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
