from pathlib import Path

from traffic_intelligence_system.data.stats import (
    SplitStats,
    compute_split_stats,
    count_instances,
    stats_to_markdown,
)


def test_compute_split_stats(tmp_path: Path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"

    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    (images_dir / "a.jpg").write_bytes(b"")
    (images_dir / "b.jpg").write_bytes(b"")
    (images_dir / "c.jpg").write_bytes(b"")

    (labels_dir / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n4 0.3 0.3 0.1 0.1")

    (labels_dir / "b.txt").write_text("")

    (labels_dir / "orphan.txt").write_text("0 0.5 0.5 0.2 0.2\noops")

    stats = compute_split_stats(images_dir, labels_dir)

    assert stats.n_images == 3
    assert stats.n_label_files == 3
    assert stats.n_matched == 2
    assert stats.n_images_without_label == 1
    assert stats.n_labels_without_image == 1
    assert stats.n_empty_labels == 1
    assert stats.n_invalid_lines == 1
    assert stats.instances_per_class == {0: 2, 4: 1}
    assert stats.images_per_class == {0: 2, 4: 1}
    assert stats.median_w_per_class[0] == 0.2


def test_count_instances(tmp_path: Path):
    labels_dir = tmp_path / "labels"

    labels_dir.mkdir(parents=True)

    (labels_dir / "a.txt").write_text("0 0.2 0.6 0.7 0.1\n0 0.2 0.6 0.7 0.1")

    (labels_dir / "b.txt").write_text("4 0.3 0.5 0.9 0.7\noops")

    counts = count_instances(labels_dir)

    assert counts == {0: 2, 4: 1}


def test_count_instances_empty_dir(tmp_path: Path):
    empty_dir = tmp_path / "empty"

    empty_dir.mkdir(parents=True)

    counts = count_instances(empty_dir)

    assert counts == {}


def test_count_instances_missing_dir(tmp_path: Path):
    missing_dir = tmp_path / "missing"

    counts = count_instances(missing_dir)

    assert counts == {}


def test_stats_to_markdown_returns_string_with_headers():
    stats = SplitStats(
        n_images=10,
        n_label_files=8,
        n_matched=7,
        n_images_without_label=3,
        n_labels_without_image=1,
        n_empty_labels=2,
        n_invalid_lines=4,
        instances_per_class={0: 5},
        images_per_class={0: 3},
        median_w_per_class={0: 0.3},
        median_h_per_class={0: 0.5},
    )
    md = stats_to_markdown({"train": stats}, ["car"])

    assert isinstance(md, str)
    assert "train" in md
    assert "images" in md
    assert "label files" in md
    assert "matched" in md
    assert "empty labels" in md
    assert "invalid lines" in md
    assert "class" in md
    assert "instances" in md
    assert "median w" in md
    assert "median h" in md


def test_stats_to_markdown_class_names():
    stats = SplitStats(
        instances_per_class={0: 5, 4: 2},
        images_per_class={0: 3, 4: 1},
        median_w_per_class={0: 0.3, 4: 0.4},
        median_h_per_class={0: 0.5, 4: 0.6},
    )
    md = stats_to_markdown({"train": stats}, ["car"])

    assert "car" in md
    assert "class_4" in md
    assert "| car " in md
    assert "| class_4 " in md


def test_stats_to_markdown_no_boxes():
    stats = SplitStats()
    md = stats_to_markdown({"train": stats}, ["car"])

    assert isinstance(md, str)
    assert "train" in md
