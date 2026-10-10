from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "social" / "the-uni-social-preview-20261004i.jpg"
OUT = ROOT / "assets" / "the-uni-social-20261010-1116.jpg"

WIDTH = 1200
HEIGHT = 630

src = Image.open(SOURCE).convert("RGB")
scale = min(WIDTH / src.width, HEIGHT / src.height)
new_size = (
    max(1, round(src.width * scale)),
    max(1, round(src.height * scale)),
)
resized = src.resize(new_size, Image.Resampling.LANCZOS)

# Keep the approved image uncropped and extend the dark background at the sides
# to fit the standard 1200x630 social-preview canvas.
canvas = Image.new("RGB", (WIDTH, HEIGHT), (5, 5, 5))
x = (WIDTH - new_size[0]) // 2
y = (HEIGHT - new_size[1]) // 2
canvas.paste(resized, (x, y))

OUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUT, "JPEG", quality=92, optimize=True, progressive=False)
print(f"Generated {OUT} from {SOURCE} ({OUT.stat().st_size} bytes)")
