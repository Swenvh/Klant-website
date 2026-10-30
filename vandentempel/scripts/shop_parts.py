# Shop ("offertelijst") additions for the single-file preview.
import re, html as H

CART_ICON = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6l1 3H8z"/><rect x="4" y="6" width="16" height="15" rx="2"/><path d="M8 11h8M8 15h5"/></svg>'


def product_info(route, fragment):
    """Pull title, category path, lead image and intro out of a product page."""
    if "vdt-product-top" not in fragment or not route.startswith("/producten/"):
        return None
    title = H.unescape(re.sub(r"<[^>]+>", "", re.search(r"(?s)<h1>(.*?)</h1>", fragment).group(1))).strip()
    crumbs = [H.unescape(x) for x in re.findall(r'(?s)<p class="vdt-breadcrumbs">(.*?)</p>', fragment)[:1] for x in re.findall(r">([^<]+)</a>", x)] if False else []
    m = re.search(r'(?s)<p class="vdt-breadcrumbs">(.*?)</p>', fragment)
    if m:
        crumbs = [H.unescape(x).strip() for x in re.findall(r">([^<]+)</a>", m.group(1))]
    img = re.search(r'(?s)vdt-product-image.*?data-img="([^"]+)"', fragment)
    intro = re.search(r'(?s)vdt-product-top.*?<p class="has-large-font-size">(.*?)</p>', fragment)
    return {
        "r": route,
        "t": title,
        "c": crumbs[1] if len(crumbs) > 1 else "",
        "s": crumbs[2] if len(crumbs) > 2 else "",
        "i": img.group(1) if img else "",
        "d": H.unescape(re.sub(r"<[^>]+>|\s+", " ", intro.group(1))).strip()[:160] if intro else "",
    }


def add_button(fragment, route):
    """Put an 'add to quote list' button first in the product's button row."""
    btn = (f'<div class="wp-block-button"><button type="button" class="wp-block-button__link vdt-add" data-add="{H.escape(route)}">'
           f'Zet op offertelijst</button></div>')
    fragment = fragment.replace('<div class="wp-block-buttons">', '<div class="wp-block-buttons">' + btn, 1)
    # The old "request a quote" button now leads to the list.
    return fragment.replace('href="#/contact/">Offerte of advies aanvragen', 'href="#/offerte/" class="is-secondary">Bekijk offertelijst', 1)


def patch_header(header):
    header = header.replace('<li class="vdt-nav-cta">', '<li><a href="#/shop/" class="vdt-nav-shop">Shop</a></li><li class="vdt-nav-cta">', 1)
    cart = f'<a class="vdt-cart" href="#/offerte/" aria-label="Offertelijst">{CART_ICON}<span class="vdt-cart-count" aria-live="polite">0</span></a>'
    return header.replace('<input type="checkbox" id="vdt-menu"', cart + '<input type="checkbox" id="vdt-menu"', 1)


def shop_sections(n_products):
    shop = f"""<section class="vdt-page" data-route="/shop/" hidden>
<div class="vdt-page-head has-brand-background-color has-white-color"><div class="vdt-wrap"><div class="vdt-page-head-inner">
<p class="vdt-eyebrow">Shop</p><h1>Alle meetapparatuur</h1>
<p class="vdt-lead has-large-font-size">Zoek in {n_products} producten, zet ze op uw offertelijst en vraag in één keer een offerte aan. U ontvangt een prijs op maat met advies van een specialist.</p></div></div></div>
<div class="vdt-wrap vdt-shop">
<aside class="vdt-shop-filters" aria-label="Filters">
<label class="vdt-field"><span>Zoeken</span><input type="search" id="vdt-q" placeholder="Bijv. isolatietester, Fluke, DC" autocomplete="off"></label>
<fieldset class="vdt-field"><legend>Productgroep</legend><div id="vdt-cats" class="vdt-chips"></div></fieldset>
<label class="vdt-field" id="vdt-sub-wrap" hidden><span>Subcategorie</span><select id="vdt-sub"><option value="">Alle subcategorieën</option></select></label>
<button type="button" class="vdt-reset" id="vdt-reset">Filters wissen</button>
<div class="vdt-shop-help"><strong>Hoe werkt het?</strong><ol><li>Zet producten op uw offertelijst</li><li>Vul uw gegevens in</li><li>U ontvangt binnen één werkdag een offerte</li></ol><p class="has-small-font-size">Liever eerst overleggen? Bel <a href="tel:+31384449009">+31 (0)38 444 90 09</a>.</p></div>
</aside>
<div class="vdt-shop-main">
<div class="vdt-shop-bar"><p id="vdt-count" aria-live="polite"></p><label class="vdt-sort"><span>Sorteren</span><select id="vdt-sort"><option value="az">Naam A-Z</option><option value="za">Naam Z-A</option><option value="cat">Productgroep</option></select></label></div>
<div id="vdt-grid" class="vdt-shop-grid"></div>
<div id="vdt-empty" class="vdt-shop-empty" hidden><p><strong>Geen producten gevonden.</strong> Probeer een andere zoekterm of wis de filters. Staat uw product er niet bij? <a href="#/contact/">Vraag het ons</a>, we leveren meer dan op de site staat.</p></div>
</div></div></section>"""
    offerte = """<section class="vdt-page" data-route="/offerte/" hidden>
<div class="vdt-page-head has-brand-background-color has-white-color"><div class="vdt-wrap"><div class="vdt-page-head-inner">
<p class="vdt-eyebrow">Offerte aanvragen</p><h1>Uw offertelijst</h1>
<p class="vdt-lead has-large-font-size">Controleer de producten en aantallen, vul uw gegevens in en verstuur de aanvraag. Geen verplichtingen.</p></div></div></div>
<div class="vdt-wrap vdt-quote">
<div class="vdt-quote-list"><h2>Producten</h2><div id="vdt-cart-items"></div>
<div id="vdt-cart-empty" class="vdt-shop-empty" hidden><p>Uw offertelijst is nog leeg. <a href="#/shop/">Ga naar de shop</a> om producten toe te voegen.</p></div></div>
<form class="vdt-quote-form is-style-vdt-card" id="vdt-quote-form" novalidate>
<h2>Uw gegevens</h2>
<label class="vdt-field"><span>Naam *</span><input name="naam" required autocomplete="name"></label>
<label class="vdt-field"><span>Bedrijf *</span><input name="bedrijf" required autocomplete="organization"></label>
<label class="vdt-field"><span>E-mail *</span><input name="email" type="email" required autocomplete="email"></label>
<label class="vdt-field"><span>Telefoon</span><input name="telefoon" type="tel" autocomplete="tel"></label>
<fieldset class="vdt-field"><legend>Ik ben geïnteresseerd in</legend><div class="vdt-checks">
<label><input type="checkbox" name="interesse" value="Aanschaf" checked> Aanschaf</label>
<label><input type="checkbox" name="interesse" value="Huur"> Huur</label>
<label><input type="checkbox" name="interesse" value="Demonstratie"> Demonstratie</label>
<label><input type="checkbox" name="interesse" value="Training"> Training</label></div></fieldset>
<label class="vdt-field"><span>Opmerking of toepassing</span><textarea name="opmerking" rows="4" placeholder="Bijv. gewenste levertijd, toepassing of spanningsniveau"></textarea></label>
<p id="vdt-form-error" class="vdt-form-error" role="alert" hidden></p>
<div class="wp-block-buttons"><div class="wp-block-button"><button type="submit" class="wp-block-button__link">Offerte aanvragen</button></div></div>
<p class="has-small-font-size vdt-muted">De aanvraag opent als e-mail aan info@vandentempel.nl. In de definitieve WordPress-site wordt dit een formulier.</p>
</form></div></section>"""
    return shop + offerte


CSS = """
/* ---- Shop / offertelijst (preview) ---- */
[hidden] { display: none !important; }
.vdt-page-head-inner > .vdt-eyebrow:first-child { padding-top: clamp(1.5rem, 4vw, 2.75rem); }
.vdt-page-head-inner > .vdt-lead:last-child { padding-bottom: clamp(1rem, 3vw, 2rem); }

.vdt-header .vdt-row { position: relative; }
.vdt-cart { order: 3; position: relative; display: grid; place-items: center; width: 44px; height: 44px; border-radius: 8px; color: var(--wp--preset--color--ink); border: 1px solid var(--wp--preset--color--line); margin-left: auto; flex-shrink: 0; }
.vdt-cart:hover { color: var(--wp--preset--color--brand); border-color: var(--wp--preset--color--brand); }
.vdt-cart-count { position: absolute; top: -7px; right: -7px; min-width: 20px; height: 20px; padding: 0 5px; border-radius: 10px; background: var(--wp--preset--color--brand); color: #fff; font-size: 12px; font-weight: 700; display: grid; place-items: center; line-height: 1; }
.vdt-cart-count.is-zero { background: var(--wp--preset--color--slate); }
.vdt-cart.bump { animation: vdt-bump .4s ease; }
@keyframes vdt-bump { 40% { transform: scale(1.15); } }
.vdt-header .vdt-preview-nav { order: 2; margin-left: auto; }
.vdt-header .vdt-cart { margin-left: 1rem; }
.vdt-burger { order: 4; }
.vdt-nav-shop { color: var(--wp--preset--color--brand) !important; }
@media (max-width: 960px) { .vdt-header .vdt-cart { margin-left: auto; margin-right: .5rem; } }

.vdt-shop { display: grid; grid-template-columns: 280px 1fr; gap: clamp(1.5rem, 3vw, 2.5rem); padding-block: var(--wp--preset--spacing--50) var(--wp--preset--spacing--60); align-items: start; }
@media (max-width: 900px) { .vdt-shop { grid-template-columns: 1fr; } }
.vdt-shop-filters { position: sticky; top: 140px; display: grid; gap: 1.25rem; }
@media (max-width: 900px) { .vdt-shop-filters { position: static; } .vdt-shop-help { display: none; } }
.vdt-field { display: grid; gap: .4rem; border: 0; padding: 0; margin: 0; min-width: 0; }
.vdt-field > span, .vdt-field > legend { font-weight: 700; font-size: var(--wp--preset--font-size--small); padding: 0; margin-bottom: .4rem; }
.vdt-field input:not([type=checkbox]), .vdt-field select, .vdt-field textarea, .vdt-sort select {
	font: inherit; padding: .7rem .85rem; border: 1px solid #C9CAD4; border-radius: 6px; background: #fff; color: var(--wp--preset--color--ink); width: 100%;
}
.vdt-field input:focus, .vdt-field select:focus, .vdt-field textarea:focus, .vdt-sort select:focus { outline: 2px solid var(--wp--preset--color--brand); outline-offset: 1px; border-color: var(--wp--preset--color--brand); }
.vdt-chips { display: flex; flex-wrap: wrap; gap: .4rem; }
.vdt-chip { font: inherit; font-size: var(--wp--preset--font-size--small); padding: .45rem .75rem; border-radius: 999px; border: 1px solid var(--wp--preset--color--line); background: #fff; cursor: pointer; color: var(--wp--preset--color--ink); text-align: left; }
.vdt-chip:hover { border-color: var(--wp--preset--color--brand); }
.vdt-chip[aria-pressed=true] { background: var(--wp--preset--color--brand); border-color: var(--wp--preset--color--brand); color: #fff; }
.vdt-chip small { opacity: .75; margin-left: .25rem; }
.vdt-reset { justify-self: start; font: inherit; font-size: var(--wp--preset--font-size--small); background: none; border: 0; padding: 0; color: var(--wp--preset--color--brand); text-decoration: underline; cursor: pointer; }
.vdt-shop-help { background: var(--wp--preset--color--mist); border-radius: 12px; padding: 1.1rem 1.25rem; font-size: var(--wp--preset--font-size--small); }
.vdt-shop-help ol { margin: .5rem 0; padding-left: 1.2rem; }
.vdt-shop-help p { margin: 0; }
.vdt-shop-bar { display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
.vdt-shop-bar p { margin: 0; color: var(--wp--preset--color--muted); }
.vdt-sort { display: flex; align-items: center; gap: .5rem; font-size: var(--wp--preset--font-size--small); font-weight: 700; }
.vdt-sort select { width: auto; padding: .45rem .7rem; }
.vdt-shop-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }
.vdt-shop-card { display: flex; flex-direction: column; background: #fff; border: 1px solid var(--wp--preset--color--line); border-radius: 12px; overflow: hidden; transition: box-shadow .25s, transform .25s; }
.vdt-shop-card:hover { box-shadow: 0 2px 4px rgba(31,32,33,.08), 0 16px 40px rgba(0,80,138,.14); transform: translateY(-2px); }
.vdt-shop-card > a { display: flex; flex-direction: column; flex: 1; color: var(--wp--preset--color--ink); text-decoration: none; }
.vdt-shop-card figure { margin: 0; aspect-ratio: 4 / 3; background: var(--wp--preset--color--mist); padding: .75rem; overflow: hidden; }
.vdt-shop-card figure img { width: 100%; height: 100%; object-fit: contain; mix-blend-mode: multiply; display: block; }
.vdt-shop-card .vdt-sc-body { flex: 1; }
.vdt-shop-card .vdt-sc-body { padding: .9rem 1rem .5rem; display: grid; gap: .3rem; }
.vdt-sc-cat { font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--wp--preset--color--muted); font-weight: 700; }
.vdt-sc-title { font-weight: 700; line-height: 1.3; }
.vdt-shop-card > a:hover .vdt-sc-title { color: var(--wp--preset--color--brand); }
.vdt-sc-price { font-size: var(--wp--preset--font-size--small); color: var(--wp--preset--color--muted); }
.vdt-shop-card .vdt-add { margin: .5rem 1rem 1rem; }
.vdt-add { font: inherit; font-weight: 700; font-size: var(--wp--preset--font-size--small); cursor: pointer; border: 0; padding: .7rem 1rem; border-radius: 6px; background: var(--wp--preset--color--brand); color: #fff; display: inline-flex; align-items: center; justify-content: center; gap: .4rem; }
.vdt-add:hover { background: var(--wp--preset--color--brand-dark); }
.vdt-add.is-added { background: #fff; color: var(--wp--preset--color--brand-dark); box-shadow: inset 0 0 0 2px var(--wp--preset--color--brand); }
.vdt-product-top .vdt-add { font-size: var(--wp--preset--font-size--medium); padding: .85rem 1.5rem; }
.vdt-product-top a.is-secondary { background: transparent; color: var(--wp--preset--color--brand); box-shadow: inset 0 0 0 2px currentColor; }
.vdt-shop-empty { background: var(--wp--preset--color--mist); border-radius: 12px; padding: 1.25rem 1.5rem; }
.vdt-shop-empty p { margin: 0; }

.vdt-quote { display: grid; grid-template-columns: 1fr 420px; gap: clamp(1.5rem, 3vw, 3rem); padding-block: var(--wp--preset--spacing--50) var(--wp--preset--spacing--60); align-items: start; }
@media (max-width: 900px) { .vdt-quote { grid-template-columns: 1fr; } }
.vdt-quote h2 { font-size: var(--wp--preset--font-size--x-large); margin: 0 0 1rem; }
.vdt-quote-form { padding: clamp(1.25rem, 3vw, 2rem); display: grid; gap: 1rem; position: sticky; top: 140px; }
@media (max-width: 900px) { .vdt-quote-form { position: static; } }
.vdt-quote-form .wp-block-buttons button { font: inherit; border: 0; cursor: pointer; width: 100%; }
.vdt-quote-form .wp-block-button { width: 100%; }
.vdt-checks { display: flex; flex-wrap: wrap; gap: .5rem 1rem; }
.vdt-checks label { display: flex; gap: .4rem; align-items: center; }
.vdt-muted { color: var(--wp--preset--color--muted); margin: 0; }
.vdt-form-error { margin: 0; color: #B3261E; font-weight: 700; }
.vdt-line { display: grid; grid-template-columns: 84px 1fr auto auto; gap: 1rem; align-items: center; padding: .85rem 0; border-bottom: 1px solid var(--wp--preset--color--line); }
.vdt-line figure { margin: 0; width: 84px; aspect-ratio: 1; background: var(--wp--preset--color--mist); border-radius: 8px; display: grid; place-items: center; padding: .35rem; }
.vdt-line figure img { max-width: 100%; max-height: 100%; object-fit: contain; mix-blend-mode: multiply; }
.vdt-line-title a { font-weight: 700; color: var(--wp--preset--color--ink); text-decoration: none; }
.vdt-line-title a:hover { color: var(--wp--preset--color--brand); }
.vdt-line-title small { display: block; color: var(--wp--preset--color--muted); }
.vdt-qty { display: inline-flex; border: 1px solid #C9CAD4; border-radius: 6px; overflow: hidden; }
.vdt-qty button { font: inherit; width: 36px; border: 0; background: var(--wp--preset--color--mist); cursor: pointer; font-weight: 700; }
.vdt-qty input { width: 46px; text-align: center; border: 0; font: inherit; -moz-appearance: textfield; }
.vdt-remove { font: inherit; background: none; border: 0; color: var(--wp--preset--color--muted); cursor: pointer; text-decoration: underline; font-size: var(--wp--preset--font-size--small); }
@media (max-width: 560px) { .vdt-line { grid-template-columns: 64px 1fr; } .vdt-line figure { width: 64px; } .vdt-line .vdt-qty, .vdt-line .vdt-remove { grid-column: 2; justify-self: start; } }
.vdt-toast { position: fixed; left: 50%; bottom: 1.5rem; translate: -50% 120px; background: var(--wp--preset--color--graphite); color: #fff; padding: .85rem 1.1rem; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,.25); display: flex; gap: 1rem; align-items: center; z-index: 90; transition: translate .3s cubic-bezier(.2,.7,.2,1); max-width: calc(100% - 2rem); }
.vdt-toast.show { translate: -50% 0; }
.vdt-toast a { color: #8CC0E8; font-weight: 700; white-space: nowrap; }
@media (max-width: 900px) {
  .vdt-chips { flex-wrap: nowrap; overflow-x: auto; padding-bottom: .4rem; margin-inline: calc(-1 * clamp(1rem, 4vw, 2.5rem)); padding-inline: clamp(1rem, 4vw, 2.5rem); scrollbar-width: thin; }
  .vdt-chip { white-space: nowrap; flex-shrink: 0; }
  .vdt-shop-filters { gap: .9rem; }
  .vdt-shop-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; }
  .vdt-shop-card .vdt-add { margin: .5rem .75rem .75rem; padding: .6rem .5rem; }
  .vdt-shop-card .vdt-sc-body { padding: .75rem .75rem .25rem; }
}
"""

JS = r"""
/* ---- Offertelijst ---- */
const CART_KEY = "vdt-offertelijst";
let memCart = {};
function loadCart() { try { return JSON.parse(localStorage.getItem(CART_KEY)) || {}; } catch (e) { return memCart; } }
function saveCart(c) { memCart = c; try { localStorage.setItem(CART_KEY, JSON.stringify(c)); } catch (e) {} updateBadge(); }
const PBY = Object.fromEntries(PRODUCTS.map(p => [p.r, p]));
function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function updateBadge() {
  const n = Object.values(loadCart()).reduce((a, b) => a + b, 0);
  document.querySelectorAll(".vdt-cart-count").forEach(el => { el.textContent = n; el.classList.toggle("is-zero", n === 0); });
  document.querySelectorAll(".vdt-add").forEach(b => { const on = loadCart()[b.dataset.add]; b.classList.toggle("is-added", !!on); b.textContent = on ? "✓ Op offertelijst" : "Zet op offertelijst"; });
}
let toastTimer;
function toast(title) {
  let t = document.querySelector(".vdt-toast");
  if (!t) { t = document.createElement("div"); t.className = "vdt-toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
  t.innerHTML = `<span><strong>${esc(title)}</strong> staat op uw offertelijst</span><a href="#/offerte/">Bekijk lijst</a>`;
  t.classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("show"), 3500);
  const c = document.querySelector(".vdt-cart"); c.classList.remove("bump"); void c.offsetWidth; c.classList.add("bump");
}
document.addEventListener("click", e => {
  const b = e.target.closest(".vdt-add"); if (!b) return;
  const c = loadCart(); const r = b.dataset.add;
  if (c[r]) { location.hash = "#/offerte/"; return; }
  c[r] = 1; saveCart(c); toast(PBY[r] ? PBY[r].t : "Product");
});

/* ---- Shop ---- */
const state = { q: "", cat: "", sub: "", sort: "az" };
function lazyImages(root) {
  const imgs = root.querySelectorAll("img[data-img]");
  if (!("IntersectionObserver" in window)) { imgs.forEach(i => { i.src = IMG[i.dataset.img] || i.src; i.removeAttribute("data-img"); }); return; }
  const io = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { const i = en.target; if (IMG[i.dataset.img]) i.src = IMG[i.dataset.img]; i.removeAttribute("data-img"); io.unobserve(i); } }), { rootMargin: "300px" });
  imgs.forEach(i => io.observe(i));
}
function buildFilters() {
  const counts = {}; PRODUCTS.forEach(p => counts[p.c] = (counts[p.c] || 0) + 1);
  const cats = Object.keys(counts).filter(Boolean).sort();
  document.getElementById("vdt-cats").innerHTML = [["", "Alle", PRODUCTS.length], ...cats.map(c => [c, c, counts[c]])]
    .map(([v, l, n]) => `<button type="button" class="vdt-chip" data-cat="${esc(v)}" aria-pressed="${state.cat === v}">${esc(l)}<small>${n}</small></button>`).join("");
  const subs = [...new Set(PRODUCTS.filter(p => p.c === state.cat).map(p => p.s).filter(Boolean))].sort();
  const sw = document.getElementById("vdt-sub-wrap"); sw.hidden = !state.cat || subs.length < 2;
  document.getElementById("vdt-sub").innerHTML = `<option value="">Alle subcategorieën</option>` + subs.map(s => `<option ${s === state.sub ? "selected" : ""}>${esc(s)}</option>`).join("");
}
function renderShop() {
  const q = state.q.trim().toLowerCase();
  let list = PRODUCTS.filter(p => (!state.cat || p.c === state.cat) && (!state.sub || p.s === state.sub) && (!q || (p.t + " " + p.c + " " + p.s + " " + p.d).toLowerCase().includes(q)));
  const by = { az: (a, b) => a.t.localeCompare(b.t, "nl"), za: (a, b) => b.t.localeCompare(a.t, "nl"), cat: (a, b) => (a.c + a.s + a.t).localeCompare(b.c + b.s + b.t, "nl") }[state.sort];
  list.sort(by);
  document.getElementById("vdt-count").textContent = `${list.length} ${list.length === 1 ? "product" : "producten"}`;
  document.getElementById("vdt-empty").hidden = list.length > 0;
  const grid = document.getElementById("vdt-grid");
  grid.innerHTML = list.map(p => `<article class="vdt-shop-card"><a href="#${esc(p.r)}"><figure>${p.i ? `<img data-img="${p.i}" alt="" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">` : ""}</figure><span class="vdt-sc-body"><span class="vdt-sc-cat">${esc(p.s || p.c)}</span><span class="vdt-sc-title">${esc(p.t)}</span><span class="vdt-sc-price">Prijs op aanvraag</span></span></a><button type="button" class="vdt-add" data-add="${esc(p.r)}">Zet op offertelijst</button></article>`).join("");
  lazyImages(grid); updateBadge();
}
document.addEventListener("click", e => {
  const chip = e.target.closest(".vdt-chip"); if (chip) { state.cat = chip.dataset.cat; state.sub = ""; buildFilters(); renderShop(); return; }
  if (e.target.id === "vdt-reset") { state.q = ""; state.cat = ""; state.sub = ""; document.getElementById("vdt-q").value = ""; buildFilters(); renderShop(); }
});
document.addEventListener("input", e => { if (e.target.id === "vdt-q") { state.q = e.target.value; renderShop(); } });
document.addEventListener("change", e => {
  if (e.target.id === "vdt-sub") { state.sub = e.target.value; renderShop(); }
  if (e.target.id === "vdt-sort") { state.sort = e.target.value; renderShop(); }
});

/* ---- Offertelijst-pagina ---- */
function renderCart() {
  const c = loadCart(); const items = Object.keys(c).filter(r => PBY[r]);
  document.getElementById("vdt-cart-empty").hidden = items.length > 0;
  const box = document.getElementById("vdt-cart-items");
  box.innerHTML = items.map(r => { const p = PBY[r]; return `<div class="vdt-line" data-r="${esc(r)}"><figure>${p.i ? `<img data-img="${p.i}" alt="">` : ""}</figure><div class="vdt-line-title"><a href="#${esc(r)}">${esc(p.t)}</a><small>${esc([p.c, p.s].filter(Boolean).join(" › "))}</small></div><div class="vdt-qty"><button type="button" data-q="-1" aria-label="Minder">−</button><input type="number" min="1" value="${c[r]}" aria-label="Aantal"><button type="button" data-q="1" aria-label="Meer">+</button></div><button type="button" class="vdt-remove">Verwijderen</button></div>`; }).join("");
  box.querySelectorAll("img[data-img]").forEach(i => { i.src = IMG[i.dataset.img] || ""; i.removeAttribute("data-img"); });
}
document.addEventListener("click", e => {
  const line = e.target.closest(".vdt-line"); if (!line) return;
  const c = loadCart(); const r = line.dataset.r;
  if (e.target.closest(".vdt-remove")) { delete c[r]; saveCart(c); renderCart(); return; }
  const q = e.target.closest("[data-q]"); if (q) { c[r] = Math.max(1, (c[r] || 1) + Number(q.dataset.q)); saveCart(c); line.querySelector("input").value = c[r]; }
});
document.addEventListener("change", e => {
  const line = e.target.closest(".vdt-line"); if (!line || e.target.tagName !== "INPUT") return;
  const c = loadCart(); c[line.dataset.r] = Math.max(1, parseInt(e.target.value, 10) || 1); e.target.value = c[line.dataset.r]; saveCart(c);
});
document.addEventListener("submit", e => {
  if (e.target.id !== "vdt-quote-form") return; e.preventDefault();
  const f = e.target, err = document.getElementById("vdt-form-error"), c = loadCart(), items = Object.keys(c).filter(r => PBY[r]);
  const missing = ["naam", "bedrijf", "email"].filter(n => !f[n].value.trim());
  if (!items.length) { err.textContent = "Voeg eerst minimaal één product toe aan uw offertelijst."; err.hidden = false; return; }
  if (missing.length || !f.email.checkValidity()) { err.textContent = "Vul uw naam, bedrijf en een geldig e-mailadres in."; err.hidden = false; f[missing[0] || "email"].focus(); return; }
  err.hidden = true;
  const interest = [...f.querySelectorAll("[name=interesse]:checked")].map(x => x.value).join(", ") || "-";
  const lines = items.map(r => `- ${c[r]}x ${PBY[r].t} (${PBY[r].c}${PBY[r].s ? " › " + PBY[r].s : ""})`);
  const body = [`Offerteaanvraag via de website`, ``, ...lines, ``, `Interesse: ${interest}`, `Naam: ${f.naam.value}`, `Bedrijf: ${f.bedrijf.value}`, `E-mail: ${f.email.value}`, `Telefoon: ${f.telefoon.value || "-"}`, ``, `Opmerking:`, f.opmerking.value || "-"].join("\n");
  location.href = `mailto:info@vandentempel.nl?subject=${encodeURIComponent("Offerteaanvraag " + f.bedrijf.value)}&body=${encodeURIComponent(body)}`;
});
"""
