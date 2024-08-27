from PIL import Image, ImageChops


def crop_borders(img):
    img_rgb = img.convert("RGB")
    bg = Image.new("RGB", img_rgb.size, img_rgb.getpixel((0, 0)))
    diff = ImageChops.difference(img_rgb, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return img_rgb.crop(bbox)
    else:
        print('Warning: no image borders crop happened')
        return img


def split_image_vertical(img):
    w, h = img.size
    return img.crop((0, 0, w/2, h)), img.crop((w/2, 0, w, h))

