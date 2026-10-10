from pathlib import Path
import base64
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_B64 = ROOT / "social" / "the-uni-marble-preview-20261010.b64"
OUT = ROOT / "assets" / "the-uni-social-marble-20261010-1230.jpg"

raw = base64.b64decode(SOURCE_B64.read_text(encoding="ascii").strip())
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(raw)

# Fail the deploy if the committed social-preview source is not the expected
# standard Open Graph canvas.
with Image.open(OUT) as img:
    if img.size != (1200, 630):
        raise RuntimeError(f"Unexpected social preview size: {img.size}")
    if img.format != "JPEG":
        raise RuntimeError(f"Unexpected social preview format: {img.format}")

print(f"Generated {OUT} from approved marble artwork ({OUT.stat().st_size} bytes)")
