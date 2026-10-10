from pathlib import Path
import base64
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "social" / ".marble-final-v2"
OUT = ROOT / "assets" / "the-uni-social-marble-fullbleed-20261010.jpg"

parts = sorted(SOURCE_DIR.glob("part*.txt"))
if len(parts) != 6:
    raise RuntimeError(f"Expected 6 verified marble source parts, found {len(parts)}")

encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
raw = base64.b64decode(encoded, validate=True)

with Image.open(BytesIO(raw)) as src:
    src.load()
    if src.format != "JPEG":
        raise RuntimeError(f"Unexpected source format: {src.format}")
    src = src.convert("RGB")

    # Remove the black frame around the approved marble artwork.
    gray = ImageOps.grayscale(src)
    mask = gray.point(lambda p: 255 if p > 24 else 0)
    bbox = mask.getbbox()
    if not bbox:
        raise RuntimeError("Could not locate marble artwork inside source image")

    left, top, right, bottom = bbox
    pad = 3
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(src.width, right + pad)
    bottom = min(src.height, bottom + pad)
    artwork = src.crop((left, top, right, bottom))

    # Fill the 1200x630 social canvas edge-to-edge while preserving every letter.
    preview = artwork.resize((1200, 630), Image.Resampling.LANCZOS)
    preview = preview.filter(ImageFilter.UnsharpMask(radius=1.1, percent=135, threshold=2))

OUT.parent.mkdir(parents=True, exist_ok=True)
preview.save(OUT, "JPEG", quality=95, subsampling=0, optimize=True)

with Image.open(OUT) as check:
    check.load()
    if check.size != (1200, 630):
        raise RuntimeError(f"Unexpected social preview size: {check.size}")
    if check.format != "JPEG":
        raise RuntimeError(f"Unexpected social preview format: {check.format}")

if OUT.stat().st_size < 25000:
    raise RuntimeError(f"Social preview is suspiciously small: {OUT.stat().st_size} bytes")

print(f"Generated sharp full-bleed {OUT} ({OUT.stat().st_size} bytes)")
