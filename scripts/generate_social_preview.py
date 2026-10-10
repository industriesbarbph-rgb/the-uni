from pathlib import Path
import base64
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_B64 = ROOT / "social" / "the-uni-marble-preview-600x315.b64"
OUT = ROOT / "assets" / "the-uni-social-marble-20261010-1250.jpg"

encoded = SOURCE_B64.read_text(encoding="ascii").strip()
# Normalize padding because the repository text transport may preserve extra '='.
encoded = encoded.replace("=", "")
encoded += "=" * (-len(encoded) % 4)
raw = base64.b64decode(encoded)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(raw)

with Image.open(OUT) as img:
    img.verify()
with Image.open(OUT) as img:
    if img.size != (600, 315):
        raise RuntimeError(f"Unexpected social preview size: {img.size}")
    if img.format != "JPEG":
        raise RuntimeError(f"Unexpected social preview format: {img.format}")

print(f"Generated {OUT} from approved marble artwork ({OUT.stat().st_size} bytes)")
