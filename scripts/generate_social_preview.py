from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "the-uni-social-v2.jpg"

WIDTH = 1200
HEIGHT = 630

def font(size, bold=False, serif=False):
    if serif:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()

# Deep-space blue/black gradient.
img = Image.new("RGB", (WIDTH, HEIGHT))
px = img.load()
for y in range(HEIGHT):
    for x in range(WIDTH):
        dx = (x - WIDTH * 0.52) / WIDTH
        dy = (y - HEIGHT * 0.45) / HEIGHT
        radial = max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy) * 1.6)
        horizon = max(0.0, 1.0 - abs(y - HEIGHT * 0.72) / (HEIGHT * 0.52))
        r = int(4 + 3 * radial)
        g = int(8 + 14 * radial + 4 * horizon)
        b = int(18 + 37 * radial + 22 * horizon)
        px[x, y] = (r, g, b)

# Soft cyan beam and horizon glow.
glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for w, alpha in [(160, 8), (90, 12), (40, 20), (10, 80), (3, 180)]:
    gd.rectangle(
        [WIDTH // 2 - w // 2, 0, WIDTH // 2 + w // 2, HEIGHT],
        fill=(70, 205, 255, alpha),
    )
for h, alpha in [(90, 8), (45, 16), (14, 70), (3, 150)]:
    y = 492
    gd.rectangle([0, y - h // 2, WIDTH, y + h // 2], fill=(67, 196, 255, alpha))
glow = glow.filter(ImageFilter.GaussianBlur(14))
img = Image.alpha_composite(img.convert("RGBA"), glow)
draw = ImageDraw.Draw(img)

GOLD = (230, 196, 127, 255)
GOLD_SOFT = (188, 151, 84, 210)
IVORY = (245, 241, 229, 255)
MUTED = (169, 188, 205, 235)
CYAN = (92, 214, 255, 220)
LINE = (83, 132, 170, 105)

# Sparse constellation network: decorative, not busy.
nodes = [
    (90, 112), (175, 72), (260, 124), (355, 86), (450, 132),
    (752, 92), (842, 132), (945, 76), (1108, 120),
    (108, 515), (215, 553), (323, 520), (878, 525), (1012, 558), (1110, 510),
]
connections = [(0,1),(1,2),(2,3),(3,4),(5,6),(6,7),(7,8),(9,10),(10,11),(12,13),(13,14)]
for a, b in connections:
    draw.line([nodes[a], nodes[b]], fill=LINE, width=2)
for i, (x, y) in enumerate(nodes):
    radius = 4 if i % 3 else 5
    fill = GOLD if i % 4 == 0 else CYAN
    draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=fill)

# Main wordmark.
the_font = font(62, bold=True, serif=True)
uni_font = font(180, bold=True, serif=True)
subtitle_font = font(31, bold=True)
museum_font = font(23)
domain_font = font(22)

# Center THE + UNI as one lockup.
the_text = "THE"
uni_text = "UNI"
the_box = draw.textbbox((0, 0), the_text, font=the_font)
uni_box = draw.textbbox((0, 0), uni_text, font=uni_font)
the_w = the_box[2] - the_box[0]
uni_w = uni_box[2] - uni_box[0]
gap = 24
total_w = the_w + gap + uni_w
x0 = (WIDTH - total_w) // 2
draw.text((x0, 216), the_text, font=the_font, fill=GOLD)
draw.text((x0 + the_w + gap, 150), uni_text, font=uni_font, fill=IVORY)

# BarbPH signature sits inside the I of UNI.
barb_font = font(18, bold=True)
label_text = "BarbPH"
label_bbox = draw.textbbox((0, 0), label_text, font=barb_font)
label_w = label_bbox[2] - label_bbox[0] + 12
label_h = label_bbox[3] - label_bbox[1] + 8
label = Image.new("RGBA", (label_w, label_h), (0, 0, 0, 0))
ld = ImageDraw.Draw(label)
ld.text((6, -label_bbox[1] + 4), label_text, font=barb_font, fill=(8, 27, 50, 255))
label = label.rotate(90, expand=True)
img.alpha_composite(label, (831, 220))
draw = ImageDraw.Draw(img)

# Fine gold accent rule.
draw.rounded_rectangle([222, 382, 978, 387], radius=2, fill=GOLD_SOFT)

# Search-readable identity remains prominent.
subtitle = "INTERACTIVE KNOWLEDGE LIBRARY"
subtitle_box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
subtitle_w = subtitle_box[2] - subtitle_box[0]
draw.text(((WIDTH - subtitle_w) // 2, 411), subtitle, font=subtitle_font, fill=IVORY)

museum = "THE IMPOSSIBLE MUSEUM"
museum_box = draw.textbbox((0, 0), museum, font=museum_font)
museum_w = museum_box[2] - museum_box[0]
draw.text(((WIDTH - museum_w) // 2, 463), museum, font=museum_font, fill=MUTED)

# Footer domain.
domain = "theuni.barbph.com"
domain_box = draw.textbbox((0, 0), domain, font=domain_font)
domain_w = domain_box[2] - domain_box[0]
draw.text(((WIDTH - domain_w) // 2, 555), domain, font=domain_font, fill=MUTED)

# Small framing corners.
corner = 42
for x, y, sx, sy in [(42,42,1,1),(WIDTH-42,42,-1,1),(42,HEIGHT-42,1,-1),(WIDTH-42,HEIGHT-42,-1,-1)]:
    draw.line([(x, y), (x + sx * corner, y)], fill=GOLD_SOFT, width=2)
    draw.line([(x, y), (x, y + sy * corner)], fill=GOLD_SOFT, width=2)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.convert("RGB").save(OUT, "JPEG", quality=92, optimize=True, progressive=True)
print(f"Generated {OUT} ({OUT.stat().st_size} bytes)")
