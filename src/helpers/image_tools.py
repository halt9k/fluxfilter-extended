from enum import Enum, auto
from logging import warning

import numpy as np
from PIL import Image, ImageChops, ImageColor


class Direction(Enum):
    VERTICAL, HORIZONTAL = 1, 2


def crop_monocolor_borders(img, sides='LTRB', col=None,  margin=10):
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size

    edge_cols = list(map(img_rgb.getpixel, [(0, 0), (w - 1, h - 1), (w - 1, 0), (0, h - 1)]))
    if len(set(edge_cols)) > 1:
        warning('Cannot crop image, border color inconsistent')
        return img

    if not col:
        col = img_rgb.getpixel((0, 0))

    bg = Image.new("RGB", img_rgb.size, col)
    diff = ImageChops.difference(img_rgb, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)

    bbox_crop = diff.getbbox()
    bbox = img_rgb.getbbox()

    if not bbox_crop:
        warning('Cannot crop image, border color inconsistent')
        return img

    bbox_crop_mg = (max(bbox_crop[0] - margin, 0),  max(bbox_crop[1] - margin, 0),
                    min(bbox_crop[2] + margin, bbox[2]),min(bbox_crop[3] + margin, bbox[3]))
    mask = np.array(['L' in sides, 'T' in sides, 'R' in sides, 'B' in sides])
    bbox_final = tuple(np.where(mask, bbox_crop_mg, bbox))
    return img.crop(bbox_final)


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


def grid_images(images, max_horiz=np.iinfo(int).max):
    # combines images in row or column depending on max_horiz arg

    n_images = len(images)
    n_horiz = min(n_images, max_horiz)
    h_sizes, v_sizes = [0] * n_horiz, [0] * (n_images // n_horiz)
    for i, im in enumerate(images):
        h, v = i % n_horiz, i // n_horiz
        h_sizes[h] = max(h_sizes[h], im.size[0])
        v_sizes[v] = max(v_sizes[v], im.size[1])

    h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
    im_grid = Image.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
    for i, im in enumerate(images):
        im_grid.paste(im, (h_sizes[i % n_horiz], v_sizes[i // n_horiz]))
    return im_grid


def remove_strip(img: np.array, strip_axis: Direction, percent_at, margin=10):
    # cuts an image on two and crops space from cut side on both

    w, h = img.size
    assert 0 <= percent_at <= 1

    if strip_axis == Direction.VERTICAL:
        imgs = [img.crop((0, 0, w * percent_at, h)),
                img.crop((w * percent_at, 0, w, h))]
        imgs = [crop_monocolor_borders(imgs[0], sides='R', margin=margin),
                crop_monocolor_borders(imgs[1], sides='L', margin=margin)]
        return grid_images(imgs, 2)
    elif strip_axis == Direction.HORIZONTAL:
        imgs = [img.crop((0, 0, w, h * percent_at)),
                img.crop((0, h * percent_at, w, h))]
        imgs = [crop_monocolor_borders(imgs[0], sides='B', margin=margin),
                crop_monocolor_borders(imgs[1], sides='T', margin=margin)]
        return grid_images(imgs, 1)
