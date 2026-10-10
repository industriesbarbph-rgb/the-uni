from pathlib import Path
import base64
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "social" / ".marble-fullbleed-20261010"
OUT = ROOT / "assets" / "the-uni-social-marble-fullbleed-20261010.jpg"

parts = [SOURCE_DIR / f"part{i:02d}.txt" for i in range(4)]
for part in parts:
    if not part.exists():
        raise RuntimeError(f"Missing marble preview source part: {part.name}")

encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
raw = base64.b64decode(encoded, validate=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(raw)

with Image.open(OUT) as img:
    img.load()
    if img.size != (1200, 630):
        raise RuntimeError(f"Unexpected social preview size: {img.size}")
    if img.format != "JPEG":
        raise RuntimeError(f"Unexpected social preview format: {img.format}")

if OUT.stat().st_size < 30000:
    raise RuntimeError(f"Social preview is suspiciously small: {OUT.stat().st_size} bytes")

print(f"Generated valid {OUT} full-bleed marble preview ({OUT.stat().st_size} bytes)")
