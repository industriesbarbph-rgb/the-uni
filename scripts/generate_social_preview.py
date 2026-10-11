from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "social" / ".transparent-final-20261011"
OUT = ROOT / "assets" / "the-uni-social-transparent-1200x630-20261011.png"

parts = sorted(SOURCE_DIR.glob("part*.txt"))
if len(parts) != 4:
    raise RuntimeError(f"Expected 4 verified transparent source parts, found {len(parts)}")

encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
raw = base64.b64decode(encoded, validate=True)

with Image.open(BytesIO(raw)) as src:
    src.load()
    if src.format != "PNG":
        raise RuntimeError(f"Unexpected transparent source format: {src.format}")
    artwork = src.convert("RGBA")

# Keep the approved THE UNI artwork unchanged in composition and place it on
# the standard transparent 1200x630 social-preview canvas.
target_w = 1080
target_h = round(artwork.height * target_w / artwork.width)
artwork = artwork.resize((target_w, target_h), Image.Resampling.LANCZOS)

preview = Image.new("RGBA", (1200, 630), (0, 0, 0, 0))
x = (1200 - artwork.width) // 2
y = (630 - artwork.height) // 2 - 8
preview.alpha_composite(artwork, (x, y))

OUT.parent.mkdir(parents=True, exist_ok=True)
preview.save(OUT, "PNG", optimize=True, compress_level=9)

with Image.open(OUT) as check:
    check.load()
    if check.size != (1200, 630):
        raise RuntimeError(f"Unexpected social preview size: {check.size}")
    if check.format != "PNG":
        raise RuntimeError(f"Unexpected social preview format: {check.format}")
    if "A" not in check.mode:
        raise RuntimeError(f"Social preview lost transparency: {check.mode}")

print(f"Generated verified transparent THE UNI social preview: {OUT} ({OUT.stat().st_size} bytes)")
