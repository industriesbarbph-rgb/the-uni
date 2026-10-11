from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "the-uni-wordmark-preview.png"
OUT = ROOT / "assets" / "the-uni-social-transparent-1200x630-20261011.png"

CANVAS_W = 1200
CANVAS_H = 630
MAX_ART_W = 1080
MAX_ART_H = 420

with Image.open(SOURCE) as src:
    src.load()
    src = src.convert("RGBA")

    # Keep the approved transparent THE UNI artwork exactly as-is;
    # only remove empty transparent margins before fitting it to the social canvas.
    alpha = src.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        raise RuntimeError("Approved THE UNI transparent source contains no visible pixels")

    artwork = src.crop(bbox)

    scale = min(MAX_ART_W / artwork.width, MAX_ART_H / artwork.height)
    target = (
        max(1, round(artwork.width * scale)),
        max(1, round(artwork.height * scale)),
    )
    artwork = artwork.resize(target, Image.Resampling.LANCZOS)

    preview = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    x = (CANVAS_W - artwork.width) // 2
    y = (CANVAS_H - artwork.height) // 2 - 8
    preview.alpha_composite(artwork, (x, y))

OUT.parent.mkdir(parents=True, exist_ok=True)
preview.save(OUT, "PNG", optimize=True, compress_level=9)

with Image.open(OUT) as check:
    check.load()
    if check.size != (CANVAS_W, CANVAS_H):
        raise RuntimeError(f"Unexpected social preview size: {check.size}")
    if check.format != "PNG":
        raise RuntimeError(f"Unexpected social preview format: {check.format}")
    if check.mode not in ("RGBA", "LA"):
        raise RuntimeError(f"Social preview lost transparency: {check.mode}")

print(f"Generated transparent THE UNI social preview: {OUT} ({OUT.stat().st_size} bytes)")
