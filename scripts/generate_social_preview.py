from pathlib import Path
import base64
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "social" / ".marble-final-v2"
OUT = ROOT / "assets" / "the-uni-social-marble-20261010-1305.jpg"

parts = sorted(SOURCE_DIR.glob("part*.txt"))
if len(parts) != 6:
    raise RuntimeError(f"Expected 6 marble preview source parts, found {len(parts)}")

encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
raw = base64.b64decode(encoded, validate=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(raw)

# Fully decode the JPEG so a truncated/broken stream fails the deploy.
with Image.open(OUT) as img:
    img.load()
    if img.size != (600, 315):
        raise RuntimeError(f"Unexpected social preview size: {img.size}")
    if img.format != "JPEG":
        raise RuntimeError(f"Unexpected social preview format: {img.format}")

if OUT.stat().st_size < 8000:
    raise RuntimeError(f"Social preview is suspiciously small: {OUT.stat().st_size} bytes")

print(f"Generated valid {OUT} from approved marble artwork ({OUT.stat().st_size} bytes)")
