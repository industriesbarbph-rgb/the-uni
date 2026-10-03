#!/usr/bin/env python3
import base64, concurrent.futures, hashlib, lzma, pathlib, re, shutil, subprocess, urllib.request, xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOT = ROOT / '.bootstrap'
STAGE = BOOT / 'stage'
BASE = 'https://ikl.barbph.com/'
EXPECTED_PAYLOAD_CHARS = 256684
EXPECTED_XZ_SHA256 = 'ce399064604dbe0f5c1f990d743b356f1e910ce522a1dd498982291ce8578758'
EXPECTED_PATCH_SHA256 = '0f9a5f33c84fe84a6310bef7ce0abca8b3a069007c5fdb60c156cdbbeb53fc78'

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent':'THE-UNI-Migration/1.0'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()

# Reconstruct the exact frozen 360-file IKL production baseline.
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
    raise RuntimeError(f'Unexpected baseline path count: {len(paths)} / unique {len(set(paths))}')

shutil.rmtree(STAGE, ignore_errors=True)
STAGE.mkdir(parents=True)

def fetch(rel):
    dest = STAGE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = sitemap_bytes if rel == 'sitemap.xml' else get(BASE + rel)
    dest.write_bytes(data)
    return rel

print('Downloading frozen IKL production snapshot...')
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
    for n, _ in enumerate(pool.map(fetch, paths), 1):
        if n % 40 == 0 or n == len(paths):
            print(f'  {n}/{len(paths)}')

# Reassemble and cryptographically verify the audited migration patch.
parts = sorted(BOOT.glob('patch.part*'))
encoded = ''.join(p.read_text().strip() for p in parts)
if len(encoded) != EXPECTED_PAYLOAD_CHARS:
    raise RuntimeError(f'Migration payload length mismatch: {len(encoded)} != {EXPECTED_PAYLOAD_CHARS}')

compressed = base64.b64decode(encoded)
compressed_sha = hashlib.sha256(compressed).hexdigest()
if compressed_sha != EXPECTED_XZ_SHA256:
    raise RuntimeError(f'Migration payload SHA-256 mismatch: {compressed_sha}')

patch = lzma.decompress(compressed)
patch_sha = hashlib.sha256(patch).hexdigest()
if patch_sha != EXPECTED_PATCH_SHA256:
    raise RuntimeError(f'Migration patch SHA-256 mismatch: {patch_sha}')

patch_path = BOOT / 'migration.patch'
patch_path.write_bytes(patch)
subprocess.run(['git','apply','--check',str(patch_path)], cwd=STAGE, check=True)
subprocess.run(['git','apply',str(patch_path)], cwd=STAGE, check=True)

# Post-migration integrity gates.
all_files = [p for p in STAGE.rglob('*') if p.is_file()]
html = list(STAGE.rglob('*.html'))
if len(all_files) != 370:
    raise RuntimeError(f'Expected 370 final files, found {len(all_files)}')
if len(list((STAGE/'builds').glob('*.html'))) != 177:
    raise RuntimeError('177-build integrity check failed')

for req in ['index.html','interactive-knowledge-library/index.html','the-impossible-museum/index.html','CNAME','sitemap.xml','robots.txt','.nojekyll']:
    if not (STAGE/req).exists():
        raise RuntimeError(f'Missing required file: {req}')

if (STAGE/'CNAME').read_text().strip() != 'theuni.barbph.com':
    raise RuntimeError('CNAME mismatch')

joined = '\n'.join(p.read_text(errors='ignore') for p in html)
if re.search(r'coach\s*doll', joined, re.I):
    raise RuntimeError('Old Coach Doll branding remains')
if 'ikl.barbph.com' in joined.lower():
    raise RuntimeError('Old IKL domain remains in HTML')

newmap = ET.parse(STAGE/'sitemap.xml').getroot()
locs = [(x.text or '').strip() for x in newmap.findall('.//s:loc', ns)]
if len(locs) != 181 or len(set(locs)) != 181:
    raise RuntimeError(f'Sitemap integrity failed: {len(locs)} URLs')

print('Integrity gates passed: 370 files / 177 builds / 181 sitemap URLs / zero old branding.')

# Copy the exact verified target tree into the repository.
for p in all_files:
    rel = p.relative_to(STAGE)
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst)

try:
    (ROOT/'BOOTSTRAP.md').unlink()
except FileNotFoundError:
    pass

# Remove temporary bootstrap machinery so main contains only maintainable production source.
bootstrap_workflow = ROOT/'.github/workflows/bootstrap-the-uni.yml'
if bootstrap_workflow.exists():
    bootstrap_workflow.unlink()
shutil.rmtree(BOOT, ignore_errors=True)

print('THE UNI source tree prepared and bootstrap payload cleaned.')
