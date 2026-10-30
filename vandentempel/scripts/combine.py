# Combine all preview pages into one self-contained HTML with a hash router.
import sys, re, base64, io, html as H
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import json
import shop_parts as shop
prev, out = Path(sys.argv[1]), Path(sys.argv[2])
cache = {}
ids = {}
def img_ref(p):
    """Register an image once; pages refer to it by id (dedupes repeats)."""
    uri = img_uri(p)
    if not uri: return ""
    if uri not in ids: ids[uri] = f"i{len(ids)}"
    return ids[uri]
def img_uri(p):
    p = p.resolve()
    if p in cache: return cache[p]
    if not p.exists(): return ""
    if p.suffix == ".svg":
        uri = "data:image/svg+xml;base64," + base64.b64encode(p.read_bytes()).decode()
    else:
        im = Image.open(p); im.thumbnail((800, 800))
        buf = io.BytesIO()
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); im = bg
        im.convert("RGB").save(buf, "JPEG", quality=66, optimize=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    cache[p] = uri; return uri
def font_uri(p):
    return "data:font/woff2;base64," + base64.b64encode(p.read_bytes()).decode()

pages = sorted(prev.rglob("index.html"))
def route(f):
    rel = f.parent.relative_to(prev).as_posix()
    return "/" if rel == "." else "/" + rel + "/"
def fix(fragment, f):
    base = f.parent
    def href(m):
        h = m.group(1)
        if h.startswith(("http", "mailto:", "tel:", "#")): return m.group(0)
        target = (base / h).resolve()
        try: r = target.parent.relative_to(prev.resolve()).as_posix() if target.name == "index.html" else None
        except ValueError: r = None
        if r is None: return 'href="#/"'
        return f'href="#{"/" if r == "." else "/" + r + "/"}"'
    fragment = re.sub(r'href="([^"]*)"', href, fragment)
    fragment = re.sub(r'src="((?:\.\./)*(?:media|theme)/[^"]+)"', lambda m: f'data-img="{img_ref(base / m.group(1))}" src="data:image/gif;base64,R0lGODlhAQABAAAAACw="', fragment)
    return fragment

home = prev / "index.html"
src = home.read_text()
header = shop.patch_header(fix(re.search(r'(?s)(<div class="vdt-site-header">.*?</header></div>)', src).group(1), home))
footer = fix(re.search(r'(?s)(<!-- wp:group \{"tagName":"footer".*)</body>', src).group(1), home)
sections = []
titles = {}
products = []
for f in pages:
    t = f.read_text()
    m = re.search(r'(?s)<main id="inhoud" class="vdt-main">(.*)</main>', t)
    if not m: continue
    r = route(f)
    titles[r] = H.unescape(re.search(r"<title>(.*?)</title>", t).group(1))
    frag = fix(m.group(1), f)
    info = shop.product_info(r, frag)
    if info:
        products.append(info)
        frag = shop.add_button(frag, r)
    sections.append(f'<section class="vdt-page" data-route="{H.escape(r)}" hidden>{frag}</section>')
# Joomla lists some products in several categories: show each once in the shop.
uniq = {}
for pr in products:
    key = (pr["t"].lower(), pr["i"])
    uniq.setdefault(key, pr)
products = list(uniq.values())
sections.append(shop.shop_sections(len(products)))
titles["/shop/"] = "Shop: alle meetapparatuur | Vandentempel"
titles["/offerte/"] = "Uw offertelijst | Vandentempel"

css = (prev / "preview-base.css").read_text() + "\n" + (prev / "theme/assets/css/theme.css").read_text()
css = re.sub(r'url\("theme/assets/fonts/([^"]+)"\)', lambda m: f'url("{font_uri(prev / "theme/assets/fonts" / m.group(1))}")', css)
css = re.sub(r'url\("\.\./images/([^"]+)"\)', lambda m: f'url("{img_uri(prev / "theme/assets/images" / m.group(1))}")', css)
import json
doc = f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vandentempel, zekerheid in spanning</title>
<meta name="description" content="Ontwerppreview van de nieuwe Vandentempel-website (alle pagina's in één bestand).">
<style>{css}
.vdt-page[hidden]{{display:none}}{shop.CSS}</style>
</head><body>
<a class="vdt-skip" href="#inhoud">Naar de inhoud</a>
{header}
<main id="inhoud" class="vdt-main">{''.join(sections)}
<section class="vdt-page" data-route="404" hidden><div class="vdt-page-head has-brand-background-color has-white-color"><div class="vdt-wrap"><h1>Niet in deze preview</h1></div></div><div class="vdt-content vdt-page-body"><p>Deze pagina zit niet in de preview. <a href="#/">Terug naar de homepage</a>.</p></div></section></main>
{footer}
<script>
const IMG = {json.dumps({v: k for k, v in ids.items()})};
const titles = {json.dumps(titles, ensure_ascii=False)};
const PRODUCTS = {json.dumps(products, ensure_ascii=False)};
{shop.JS}
function show() {{
  let r = decodeURIComponent(location.hash.slice(1)) || "/";
  if (!r.endsWith("/")) r += "/";
  let found = false;
  document.querySelectorAll(".vdt-page").forEach(s => {{ const on = s.dataset.route === r; s.hidden = !on; found = found || on; }});
  if (!found) document.querySelector('.vdt-page[data-route="404"]').hidden = false;
  document.querySelectorAll('.vdt-site-header img[data-img], .vdt-page:not([hidden]) img[data-img], footer img[data-img]').forEach(i => {{ if (IMG[i.dataset.img]) {{ i.src = IMG[i.dataset.img]; i.removeAttribute("data-img"); }} }});
  document.title = titles[r] || "Vandentempel";
  if (r === "/shop/") {{ buildFilters(); renderShop(); }}
  if (r === "/offerte/") renderCart();
  updateBadge();
  const t = document.getElementById("vdt-menu"); if (t) t.checked = false;
  window.scrollTo(0, 0);
}}
document.addEventListener("click", e => {{ const a = e.target.closest('a[href="#inhoud"]'); if (a) {{ e.preventDefault(); document.getElementById("inhoud").focus(); }} }});
window.addEventListener("hashchange", show); show();
</script>
</body></html>"""
out.write_text(doc)
print("pages", len(sections), "images", len(cache), round(out.stat().st_size / 1e6, 1), "MB")
