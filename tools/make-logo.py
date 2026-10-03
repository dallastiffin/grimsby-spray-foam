#!/usr/bin/env python3
"""
Regenerate every logo asset from the master Logo.png.

    python tools/make-logo.py

The Grimsby logo is a single round badge (the house-and-foam mark
marking stripe, with the business name inside the ring) rather than a
wordmark-plus-icon lockup, so there is nothing to split. The badge is used everywhere: header icon,
favicons, schema logo and the footer mark. White outside the ring is knocked
out so the badge sits cleanly on the dark footer.

Outputs into site/images/
    icon-{16,32,48,64,96,180,192,512}.png   header logo + favicons
    favicon.ico                             multi-resolution, legacy browsers
    logo.png / logo.jpg                     512px badge, for schema.org
    wordmark-{300,600}.png                  badge on transparent, light backgrounds
    wordmark-light-{300,600}.png            same badge, used in the footer
"""
from PIL import Image
from collections import deque
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "Logo.png")
IMG  = os.path.join(ROOT, "site", "images")


def clear_outside(img, thresh=225):
    """Flood-fill transparency inward from the border. Only white that is
    connected to an outside edge is removed, so the white lettering inside
    the ring survives."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    seen = bytearray(w * h)
    q = deque()

    def is_white(x, y):
        r, g, b, _ = px[x, y]
        return r >= thresh and g >= thresh and b >= thresh

    for x in range(w):
        for y in (0, h - 1):
            if is_white(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_white(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    while q:
        x, y = q.popleft()
        px[x, y] = (255, 255, 255, 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and is_white(nx, ny):
                seen[ny * w + nx] = 1
                q.append((nx, ny))
    return img.crop(img.getbbox())


def save_png(img, path, colors=128):
    rgba = img.convert("RGBA")
    alpha = rgba.split()[-1]
    out = rgba.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT).convert("RGBA")
    out.putalpha(alpha)
    out.save(path, optimize=True)


def main():
    os.makedirs(IMG, exist_ok=True)
    badge = clear_outside(Image.open(SRC))
    side = max(badge.size) + 8
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(badge, ((side - badge.width) // 2, (side - badge.height) // 2), badge)

    for size in (512, 192, 180, 96, 64, 48, 32, 16):
        save_png(sq.resize((size, size), Image.LANCZOS),
                 os.path.join(IMG, "icon-%d.png" % size))
        print("  icon-%d.png" % size)

    big = sq.resize((512, 512), Image.LANCZOS)
    save_png(big, os.path.join(IMG, "logo.png"))
    flat = Image.new("RGB", big.size, (255, 255, 255))
    flat.paste(big, mask=big.split()[-1])
    flat.save(os.path.join(IMG, "logo.jpg"), "JPEG", quality=88, optimize=True)
    sq.resize((256, 256), Image.LANCZOS).save(
        os.path.join(IMG, "favicon.ico"),
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("  favicon.ico, logo.png, logo.jpg")

    for w in (600, 300):
        save_png(sq.resize((w, w), Image.LANCZOS), os.path.join(IMG, "wordmark-%d.png" % w))
        save_png(sq.resize((w, w), Image.LANCZOS), os.path.join(IMG, "wordmark-light-%d.png" % w))
        print("  wordmark-%d.png, wordmark-light-%d.png" % (w, w))

    print("\nDone. Run 'python build.py' to refresh the cache fingerprints.")


if __name__ == "__main__":
    main()
