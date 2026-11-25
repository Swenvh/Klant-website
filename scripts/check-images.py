import re, sys, json
from pathlib import Path
from PIL import Image
dist=Path(sys.argv[1]); problems=[]; count=0; sizes={}
def exists(ref):
    p=dist/ref.split('?')[0].lstrip('/'); return p.is_file(), p
def dims(p):
    if p not in sizes:
        with Image.open(p) as im: sizes[p]=im.size
    return sizes[p]
for html in sorted(dist.rglob('index.html')):
    if 'client' in html.parts: continue
    s=html.read_text(); page='/'+str(html.parent.relative_to(dist)).strip('.')
    for tag in re.findall(r'<img\b[^>]*>',s):
        count+=1
        attrs=dict(re.findall(r'([a-z-]+)="([^"]*)"',tag))
        src=attrs.get('src','')
        if not src: problems.append((page,'img zonder src',tag[:80])); continue
        if src.startswith('data:'): continue
        ok,p=exists(src)
        if not ok: problems.append((page,'src ontbreekt',src)); continue
        if 'alt' not in attrs: problems.append((page,'geen alt',src))
        w,h=dims(p)
        if 'width' in attrs and 'height' in attrs:
            r1=int(attrs['width'])/int(attrs['height']); r2=w/h
            if abs(r1-r2)/r2>0.02: problems.append((page,f'verhouding klopt niet (attr {attrs["width"]}x{attrs["height"]}, bestand {w}x{h})',src))
        else: problems.append((page,'geen width/height',src))
        if attrs.get('fetchpriority')!='high' and attrs.get('loading') not in ('lazy','eager'): problems.append((page,'geen loading=lazy of eager',src))
        for part in attrs.get('srcset','').split(','):
            part=part.strip()
            if not part: continue
            url,wd=part.split()
            ok,p2=exists(url)
            if not ok: problems.append((page,'srcset-variant ontbreekt',url)); continue
            vw=dims(p2)[0]
            if str(vw)+'w'!=wd: problems.append((page,f'srcset-breedte {wd} klopt niet met bestand {vw}px',url))
        if 'srcset' in attrs and 'sizes' not in attrs: problems.append((page,'srcset zonder sizes',src))
    for ref in re.findall(r'<link[^>]+(?:rel="preload"[^>]+as="image"|rel="icon")[^>]+href="([^"]+)"',s):
        if ref.startswith('data:'): continue
        if not exists(ref)[0]: problems.append((page,'preload/icon ontbreekt',ref))
    for ref in re.findall(r'<meta property="og:image" content="[^"]*?(/assets/[^"]+)"',s):
        if not exists(ref)[0]: problems.append((page,'og:image ontbreekt',ref))
    for ref in re.findall(r'<image[^>]+href="([^"]+)"',s):
        if not exists(ref)[0]: problems.append((page,'svg-image ontbreekt',ref))
css=(dist/'style.css').read_text()
for ref in set(re.findall(r"url\('?(/assets/[^')]+)'?\)",css)):
    if not exists(ref)[0]: problems.append(('style.css','css-afbeelding ontbreekt',ref))
js=(dist/'app.js').read_text()
for ref in set(re.findall(r"['\"](/assets/[^'\"]+)['\"]",js)):
    if not exists(ref)[0]: problems.append(('app.js','js-afbeelding ontbreekt',ref))
print(f'{count} img-tags gecontroleerd, {len(problems)} problemen')
for p in problems: print(' -',*p)
sys.exit(1 if problems else 0)
