"""Download the salmon species illustrations from Wikimedia Commons into species/*.webp.

All images are in the public domain (U.S. Government works and a 1907 U.S. Bureau of Fisheries report).
assemble.py inlines species/*.webp into the page. Run this script only to change an image.

Needs Pillow with WebP support.
"""
import io, os, requests
from PIL import Image, ImageChops

# file name -> (Commons file title, flip so that the fish faces right)
IMAGES = {
    "chinook-ocean": ("Lake Washington Ship Canal Fish Ladder pamphlet - ocean phase Chinook.jpg", False),
    "chinook-spawn": ("Lake Washington Ship Canal Fish Ladder pamphlet - male freshwater phase Chinook.jpg", False),
    "coho-ocean":    ("Lake Washington Ship Canal Fish Ladder pamphlet - ocean phase Coho.jpg", False),
    "coho-spawn":    ("Lake Washington Ship Canal Fish Ladder pamphlet - male freshwater phase Coho.jpg", False),
    "sockeye-ocean": ("Lake Washington Ship Canal Fish Ladder pamphlet - ocean phase Sockeye.jpg", False),
    "sockeye-spawn": ("Lake Washington Ship Canal Fish Ladder pamphlet - male freshwater phase Sockeye.jpg", False),
    "pink-ocean":    ("Humpback Salmon Adult Male.jpg", True),
    "pink-spawn":    ("Pink salmon FWS.jpg", False),
    "chum-spawn":    ("Salmon chum fish oncorhynchus keta.jpg", False),
}
WIDTH = 640     # about 2x the card width in the side panel
HEADERS = {"User-Agent": "bc-salmon-map-build/1.0 (https://github.com/volkotyk/bc-salmon-map)"}


def trim(im):
    """Cut the near-white margin around the drawing."""
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 24 else 0)
    box = diff.getbbox()
    return im.crop(box) if box else im


os.makedirs("species", exist_ok=True)
for name, (title, flip) in IMAGES.items():
    r = requests.get("https://commons.wikimedia.org/wiki/Special:FilePath/" + title,
                     params={"width": 1200}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    im = trim(Image.open(io.BytesIO(r.content)).convert("RGB"))
    if flip:
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.Resampling.LANCZOS)
    path = f"species/{name}.webp"
    im.save(path, "WEBP", quality=72, method=6)
    print(path, im.size, os.path.getsize(path), "bytes")
