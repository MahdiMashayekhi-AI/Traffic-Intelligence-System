from pathlib import Path

import numpy as np
from PIL import Image

from traffic_intelligence_system.data.thumbnails import (
    build_thumbnail_matrix,
    load_thumbnail,
)


def test_load_thumbnail(tmp_path: Path):
    image_path = tmp_path / "test_image.png"

    img = Image.new("RGB", (64, 32), color=(255, 0, 0))
    img.save(image_path)

    thumbnail = load_thumbnail(image_path, size=(32, 18))

    assert thumbnail.shape == (32 * 18,)
    assert thumbnail.dtype == np.float32
    assert np.all((thumbnail >= 0) & (thumbnail <= 1))


def test_build_thumbnail_matrix(tmp_path: Path):
    image_paths = []

    for i in range(3):
        image_path = tmp_path / f"test_image_{i}.png"
        img = Image.new("RGB", (64, 32), color=(255, 0, 0))
        img.save(image_path)
        image_paths.append(image_path)

    thumbnail_matrix = build_thumbnail_matrix(image_paths, size=(32, 18))

    assert thumbnail_matrix.shape == (3, 32 * 18)
    assert thumbnail_matrix.dtype == np.float32


def test_build_thumbnail_matrix_empty():
    thumbnail_matrix = build_thumbnail_matrix([], size=(32, 18))

    assert thumbnail_matrix.shape == (0, 32 * 18)
    assert thumbnail_matrix.dtype == np.float32
