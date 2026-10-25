from pathlib import Path

import numpy as np
from PIL import Image


def load_thumbnail(image_path: Path, size: tuple[int, int] = (32, 18)) -> np.ndarray:
    with Image.open(image_path) as img:
        image = img.convert("L")
        image = image.resize(size)
        return np.array(image, dtype=np.float32).ravel() / np.float32(255.0)


def build_thumbnail_matrix(
    paths: list[Path], size: tuple[int, int] = (32, 18)
) -> np.ndarray:
    list_of_thumbnails = []

    if len(paths) == 0:
        return np.empty((0, size[0] * size[1]), dtype=np.float32)

    for path in paths:
        thumbnail = load_thumbnail(path, size=size)
        list_of_thumbnails.append(thumbnail)

    return np.stack(list_of_thumbnails, axis=0)
