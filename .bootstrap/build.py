#!/usr/bin/env python3
import base64, concurrent.futures, gzip, os, pathlib, re, shutil, subprocess, urllib.request, xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOT = ROOT / '.bootstrap'
STAGE = BOOT / 'stage'
BASE = 'https://ikl.barbph.com/'

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'THE-UNI-Migration/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r: return r.read()

# Build the exact 360-file public production snapshot from the live frozen IKL site.
sitemap_bytes=get(BASE+'sitemap.xml')
root=ET.fromstring(sitemap_bytes)
ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
builds=[]
for loc in root.findall('.//s:loc',ns):
    u=(loc.text or '').strip()
    if '/builds/' in u:
        builds.append('builds/'+u.split('/builds/',1)[1])
builds=sorted(set(builds))
if len(builds)!=177:
    raise RuntimeError(f'Expected 177 live build URLs, found {len(builds)}')
paths=['index.html','robots.txt','sitemap.xml','coauthor/index.html','coauthor/thanks/index.html']
paths += builds
paths += ['social/'+pathlib.PurePosixPath(p).name.rsplit('.',1)[0]+'.jpg' for p in builds]
paths += ['social/interactive-knowledge-library.jpg']
if len(paths)!=360 or len(set(paths))!=360:
    raise RuntimeError(f'Unexpected baseline path count: {len(paths)} / unique {len(set(paths))}')
shutil.rmtree(STAGE,ignore_errors=True); STAGE.mkdir(parents=True)

def fetch(rel):
    dest=STAGE/rel; dest.parent.mkdir(parents=True,exist_ok=True)
    data=sitemap_bytes if rel=='sitemap.xml' else get(BASE+rel)
    dest.write_bytes(data); return rel
print('Downloading frozen IKL production snapshot...')
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
    for n,_ in enumerate(ex.map(fetch,paths),1):
        if n%40==0 or n==len(paths): print(f'  {n}/{len(paths)}')
# Apply the locally audited migration patch that converts the snapshot into the exact staged THE UNI tree.
encoded=''.join(p.read_text().strip() for p in sorted(BOOT.glob('patch.part*')))
patch=gzip.decompress(base64.b64decode(encoded))
patch_path=BOOT/'migration.patch'; patch_path.write_bytes(patch)
subprocess.run(['git','apply','--check',str(patch_path)],cwd=STAGE,check=True)
subprocess.run(['git','apply',str(patch_path)],cwd=STAGE,check=True)
# Post-migration integrity gates.
all_files=[p for p in STAGE.rglob('*') if p.is_file()]
html=list(STAGE.rglob('*.html'))
if len(all_files)!=370: raise RuntimeError(f'Expected 370 final files, found {len(all_files)}')
if len(list((STAGE/'builds').glob('*.html')))!=177: raise RuntimeError('177-build integrity check failed')
for req in ['index.html','interactive-knowledge-library/index.html','the-impossible-museum/index.html','CNAME','sitemap.xml','robots.txt','.nojekyll']:
    if not (STAGE/req).exists(): raise RuntimeError(f'Missing required file: {req}')
if (STAGE/'CNAME').read_text().strip()!='theuni.barbph.com': raise RuntimeError('CNAME mismatch')
joined='\n'.join(p.read_text(errors='ignore') for p in html)
if re.search(r'coach\s*doll',joined,re.I): raise RuntimeError('Old Coach Doll branding remains')
if 'ikl.barbph.com' in joined.lower(): raise RuntimeError('Old IKL domain remains in HTML')
newmap=ET.parse(STAGE/'sitemap.xml').getroot(); locs=[(x.text or '').strip() for x in newmap.findall('.//s:loc',ns)]
if len(locs)!=181 or len(set(locs))!=181: raise RuntimeError(f'Sitemap integrity failed: {len(locs)} URLs')
print('Integrity gates passed: 370 files / 177 builds / 181 sitemap URLs / zero old branding.')
# Copy exact target tree into the repository. Bootstrap files are removed in a later cleanup commit.
for p in all_files:
    rel=p.relative_to(STAGE); dst=ROOT/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dst)
try: (ROOT/'BOOTSTRAP.md').unlink()
except FileNotFoundError: pass
print('THE UNI source tree prepared.')
