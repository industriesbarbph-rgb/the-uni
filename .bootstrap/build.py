#!/usr/bin/env python3
import base64, concurrent.futures, pathlib, re, shutil, time, urllib.request, xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOT = ROOT / '.bootstrap'
STAGE = BOOT / 'stage'
BASE = 'https://ikl.barbph.com/'
NEW = 'https://theuni.barbph.com/'

def get(url, attempts=6):
    last = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'THE-UNI-Migration/2.0'})
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read()
        except Exception as exc:
            last = exc
            if attempt == attempts:
                raise
            time.sleep(min(15, 2 ** (attempt - 1)))
    raise last

def brand_domain(text):
    replacements = [
        ('COACH DOLL EDITION', 'THE UNI'),
        ('Coach Doll Edition', 'THE UNI'),
        ('COACH DOLL', 'THE UNI'),
        ('Coach Doll', 'THE UNI'),
        ('https://ikl.barbph.com', 'https://theuni.barbph.com'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r'coach\s+doll(?:\s+edition)?', 'THE UNI', text, flags=re.I)
    return text

sitemap_bytes = get(BASE + 'sitemap.xml')
root = ET.fromstring(sitemap_bytes)
ns = {'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
builds = []
for loc in root.findall('.//s:loc', ns):
    url = (loc.text or '').strip()
    if '/builds/' in url:
        builds.append('builds/' + url.split('/builds/', 1)[1])
builds = sorted(set(builds))
if len(builds) != 177:
    raise RuntimeError(f'Expected 177 live build URLs, found {len(builds)}')

paths = ['index.html','robots.txt','sitemap.xml','coauthor/index.html','coauthor/thanks/index.html']
paths += builds
paths += ['social/' + pathlib.PurePosixPath(p).name.rsplit('.', 1)[0] + '.jpg' for p in builds]
paths += ['social/interactive-knowledge-library.jpg']
if len(paths) != 360 or len(set(paths)) != 360:
    raise RuntimeError(f'Unexpected baseline path count: {len(paths)}')

shutil.rmtree(STAGE, ignore_errors=True)
STAGE.mkdir(parents=True)

def fetch(rel):
    dest = STAGE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = sitemap_bytes if rel == 'sitemap.xml' else get(BASE + rel)
    dest.write_bytes(data)
    return rel

print('Downloading frozen IKL production snapshot...', flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for n, _ in enumerate(pool.map(fetch, paths), 1):
        if n % 40 == 0 or n == len(paths):
            print(f'  {n}/{len(paths)}', flush=True)

# Rebrand all 177 experiences while keeping their content and interaction code intact.
for rel in builds:
    p = STAGE / rel
    text = p.read_text(errors='ignore')
    text = brand_domain(text)
    text = text.replace('../index.html', '/interactive-knowledge-library/')
    text = re.sub(r"""href=(["'])[^"']*\\1(?=[^>]*title=(["'])Back to the Interactive Knowledge Library\\2)""",
                  'href="/interactive-knowledge-library/"', text, flags=re.I)
    # Every experience explicitly declares its parent collection even when its visual UI has no back control.
    if '<head>' in text:
        text = text.replace('<head>', '<head>\n<link rel="up" href="/interactive-knowledge-library/">', 1)
    else:
        text = '<link rel="up" href="/interactive-knowledge-library/">\n' + text
    p.write_text(text)

# Preserve the production library homepage as a collection page under THE UNI.
source_home = (STAGE / 'index.html').read_text(errors='ignore')
library = brand_domain(source_home)
library = library.replace('<head>', '<head>\n<base href="/">', 1)
library = re.sub(r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']+["\']\s*/?>',
                 '<link rel="canonical" href="https://theuni.barbph.com/interactive-knowledge-library/">',
                 library, count=1, flags=re.I)
library = re.sub(r'(<meta\s+property=["\']og:url["\']\s+content=["\'])[^"\']+(["\'])',
                 r'\1https://theuni.barbph.com/interactive-knowledge-library/\2', library, count=1, flags=re.I)
library = re.sub(r'(<div\s+class=["\']brand["\']>).*?(</div>)',
                 '<a class="brand" href="/" aria-label="THE UNI by BarbPH"><img src="/assets/the-uni-wordmark.svg" alt="THE UNI"></a>',
                 library, count=1, flags=re.I|re.S)
library = library.replace('href="coauthor/"', 'href="/coauthor/"').replace("href='coauthor/'", "href='/coauthor/'")
library = library.replace('href="../coauthor/"', 'href="/coauthor/"').replace("href='../coauthor/'", "href='/coauthor/'")
# Absolute collection routes protect all catalog links after moving the homepage one level deeper.
library = re.sub(r'(?P<q>["\'])builds/', lambda m: m.group('q') + '/builds/', library)
library = library.replace('</head>', '''<style id="the-uni-wordmark-override">
.brand{display:inline-flex!important;align-items:center!important;line-height:1!important;white-space:nowrap!important}
.brand img{display:block;width:96px;height:auto;filter:drop-shadow(0 1px 10px rgba(0,0,0,.28))}
@media(max-width:680px){.brand img{width:86px}}
</style>\n</head>''', 1)
libdir = STAGE / 'interactive-knowledge-library'
libdir.mkdir(parents=True, exist_ok=True)
(libdir / 'index.html').write_text(library)

ROOT_INDEX = r'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>THE UNI — Knowledge You Can Enter</title>
<meta name="description" content="THE UNI by BarbPH is a home for interactive knowledge: enter the Interactive Knowledge Library and The Impossible Museum.">
<link rel="canonical" href="https://theuni.barbph.com/"><meta name="theme-color" content="#08070b">
<meta property="og:type" content="website"><meta property="og:site_name" content="THE UNI"><meta property="og:title" content="THE UNI — Knowledge You Can Enter">
<meta property="og:description" content="Enter interactive knowledge through the Interactive Knowledge Library and The Impossible Museum."><meta property="og:url" content="https://theuni.barbph.com/">
<style>
:root{--ink:#f6f1e8;--muted:#b8b0a6;--line:rgba(240,216,171,.17);--gold:#d5b476;--bg:#060509}*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink)}body{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;min-height:100vh;background:radial-gradient(circle at 50% 8%,rgba(111,137,170,.17),transparent 31%),radial-gradient(circle at 18% 28%,rgba(213,180,118,.09),transparent 22%),linear-gradient(180deg,#0d0c11,#060509 58%)}a{color:inherit}.shell{width:min(1180px,calc(100% - 32px));margin:auto;padding:18px 0 54px}.top{display:flex;justify-content:space-between;align-items:center;padding:9px 4px 20px}.brand img{display:block;width:174px;max-width:43vw;height:auto}.parent{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);text-decoration:none}.hero{padding:12vh 0 8vh;max-width:950px}.kicker{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold);margin-bottom:20px}.hero h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(58px,10vw,132px);line-height:.88;letter-spacing:-.055em;margin:0}.hero h1 em{font-weight:400;color:var(--gold)}.hero p{font-family:Georgia,"Times New Roman",serif;font-size:clamp(18px,2vw,29px);line-height:1.5;color:#dfd7ca;max-width:690px;margin:28px 0 0}.doors{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:38px}.door{display:block;min-height:300px;padding:26px;border:1px solid var(--line);border-radius:28px;text-decoration:none;background:linear-gradient(180deg,rgba(24,21,26,.63),rgba(8,8,11,.78));position:relative;overflow:hidden;transition:.25s ease}.door:hover,.door:focus-visible{transform:translateY(-4px);border-color:rgba(213,180,118,.45);outline:none}.door small{font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold)}.door h2{font-family:Georgia,"Times New Roman",serif;font-size:clamp(34px,4vw,60px);font-weight:400;line-height:1.02;letter-spacing:-.035em;margin:88px 0 10px;max-width:500px}.door p{color:var(--muted);line-height:1.65;font-size:13px;max-width:480px}.arrow{position:absolute;right:24px;bottom:22px;font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:#e6dcca}.footer{padding:52px 2px 0;color:#857e78;font-size:10px;letter-spacing:.08em}.footer strong{color:#ddd5ca;font-weight:500}.museum:before,.library:before{content:"";position:absolute;width:260px;height:260px;border-radius:50%;right:-60px;top:-80px;background:radial-gradient(circle at 34% 30%,rgba(255,255,255,.24),rgba(213,180,117,.09) 24%,transparent 67%)}.museum:before{background:radial-gradient(circle at 34% 30%,rgba(255,255,255,.18),rgba(185,155,205,.1) 24%,transparent 67%)}@media(max-width:760px){.shell{width:min(100% - 18px,1180px)}.hero{padding:10vh 7px 7vh}.doors{grid-template-columns:1fr}.door{min-height:245px}.door h2{margin-top:62px}.parent{font-size:8px}.brand img{width:154px}}
</style>
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://theuni.barbph.com/#publisher","name":"BarbPH","url":"https://barbph.com/"},{"@type":"WebSite","@id":"https://theuni.barbph.com/#website","url":"https://theuni.barbph.com/","name":"THE UNI","description":"A home for interactive knowledge by BarbPH.","publisher":{"@id":"https://theuni.barbph.com/#publisher"},"inLanguage":"en"}]}</script>
</head><body><main class="shell">
<header class="top"><a class="brand" href="/" aria-label="THE UNI home"><img src="/assets/the-uni-wordmark.svg" alt="THE UNI"></a><a class="parent" href="https://barbph.com/">by BarbPH</a></header>
<section class="hero"><div class="kicker">THE UNI</div><h1>Knowledge you can <em>enter.</em></h1><p>Two connected spaces for exploring ideas, systems, objects, experiments and reconstructions across human knowledge.</p></section>
<section class="doors" aria-label="Explore THE UNI">
<a class="door library" href="/interactive-knowledge-library/"><small>Explore</small><h2>Interactive Knowledge Library</h2><p>177 connected learning experiences spanning knowledge maps, interactive objects, laboratories and reconstruction.</p><span class="arrow">Enter →</span></a>
<a class="door museum" href="/the-impossible-museum/"><small>Explore</small><h2>The Impossible Museum</h2><p>A crawlable home for exhibits and experiences that bring together things no physical museum could place in one room.</p><span class="arrow">Enter →</span></a>
</section><footer class="footer"><strong>THE UNI</strong> · by BarbPH · © 2026</footer></main></body></html>'''

COAUTHOR = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Be a Co-Author — THE UNI</title><meta name="description" content="Propose a verified addition to THE UNI. Public submissions are reviewed before publication.">
<link rel="canonical" href="https://theuni.barbph.com/coauthor/"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website"><meta property="og:site_name" content="THE UNI"><meta property="og:title" content="Be a Co-Author — THE UNI">
<meta property="og:description" content="Propose a source-backed addition to THE UNI. Nothing is published automatically."><meta property="og:url" content="https://theuni.barbph.com/coauthor/">
<style>:root{--ink:#f6f1e8;--muted:#b8b0a6;--line:rgba(240,216,171,.16);--gold:#d5b476}*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#060509;color:var(--ink)}body{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:radial-gradient(circle at 50% -8%,rgba(111,137,170,.2),transparent 34%),linear-gradient(180deg,#111117,#060509 64%)}a{color:inherit}.shell{width:min(980px,calc(100% - 28px));margin:auto;padding:16px 0 70px}.top{display:flex;justify-content:space-between;align-items:center;padding:10px 0}.top img{width:132px}.phase{font-size:9px;letter-spacing:.17em;text-transform:uppercase;color:var(--gold)}.hero{padding:13vh 0 7vh}.kicker{font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);margin-bottom:16px}h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(52px,8vw,92px);line-height:.94;margin:0 0 24px}.lead{font-family:Georgia,"Times New Roman",serif;font-size:clamp(18px,2vw,27px);line-height:1.5;color:#ded5ca;max-width:760px}.card{border:1px solid var(--line);border-radius:28px;padding:28px;background:rgba(17,14,19,.76)}h2{font-family:Georgia,"Times New Roman",serif;font-size:32px;font-weight:400;margin:0 0 12px}.card p{color:var(--muted);line-height:1.7}.notice{margin:20px 0;padding:16px;border-left:2px solid var(--gold);background:rgba(213,180,118,.06);color:#ddd5ca;line-height:1.65}.button{display:inline-flex;text-decoration:none;border:1px solid rgba(221,190,130,.45);background:rgba(181,140,77,.16);border-radius:999px;padding:13px 18px;text-transform:uppercase;font-size:10px;font-weight:700;letter-spacing:.09em;margin-top:8px}.button:hover,.button:focus-visible{background:rgba(181,140,77,.24);outline:none}.steps{margin-top:26px;color:var(--muted);font-size:13px;line-height:1.8}.back{display:inline-block;margin-top:32px;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.13em;text-decoration:none}@media(max-width:650px){.hero{padding:10vh 4px 6vh}.card{padding:20px}}</style></head>
<body><main class="shell"><header class="top"><a href="/" aria-label="THE UNI home"><img src="/assets/the-uni-wordmark.svg" alt="THE UNI"></a><div class="phase">Co-Authorship</div></header>
<section class="hero"><div class="kicker">A controlled contribution layer</div><h1>Help grow THE UNI.</h1><p class="lead">Propose a subject, node, relationship, learning experience, correction, exhibit, or source. Every proposal is reviewed and verified before anything can enter production.</p></section>
<section class="card"><h2>Public proposal intake</h2><p>THE UNI uses a structured GitHub issue form so every proposal is source-backed, timestamped, reviewable, and kept separate from production content.</p>
<div class="notice">Nothing submitted is published automatically. Proposals pass scope review, source review, factual verification, moderation, interaction design, and production QA before publication.</div>
<a class="button" href="https://github.com/industriesbarbph-rgb/the-uni/issues/new?template=coauthor.yml" target="_blank" rel="noopener">Open Co-Author Submission ↗</a>
<div class="steps">A free GitHub account is required to submit and follow a proposal. Accepted proposals still do not grant direct production access.</div></section>
<a class="back" href="/interactive-knowledge-library/">← Interactive Knowledge Library</a></main></body></html>'''

THANKS = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Co-Author Submission — THE UNI</title><meta name="robots" content="noindex,follow"><style>html,body{margin:0;min-height:100%;background:#07060a;color:#f6f1e8}body{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;display:grid;place-items:center}.card{width:min(680px,calc(100% - 28px));border:1px solid rgba(240,216,171,.17);border-radius:28px;padding:32px;background:#111016}.card img{width:150px}.card h1{font-family:Georgia,serif;font-weight:400;font-size:42px}.card p{color:#b8b0a6;line-height:1.7}.card a{color:#d5b476}</style></head><body><main class="card"><a href="/"><img src="/assets/the-uni-wordmark.svg" alt="THE UNI"></a><h1>Co-author proposals have moved to GitHub.</h1><p>Use the structured public proposal form so your sources, context, and review history stay attached to the submission.</p><p><a href="/coauthor/">Open the Co-Author page →</a></p></main></body></html>'''

MUSEUM = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Impossible Museum — THE UNI</title><meta name="description" content="The Impossible Museum is a crawlable section of THE UNI by BarbPH for exhibits and interactive experiences unconstrained by a physical museum room.">
<link rel="canonical" href="https://theuni.barbph.com/the-impossible-museum/"><meta name="theme-color" content="#08070b">
<meta property="og:type" content="website"><meta property="og:site_name" content="THE UNI"><meta property="og:title" content="The Impossible Museum — THE UNI"><meta property="og:description" content="A museum space for exhibits and interactive experiences that a physical museum could not contain in one room."><meta property="og:url" content="https://theuni.barbph.com/the-impossible-museum/">
<style>:root{--ink:#f6f1e8;--muted:#b8b0a6;--gold:#d5b476;--line:rgba(240,216,171,.17)}*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#050408;color:var(--ink)}body{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;min-height:100vh;background:radial-gradient(circle at 70% 12%,rgba(185,155,205,.17),transparent 31%),radial-gradient(circle at 15% 25%,rgba(213,180,118,.08),transparent 24%),linear-gradient(180deg,#0e0912,#050408 58%)}a{color:inherit}.shell{width:min(1100px,calc(100% - 32px));margin:auto;padding:18px 0 70px}.top{display:flex;justify-content:space-between;align-items:center}.top img{width:174px;max-width:44vw}.back{text-decoration:none;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}.hero{padding:17vh 0 8vh}.kicker{font-size:10px;letter-spacing:.23em;text-transform:uppercase;color:var(--gold);margin-bottom:18px}h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(58px,9vw,118px);font-weight:400;line-height:.88;letter-spacing:-.05em;margin:0;max-width:950px}p{font-family:Georgia,"Times New Roman",serif;font-size:clamp(18px,2vw,27px);line-height:1.55;color:#ded5e0;max-width:760px;margin:28px 0 0}.note{margin-top:44px;border-top:1px solid var(--line);padding-top:20px;color:var(--muted);font-size:12px;line-height:1.7;max-width:720px}.footer{padding-top:56px;color:#857e78;font-size:10px;letter-spacing:.08em}@media(max-width:700px){.shell{width:min(100% - 18px,1100px)}.hero{padding:13vh 7px 7vh}}</style>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"CollectionPage","@id":"https://theuni.barbph.com/the-impossible-museum/#webpage","url":"https://theuni.barbph.com/the-impossible-museum/","name":"The Impossible Museum — THE UNI","isPartOf":{"@id":"https://theuni.barbph.com/#website"},"inLanguage":"en"}</script>
</head><body><main class="shell"><header class="top"><a href="/" aria-label="THE UNI home"><img src="/assets/the-uni-wordmark.svg" alt="THE UNI"></a><a class="back" href="/">THE UNI</a></header><section class="hero"><div class="kicker">THE UNI · Crawlable Collection</div><h1>The Impossible Museum</h1><p>A museum unconstrained by walls, distance, scale or time—built to hold interactive exhibits and experiences that could never occupy one physical room.</p><div class="note">This section is established as a permanent, crawlable part of THE UNI. Exhibits will be added here without mixing them into the 177-experience Interactive Knowledge Library catalog.</div></section><footer class="footer">THE UNI · by BarbPH · © 2026</footer></main></body></html>'''

WORDMARK = r'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 174 40" role="img" aria-labelledby="title desc">
<title id="title">THE UNI</title><desc id="desc">THE UNI wordmark with BarbPH lettering embedded inside the letter I.</desc>
<g fill="#f7f5f0" font-family="Segoe UI Variable Display, Segoe UI, Arial, sans-serif" font-size="25" font-weight="650" letter-spacing="3.1"><text x="1" y="29">THE UN</text></g>
<g transform="translate(151 4)"><rect x="0" y="0" width="20" height="3.2" rx="1.3" fill="#f7f5f0"/><rect x="0" y="29" width="20" height="3.2" rx="1.3" fill="#f7f5f0"/><rect x="6" y="3" width="8" height="26.2" rx="1" fill="rgba(247,245,240,.08)" stroke="#f7f5f0" stroke-width="1"/><g fill="#d8b873" font-family="Arial Narrow, Arial, sans-serif" font-size="4.25" font-weight="700" text-anchor="middle"><text x="10" y="7.4">B</text><text x="10" y="11.6">a</text><text x="10" y="15.8">r</text><text x="10" y="20">b</text><text x="10" y="24.2">P</text><text x="10" y="28.4">H</text></g></g></svg>'''

PREVIEW_B64 = '''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'''

ISSUE = r'''name: THE UNI Co-Author Submission
description: Propose a subject, node, relationship, learning experience, correction, or source for THE UNI.
title: "[Co-Author] "
labels:
  - co-author-submission
body:
  - type: markdown
    attributes:
      value: |
        Thank you for proposing a contribution to **THE UNI**. Submission does not provide editing or publishing access. Every proposal is reviewed before anything can enter the public site.
  - type: dropdown
    id: contribution_type
    attributes:
      label: Contribution type
      options:
        - New subject or field
        - New node for an existing Knowledge Map
        - Relationship between existing nodes
        - New Knowledge Object
        - New Learning Laboratory topic
        - Reconstruction topic
        - The Impossible Museum exhibit
        - Correction to existing content
        - Source or evidence contribution
        - Question identifying missing coverage
        - Other proposed learning experience
    validations: {required: true}
  - type: input
    id: proposed_subject
    attributes: {label: Proposed subject, placeholder: "Example: Embodied Cognition"}
    validations: {required: true}
  - type: textarea
    id: proposal_details
    attributes: {label: What should THE UNI add, change, or represent?, description: Describe the proposed knowledge, structure, correction, exhibit, or learning experience.}
    validations: {required: true}
  - type: textarea
    id: sources_evidence
    attributes: {label: Sources or evidence, description: Add URLs, citations, primary sources, official documentation, or other material that can be checked.}
    validations: {required: true}
  - type: textarea
    id: uncertainty_or_inference
    attributes: {label: What is uncertain, disputed, inferred, or still needs checking?, description: Keep evidence, inference, and disputed claims clearly separated.}
  - type: input
    id: contributor_name
    attributes: {label: Contributor name / preferred credit}
    validations: {required: true}
  - type: checkboxes
    id: acknowledgement
    attributes:
      label: Submission acknowledgement
      options:
        - label: I understand this is a proposal for review and is not published automatically.
          required: true
        - label: I confirm that I identified sources/evidence in good faith and flagged known uncertainty or inference.
          required: true
'''

PAGES = r'''name: Deploy THE UNI to GitHub Pages
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: false
jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Configure Pages
        uses: actions/configure-pages@v5
      - name: Upload static site
        uses: actions/upload-pages-artifact@v3
        with:
          path: .
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
'''

README = r'''# THE UNI

THE UNI is the BarbPH home for interactive knowledge.

## Public structure
- `/` — THE UNI
- `/interactive-knowledge-library/` — Interactive Knowledge Library
- `/the-impossible-museum/` — The Impossible Museum
- `/builds/` — 177 interactive learning experiences
- `/coauthor/` — public co-author proposal entry point

This repository is the production source for `https://theuni.barbph.com/` on GitHub Pages.

The legacy `https://ikl.barbph.com/` remains untouched until THE UNI passes live production QA and old-to-new redirects are ready.

THE UNI is the public project brand. Interactive Knowledge Library and The Impossible Museum remain crawlable collection names. The THE UNI wordmark contains the BarbPH signature inside the letter I.
'''

(STAGE / 'index.html').write_text(ROOT_INDEX)
(STAGE / 'coauthor/index.html').write_text(COAUTHOR)
(STAGE / 'coauthor/thanks/index.html').write_text(THANKS)
museum_dir = STAGE / 'the-impossible-museum'; museum_dir.mkdir(parents=True, exist_ok=True); (museum_dir/'index.html').write_text(MUSEUM)
assets = STAGE / 'assets'; assets.mkdir(parents=True, exist_ok=True)
(assets/'the-uni-wordmark.svg').write_text(WORDMARK)
(assets/'the-uni-wordmark-preview.png').write_bytes(base64.b64decode(PREVIEW_B64))
(STAGE/'.nojekyll').write_text('')
(STAGE/'CNAME').write_text('theuni.barbph.com\n')
(STAGE/'README.md').write_text(README)

issue_dir = STAGE/'.github/ISSUE_TEMPLATE'; issue_dir.mkdir(parents=True, exist_ok=True)
(issue_dir/'coauthor.yml').write_text(ISSUE)
(issue_dir/'config.yml').write_text('blank_issues_enabled: false\n')
workflow_dir = STAGE/'.github/workflows'; workflow_dir.mkdir(parents=True, exist_ok=True)
(workflow_dir/'pages.yml').write_text(PAGES)

# Build a clean sitemap for the THE UNI information architecture.
urls = [
    NEW,
    NEW + 'interactive-knowledge-library/',
    NEW + 'the-impossible-museum/',
    NEW + 'coauthor/',
] + [NEW + rel for rel in builds]
urlset = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
for url in urls:
    node = ET.SubElement(urlset, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')
    ET.SubElement(node, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text = url
    ET.SubElement(node, '{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod').text = '2026-10-03'
ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
ET.ElementTree(urlset).write(STAGE/'sitemap.xml', encoding='utf-8', xml_declaration=True)
(STAGE/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: https://theuni.barbph.com/sitemap.xml\n')

# Integrity and migration gates.
all_files = [p for p in STAGE.rglob('*') if p.is_file()]
html = list(STAGE.rglob('*.html'))
if len(all_files) != 370:
    raise RuntimeError(f'Expected 370 final files, found {len(all_files)}')
if len(html) != 182:
    raise RuntimeError(f'Expected 182 HTML files, found {len(html)}')
if len(list((STAGE/'builds').glob('*.html'))) != 177:
    raise RuntimeError('177-build integrity check failed')
for req in ['index.html','interactive-knowledge-library/index.html','the-impossible-museum/index.html','coauthor/index.html','CNAME','sitemap.xml','robots.txt','.nojekyll','assets/the-uni-wordmark.svg']:
    if not (STAGE/req).exists():
        raise RuntimeError(f'Missing required file: {req}')
joined = '\n'.join(p.read_text(errors='ignore') for p in html)
if re.search(r'coach\s+doll', joined, re.I):
    raise RuntimeError('Public Coach Doll branding remains')
if 'ikl.barbph.com' in joined.lower():
    raise RuntimeError('Old IKL domain remains in HTML')
if (STAGE/'CNAME').read_text().strip() != 'theuni.barbph.com':
    raise RuntimeError('CNAME mismatch')
newmap = ET.parse(STAGE/'sitemap.xml').getroot()
locs = [(x.text or '').strip() for x in newmap.findall('.//s:loc', ns)]
if len(locs) != 181 or len(set(locs)) != 181:
    raise RuntimeError(f'Sitemap integrity failed: {len(locs)} URLs')
for rel in builds:
    text = (STAGE/rel).read_text(errors='ignore')
    if '/interactive-knowledge-library/' not in text:
        raise RuntimeError(f'Library return route missing in {rel}')
if '177 connected learning experiences' not in ROOT_INDEX:
    raise RuntimeError('Root catalog count marker missing')
print('Integrity gates passed: 370 files / 182 HTML / 177 builds / 181 sitemap URLs / zero old public branding.', flush=True)

# Freeze verified bytes before removing bootstrap machinery, then replace the repository tree.
payload = [(p.relative_to(STAGE), p.read_bytes()) for p in all_files]
for child in list(ROOT.iterdir()):
    if child.name == '.git':
        continue
    if child.is_dir():
        shutil.rmtree(child)
    else:
        child.unlink()
for rel, data in payload:
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)

print('THE UNI production source prepared. Bootstrap machinery removed.', flush=True)
