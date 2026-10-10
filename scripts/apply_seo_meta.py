from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

SITE_URL = "https://theuni.barbph.com/"
SEO_TITLE = "THE UNI | Interactive Learning Library, Visual Guides & Quizzes"
SOCIAL_TITLE = "THE UNI — Interactive Knowledge Library"
DESCRIPTION = (
    "Explore interactive learning, visual guides, knowledge maps, educational models, "
    "and quizzes across science, engineering, technology, business, and psychology."
)
IMAGE_URL = "https://theuni.barbph.com/assets/the-uni-social-marble-20261010-1305.jpg"

META_KEYS = [
    "description",
    "robots",
    "og:type",
    "og:site_name",
    "og:locale",
    "og:url",
    "og:title",
    "og:description",
    "og:image",
    "og:image:url",
    "og:image:secure_url",
    "og:image:type",
    "og:image:width",
    "og:image:height",
    "og:image:alt",
    "twitter:card",
    "twitter:url",
    "twitter:title",
    "twitter:description",
    "twitter:image",
    "twitter:image:alt",
]

def remove_meta_tag(html: str, key: str) -> str:
    escaped = re.escape(key)
    pattern = (
        r"<meta\b"
        r"(?=[^>]*(?:name|property)\s*=\s*(?:\"" + escaped + r"\"|'" + escaped + r"'))"
        r"[^>]*>\s*"
    )
    return re.sub(pattern, "", html, flags=re.IGNORECASE)

html = INDEX.read_text(encoding="utf-8")

html = re.sub(
    r"\s*<!-- THE UNI SEO START -->.*?<!-- THE UNI SEO END -->\s*",
    "\n",
    html,
    flags=re.IGNORECASE | re.DOTALL,
)

html = re.sub(r"<title\b[^>]*>.*?</title>\s*", "", html, flags=re.IGNORECASE | re.DOTALL)
html = re.sub(
    r"<link\b(?=[^>]*\brel\s*=\s*(?:\"canonical\"|'canonical'))[^>]*>\s*",
    "",
    html,
    flags=re.IGNORECASE,
)
html = re.sub(
    r"<link\b(?=[^>]*\brel\s*=\s*(?:\"image_src\"|'image_src'))[^>]*>\s*",
    "",
    html,
    flags=re.IGNORECASE,
)
html = re.sub(
    r"<meta\b(?=[^>]*\bitemprop\s*=\s*(?:\"image\"|'image'))[^>]*>\s*",
    "",
    html,
    flags=re.IGNORECASE,
)
for key in META_KEYS:
    html = remove_meta_tag(html, key)

schema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "THE UNI",
    "alternateName": "THE UNI — Interactive Knowledge Library",
    "url": SITE_URL,
    "description": DESCRIPTION,
    "inLanguage": "en",
    "about": [
        "interactive learning",
        "visual learning",
        "science",
        "engineering",
        "technology",
        "business",
        "psychology",
    ],
}

block = f'''<!-- THE UNI SEO START -->
<title>{SEO_TITLE}</title>
<meta name="description" content="{DESCRIPTION}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{SITE_URL}">
<link rel="image_src" href="{IMAGE_URL}">
<meta itemprop="image" content="{IMAGE_URL}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="THE UNI">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:title" content="{SOCIAL_TITLE}">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:image" content="{IMAGE_URL}">
<meta property="og:image:url" content="{IMAGE_URL}">
<meta property="og:image:secure_url" content="{IMAGE_URL}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="600">
<meta property="og:image:height" content="315">
<meta property="og:image:alt" content="THE UNI marble monument — by barb the builder">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:url" content="{SITE_URL}">
<meta name="twitter:title" content="{SOCIAL_TITLE}">
<meta name="twitter:description" content="{DESCRIPTION}">
<meta name="twitter:image" content="{IMAGE_URL}">
<meta name="twitter:image:alt" content="THE UNI marble monument — by barb the builder">

<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":"))}</script>
<!-- THE UNI SEO END -->
'''

charset_match = re.search(
    r"<meta\b[^>]*\bcharset\s*=\s*(?:\"[^\"]+\"|'[^']+'|[^\s>]+)[^>]*>\s*",
    html,
    flags=re.IGNORECASE,
)
if charset_match:
    insert_at = charset_match.end()
else:
    head_match = re.search(r"<head\b[^>]*>\s*", html, flags=re.IGNORECASE)
    if not head_match:
        raise RuntimeError("Could not find <head> in index.html")
    insert_at = head_match.end()

html = html[:insert_at] + block + html[insert_at:]
INDEX.write_text(html, encoding="utf-8")

print("Applied THE UNI SEO and social metadata")
print(f"SEO title: {SEO_TITLE}")
print(f"Social title: {SOCIAL_TITLE}")
print(f"Social image: {IMAGE_URL}")
