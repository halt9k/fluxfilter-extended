from enum import Enum, auto

import numpy as np
from PIL import Image, ImageChops


def crop_borders(img, margin=5):
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


def split_image_vertical(img):
    w, h = img.size
    return img.crop((0, 0, w/2, h)), img.crop((w/2, 0, w, h))


class Direction(Enum):
    VERTICAL, HORIZONTAL = 1, 2


def remove_white_strip(img: np.array, direction: Direction, percent_from, percent_to):
    img = Image.open('image.jpg').convert('RGB')

    crop = img.crop((x1, y1, x2, y2))
    pixels = np.array(crop)

    is_white = np.all(pixels == [255, 255, 255])
