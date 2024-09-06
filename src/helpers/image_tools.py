from enum import Enum, auto

import numpy as np
from PIL import Image, ImageChops


class Direction(Enum):
    VERTICAL, HORIZONTAL = 1, 2


def crop_borders(img, margin=10):
    img_rgb = img.convert("RGB")
    bg = Image.new("RGB", img_rgb.size, img_rgb.getpixel((0, 0)))
    diff = ImageChops.difference(img_rgb, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()

    if bbox:
        if img.getbbox() != bbox:
            bbox = (bbox[0] - margin, bbox[1] - margin, bbox[2] + margin, bbox[3] + margin )
        return img.crop(bbox)
    else:
        print('Warning: image borders crop failed')
        return img


def split_image(img: Image, direction: Direction, n):
    assert n > 0
    w, h = img.size

    # crop: left, upper, right, lower
    imgs = []
    if direction == Direction.HORIZONTAL:
        imgs = [img.crop((w * i / n, 0, w * (i + 1) / n, h)) for i in range(n)]
    elif direction == Direction.VERTICAL:
        imgs = [img.crop((0, h * i / n, w, h * (i + 1) / n)) for i in range(n)]

    return imgs


def remove_white_strip(img: np.array, direction: Direction, percent_from, percent_to):
    img = Image.open('image.jpg').convert('RGB')

    crop = img.crop((x1, y1, x2, y2))
    pixels = np.array(crop)

    is_white = np.all(pixels == [255, 255, 255])
