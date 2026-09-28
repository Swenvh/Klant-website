# Bundelt dist/ tot één zelfstandig HTML-bestand (preview/van-ommen-preview.html) met alle
# pagina's en klikbare navigatie, om de site zonder server te bekijken. Formulieren naar
# /api (afspraken, statistiek) werken in de preview niet.
import re, json, base64, mimetypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'dist'
routes={}
for f in sorted(D.rglob('index.html')):
    if '.openai' in f.parts: continue
    r='/'+str(f.parent.relative_to(D)).strip('.')+'/' if f.parent!=D else '/'
    routes[r.replace('//','/')]=f.read_text()
imap=json.loads((D/'assets/responsive-images.json').read_text())
assets={}
def tok(path):
    path=path.split('?')[0]
    assets[path]=None
    return f'%%A:{path}%%'
def pick(src):
    # kies een middelgrote variant (≈960px) voor een compact bestand
    for k,info in imap.items():
        vs=info['variants']
        if src==k or any(v['src']==src for v in vs):
            best=min(vs,key=lambda v:abs(v['width']-1000))
            return best['src']
    return src
css=(D/'style.css').read_text()
css=re.sub(r"url\('(/assets/[^']+)'\)",lambda m:"url('"+tok(pick(m.group(1)) if m.group(1).endswith(('.webp','.jpg','.jpeg','.png')) else m.group(1))+"')",css)
app=(D/'app.js').read_text()
app=re.sub(r"(['\"`])(/assets/[^'\"`]+)",lambda m:m.group(1)+tok(pick(m.group(2))),app)
pages={}
for r,h in routes.items():
    h=re.sub(r'<link rel="stylesheet" href="/style.css">','<style>%%CSS%%</style>',h)
    h=re.sub(r'<link rel="preload"[^>]*>','',h)
    h=re.sub(r'<script src="/app.js" defer></script>','',h)
    h=re.sub(r'\s(srcset|sizes)="[^"]*"','',h)
    h=re.sub(r'(["\'(])(/assets/[^"\')\s]+\.(?:webp|jpe?g|png|ttf))',lambda m:m.group(1)+tok(pick(m.group(2))),h)
    h=re.sub(r'\sloading="lazy"','',h)
    h=h.replace('</body>','<script>%%APP%%</script><script>%%NAV%%</script></body>')
    pages[r]=h
for p in list(assets):
    f=D/p.lstrip('/')
    mt=mimetypes.guess_type(f.name)[0] or ('font/ttf' if f.suffix=='.ttf' else 'application/octet-stream')
    if f.suffix=='.webp': mt='image/webp'
    assets[p]=f'data:{mt};base64,'+base64.b64encode(f.read_bytes()).decode()
nav=r"""(()=>{document.addEventListener('click',e=>{const a=e.target.closest('a[href]');if(!a||e.defaultPrevented)return;const href=a.getAttribute('href');if(!href.startsWith('/')||href.startsWith('//'))return;const u=new URL(href,'https://x');let p=u.pathname;if(!p.endsWith('/'))p+='/';if(!VOS.pages[p])return;e.preventDefault();VOS.go(p,u.hash)});})();"""
boot="""<!doctype html><meta charset="utf-8"><title>Van Ommen Schilderwerken, preview</title><script>
const VOS={pages:%s,assets:%s,css:%s,app:%s,nav:%s};
navigator.sendBeacon=()=>true;
VOS.fill=s=>s.replace(/%%%%A:([^%%]+)%%%%/g,(m,p)=>VOS.assets[p]||p);
VOS.go=(route,hash)=>{let h=VOS.pages[route];const css=VOS.fill(VOS.css);h=h.replace('%%%%CSS%%%%',()=>css).replace('%%%%APP%%%%',()=>'(()=>{'+VOS.app+'\\n})();').replace('%%%%NAV%%%%',()=>VOS.nav);h=VOS.fill(h);document.open();document.write(h);document.close();if(hash){setTimeout(()=>{const t=document.getElementById(hash.slice(1));if(t)t.scrollIntoView()},50)}else scrollTo(0,0);};
VOS.go('/','');
</script>""" % tuple(json.dumps(x).replace('</','<\\/') for x in (pages,assets,css,app,nav))
out=ROOT/'preview/van-ommen-preview.html'
out.parent.mkdir(exist_ok=True)
out.write_text(boot)
print(len(pages),'pagina\'s',len(assets),'bestanden',round(out.stat().st_size/1e6,1),'MB')
