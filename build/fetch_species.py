"""Make the salmon species images in species/*.webp.

Sea phase: photos from the "BC Wild Salmon Identification Guide" PDF. The photos are
© Washington Department of Fish and Wildlife (WDFW), all rights reserved; WDFW allows
non-commercial, informational copies with its reproduction notice (https://wdfw.wa.gov/privacy).
Spawning phase: public-domain drawings from Wikimedia Commons (U.S. Government works).
assemble.py inlines species/*.webp into the page. Run this script only to change an image.

Usage: python fetch_species.py path/to/salmon_species_chart.pdf
Needs Pillow with WebP support and pypdf.
"""
import io, os, sys, requests
from PIL import Image, ImageChops
from pypdf import PdfReader

# file name -> (Commons file title, flip so that the fish faces right)
IMAGES = {
    "chinook-spawn": ("Lake Washington Ship Canal Fish Ladder pamphlet - male freshwater phase Chinook.jpg", False),
    "coho-spawn":    ("Lake Washington Ship Canal Fish Ladder pamphlet - male freshwater phase Coho.jpg", False),
    "sockeye-spawn": ("Lake Washington Ship Canal Fish Ladder pamphlet - male freshwater phase Sockeye.jpg", False),
    "pink-spawn":    ("Pink salmon FWS.jpg", False),
    "chum-spawn":    ("Salmon chum fish oncorhynchus keta.jpg", False),
}
# file name -> image name in the PDF. The PDF photos face left, so all of them are flipped.
PHOTOS = {
    "chum-ocean":    "Im0.jpg",
    "sockeye-ocean": "Im1.jpg",
    "coho-ocean":    "Im2.jpg",
    "chinook-ocean": "Im3.jpg",
    "pink-ocean":    "Im4.jpg",
}
WIDTH = 640     # about 2x the card width in the side panel
HEADERS = {"User-Agent": "bc-salmon-map-build/1.0 (https://github.com/volkotyk/bc-salmon-map)"}


def trim(im):
    """Cut the near-white margin around the drawing."""
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 24 else 0)
    box = diff.getbbox()
    return im.crop(box) if box else im


def save(name, im, flip):
    im = trim(im.convert("RGB"))
    if flip:
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.Resampling.LANCZOS)
    path = f"species/{name}.webp"
    im.save(path, "WEBP", quality=72, method=6)
    print(path, im.size, os.path.getsize(path), "bytes")


if len(sys.argv) != 2:
    sys.exit(__doc__)
os.makedirs("species", exist_ok=True)
pdf = {im.name: im.image for im in PdfReader(sys.argv[1]).pages[0].images}
for name, key in PHOTOS.items():
    save(name, pdf[key], True)
for name, (title, flip) in IMAGES.items():
    r = requests.get("https://commons.wikimedia.org/wiki/Special:FilePath/" + title,
                     params={"width": 1200}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    save(name, Image.open(io.BytesIO(r.content)), flip)
