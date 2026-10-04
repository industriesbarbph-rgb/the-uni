from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, random

W, H = 1200, 630
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "social" / "the-uni-social-preview-20261004i.jpg"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Dark cosmic base.
im = Image.new("RGBA", (W, H), (7, 6, 10, 255))
halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
hd.ellipse((190, 65, 1010, 570), fill=(112, 83, 126, 34))
halo = halo.filter(ImageFilter.GaussianBlur(105))
im = Image.alpha_composite(im, halo)

# Constellation / node language.
draw = ImageDraw.Draw(im)
pts = [(90,170),(185,110),(270,145),(1035,120),(1110,210),(980,275),
       (155,455),(275,520),(925,505),(1080,440),(575,92),(650,118)]
for a,b in [(0,1),(1,2),(3,4),(4,5),(6,7),(8,9),(10,11),(2,10),(5,11)]:
    draw.line((*pts[a], *pts[b]), fill=(211,193,168,30), width=1)
for x,y in pts:
    draw.ellipse((x-3,y-3,x+3,y+3), fill=(235,221,202,130))
    draw.ellipse((x-9,y-9,x+9,y+9), outline=(211,193,168,35), width=1)

# Render THE UNI's actual stone wordmark. Fall back to type if SVG rendering fails.
wordmark_done = False
try:
    import cairosvg
    svg = ROOT / "assets" / "the-uni-wordmark-artifact-v4.svg"
    tmp = ROOT / "social" / ".the-uni-wordmark-render.png"
    cairosvg.svg2png(url=str(svg), write_to=str(tmp), output_width=860, output_height=310)
    wm = Image.open(tmp).convert("RGBA")
    bbox = wm.getbbox()
    if bbox:
        wm = wm.crop(bbox)
    if wm.width > 850:
        s = 850 / wm.width
        wm = wm.resize((int(wm.width*s), int(wm.height*s)), Image.Resampling.LANCZOS)
    im.alpha_composite(wm, ((W-wm.width)//2, 155))
    wordmark_done = True
    tmp.unlink(missing_ok=True)
except Exception as exc:
    print("Wordmark SVG fallback:", exc)

font_regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
if not os.path.exists(font_regular):
    font_regular = None
if not os.path.exists(font_bold):
    font_bold = font_regular

if not wordmark_done:
    fallback = ImageDraw.Draw(im)
    f = ImageFont.truetype(font_bold, 150) if font_bold else ImageFont.load_default()
    label = "THE UNI"
    box = fallback.textbbox((0,0), label, font=f)
    fallback.text(((W-(box[2]-box[0]))//2, 190), label, font=f, fill=(226,195,145,255))

draw = ImageDraw.Draw(im)
small = ImageFont.truetype(font_regular, 22) if font_regular else ImageFont.load_default()
tiny = ImageFont.truetype(font_regular, 15) if font_regular else ImageFont.load_default()

subtitle = "INTERACTIVE KNOWLEDGE LIBRARY  ·  THE IMPOSSIBLE MUSEUM"
box = draw.textbbox((0,0), subtitle, font=small)
draw.text(((W-(box[2]-box[0]))//2, 435), subtitle, font=small, fill=(224,214,201,225))
draw.line((395,493,805,493), fill=(207,176,135,55), width=1)
domain = "theuni.barbph.com"
box = draw.textbbox((0,0), domain, font=tiny)
draw.text(((W-(box[2]-box[0]))//2, 518), domain, font=tiny, fill=(164,156,148,170))

# Baseline JPEG, RGB, exact OG dimensions. Deliberately NOT progressive.
im.convert("RGB").save(
    OUT,
    "JPEG",
    quality=82,
    subsampling=2,
    progressive=False,
    optimize=True,
)

# Strict decode verification: fail deployment if the image is damaged.
check = Image.open(OUT)
if check.size != (1200, 630) or check.format != "JPEG":
    raise SystemExit(f"Bad social preview geometry/format: {check.size} {check.format}")
check.load()
check.verify()
raw = OUT.read_bytes()
if not (raw[:2] == bytes([0xFF, 0xD8]) and raw[-2:] == bytes([0xFF, 0xD9])):
    raise SystemExit("Social preview JPEG is not a complete JPEG stream")
print(f"Generated valid OG image: {OUT} ({len(raw)} bytes)")
