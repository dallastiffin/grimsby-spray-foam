#!/usr/bin/env python3
"""
Regenerate every logo asset from the master Logo.png.

    python tools/make-logo.py

Logo.png is a horizontal lockup: the house-section mark (charcoal outline,
rust foam fill with a scalloped top) on the left, "GRIMSBY / SPRAY FOAM
INSULATION" on the right, on white.

The previous version of this script padded the whole lockup into a square,
which made the header logo and every favicon an unreadable smear. This one
splits the lockup properly:

Outputs into site/images/
    lockup-{240,480}.png         tight-cropped full lockup, transparent, header
    lockup-light-{240,480}.png   same, charcoal turned white, for the dark footer
    icon-{16,32,48,64,96,180,192,512}.png   the house mark alone, favicons
    favicon.ico                  multi-resolution, legacy browsers
    logo.png / logo.jpg          512px mark on white, for schema.org
    wordmark-*.png               kept as aliases of the lockup so nothing old 404s
"""
from PIL import Image
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "Logo.png")
IMG  = os.path.join(ROOT, "site", "images")

CHARCOAL = (46, 43, 39)


def knock_out_white(img, thresh=235):
    """White to transparent, with a soft edge so anti-aliasing survives."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            m = min(r, g, b)
            if m >= thresh:
                px[x, y] = (r, g, b, 0)
            elif m > 190:
                # partial: fade toward transparent as it approaches white
                k = (m - 190) / float(thresh - 190)
                px[x, y] = (r, g, b, int(a * (1 - k)))
    return img


def bbox_of(img):
    return img.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()


def main():
    os.makedirs(IMG, exist_ok=True)
    src = knock_out_white(Image.open(SRC))
    lock = src.crop(bbox_of(src))

    # The mark is the left cluster: find the first fully empty column gap.
    alpha = lock.getchannel("A")
    w, h = lock.size
    cols = [any(alpha.getpixel((x, y)) > 24 for y in range(0, h, 2)) for x in range(w)]
    gap_start = None
    for x in range(int(w * 0.1), w):
        if not cols[x]:
            gap_start = x
            break
    mark = lock.crop((0, 0, gap_start, h))
    mark = mark.crop(bbox_of(mark))

    # Lockups
    for height in (240, 480):
        ww = int(round(lock.width * height / lock.height))
        lock.resize((ww, height), Image.LANCZOS).save(
            os.path.join(IMG, "lockup-%d.png" % height), optimize=True)
    light = lock.copy()
    lp = light.load()
    for y in range(light.height):
        for x in range(light.width):
            r, g, b, a = lp[x, y]
            if a and abs(r - CHARCOAL[0]) < 40 and abs(g - CHARCOAL[1]) < 40 and abs(b - CHARCOAL[2]) < 40:
                lp[x, y] = (255, 255, 255, a)
            elif a and x > gap_start and r > g + 40:
                # rust tagline is too dark to read on charcoal; cured-foam tone instead
                lp[x, y] = (235, 217, 166, a)
    for height in (240, 480):
        ww = int(round(light.width * height / light.height))
        light.resize((ww, height), Image.LANCZOS).save(
            os.path.join(IMG, "lockup-light-%d.png" % height), optimize=True)

    # Square mark for icons, with breathing room
    side = int(max(mark.size) * 1.18)
    # Opaque white tile: a transparent mark loses its charcoal outline on a
    # dark browser tab or home screen.
    sq = Image.new("RGBA", (side, side), (255, 255, 255, 255))
    sq.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2), mark)
    for s in (16, 32, 48, 64, 96, 180, 192, 512):
        sq.resize((s, s), Image.LANCZOS).save(os.path.join(IMG, "icon-%d.png" % s), optimize=True)
    sq.resize((48, 48), Image.LANCZOS).save(
        os.path.join(IMG, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

    on_white = Image.new("RGB", (512, 512), (255, 255, 255))
    big = sq.resize((512, 512), Image.LANCZOS)
    on_white.paste(big, (0, 0), big)
    big.save(os.path.join(IMG, "logo.png"), optimize=True)
    on_white.save(os.path.join(IMG, "logo.jpg"), quality=90)

    # Legacy names, so any cached page or external reference still resolves
    for n, src_name in (("wordmark-300.png", "lockup-240.png"),
                        ("wordmark-600.png", "lockup-480.png"),
                        ("wordmark-light-300.png", "lockup-light-240.png"),
                        ("wordmark-light-600.png", "lockup-light-480.png")):
        Image.open(os.path.join(IMG, src_name)).save(os.path.join(IMG, n), optimize=True)
    print("logo assets written; lockup %dx%d, mark %dx%d" % (lock.width, lock.height, mark.width, mark.height))


if __name__ == "__main__":
    main()
