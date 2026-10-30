"""Build the WordPress import (WXR), redirect list and static preview.

Usage:
  python3 -I build.py <content.json> <vandentempel-dir> [--preview-media <dir>]

<vandentempel-dir> is the folder holding wp-content/, import/ and preview/.
--preview-media points at a folder with downloaded images named by
media_name(url); without it the preview links images on vandentempel.nl.
"""

import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ORIGIN = "https://vandentempel.nl"
THEME = "/wp-content/themes/vandentempel"

CATEGORIES = [
    ("/producten/transformator-meetapparatuur/", "Transformator-meetapparatuur", "/media/yootheme/cache/8d/transformator-8d8ab686.jpg"),
    ("/producten/hoogspanningsbeproeving/", "Hoogspanningsbeproeving", "/media/yootheme/cache/32/Hoogspanningsbeproeving-32ab939b.jpg"),
    ("/producten/kabelmeetapparatuur/", "Kabelmeetapparatuur", "/media/yootheme/cache/49/kabels_2022-49b399e3.jpg"),
    ("/producten/isoleerolie/", "Isoleerolie", "/media/yootheme/cache/1b/Isoleerolie-1b925e84.jpg"),
    ("/producten/onderstations-relais-testsystemen/", "Onderstations, relais-testsystemen", "/media/yootheme/cache/c8/onderstation-c88e6020.jpg"),
    ("/producten/thermografische-camera-s/", "Thermografie", "/media/yootheme/cache/b8/Thermografie-b87fed21.jpg"),
    ("/producten/power-quality-meetapparatuur/", "Power Quality meetapparatuur", "/media/yootheme/cache/99/Power-Quality-Analyzer_2_750x500px-9917759f.jpg"),
    ("/producten/overige-test-en-meetapparatuur/", "Overige test- en meetapparatuur", "/media/yootheme/cache/3a/motoren-3a480b9c.jpg"),
]

HIGHLIGHTS = [  # "Productnieuws" on the current home page, texts verbatim.
    ("WiseGrid ALLINA T1", "Nieuw in ons assortiment! Dé multifunctionele transformator- en onderstationtester.",
     "/images/producten/WiseGrid/Allina-T1_900x900px_web.jpg",
     "/nl/producten/transformator-meetapparatuur/mobiele-testsystemen/item/onderstation"),
    ("DV Power TWR-250B", "Drie-fase analyzer. Meet onder andere de wikkelingsweerstand en de wikkelverhouding (turns ratio) van transformatoren.",
     "/images/producten/DVPower/TWR250B-Isometric_800x800px.jpg",
     "/nl/producten/transformator-meetapparatuur/ratiometers/item/wikkelingsweerstand-en-ratio-analyzer-twr-250b"),
    ("JUPITER E", "Eenvoudig uitkleuren en kabels selecteren in laag- en middenspanning.",
     "/images/producten/Made/Jupiter-E-set_2000x2000px_web.jpg",
     "/nl/producten/kabelmeetapparatuur/selectie-identificatie-veiligheid/item/jupiter-e-kabel-en-fase-identificatie-2"),
    ("Raytech CAPO 12", "Voor het meten van de capaciteit en tangens-delta van vermogenstransformatoren.",
     "/images/producten/Raytech/70059-capo-12-01a_800x800.jpg",
     "/nl/producten/transformator-meetapparatuur/isolatiebeproeving/item/capo-12-capaciteit-en-tangens-delta"),
]

ICONS = {
    "advies": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M8.5 11h7M8.5 14h4"/></svg>',
    "levering": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/></svg>',
    "nazorg": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18v3h3l6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/></svg>',
    "training": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 9l10-5 10 5-10 5L2 9z"/><path d="M6 11v5c3 2.5 9 2.5 12 0v-5"/><path d="M22 9v6"/></svg>',
}


def media_name(url):
    ext = re.search(r"\.(jpe?g|png|webp|gif|svg)(?:\?|$)", url, re.I)
    return hashlib.md5(url.encode()).hexdigest()[:16] + "." + (ext.group(1).lower() if ext else "jpg")


def text_of(fragment):
    return html.unescape(re.sub(r"<[^>]+>|\s+", " ", fragment)).strip()


def first_sentences(fragment, limit=190):
    for para in re.findall(r"(?s)<p>(.*?)</p>", fragment):
        t = text_of(para)
        if len(t) > 40:
            if len(t) <= limit:
                return t
            cut = t[:limit].rsplit(". ", 1)[0]
            return (cut if len(cut) > 60 else t[:limit].rsplit(" ", 1)[0]) + ("." if not cut.endswith(".") else "") if len(cut) > 60 else t[:limit].rsplit(" ", 1)[0] + " …"
    return ""


def new_from_old(old):
    p = old.rstrip("/")[len("/nl"):]
    p = p.replace("/item/", "/").replace("/service-apparaten/verhuur", "/verhuur")
    p = re.sub(r"/nieuws/\d+-", "/nieuws/", p)
    return p + "/"


# ---------------------------------------------------------------- blocks

def b_par(inner, cls="", size="", color=""):
    attrs, classes = {}, []
    if cls:
        attrs["className"] = cls
        classes.append(cls)
    if color:
        attrs["textColor"] = color
        classes += [f"has-{color}-color", "has-text-color"]
    if size:
        attrs["fontSize"] = size
        classes.append(f"has-{size}-font-size")
    a = (" " + json.dumps(attrs, ensure_ascii=False)) if attrs else ""
    c = f' class="{" ".join(classes)}"' if classes else ""
    return f"<!-- wp:paragraph{a} -->\n<p{c}>{inner}</p>\n<!-- /wp:paragraph -->"


def b_heading(inner, level=2, cls="", size=""):
    attrs = {"level": level} if level != 2 else {}
    classes = ["wp-block-heading"]
    if cls:
        attrs["className"] = cls
        classes.append(cls)
    if size:
        attrs["fontSize"] = size
        classes.append(f"has-{size}-font-size")
    a = (" " + json.dumps(attrs, ensure_ascii=False)) if attrs else ""
    return f'<!-- wp:heading{a} -->\n<h{level} class="{" ".join(classes)}">{inner}</h{level}>\n<!-- /wp:heading -->'


def b_group(inner, cls="", tag="div", bg="", fg="", align=""):
    attrs = {}
    classes = ["wp-block-group"]
    if tag != "div":
        attrs["tagName"] = tag
    if align:
        attrs["align"] = align
        classes.append(f"align{align}")
    if cls:
        attrs["className"] = cls
        classes.append(cls)
    if fg:
        attrs["textColor"] = fg
        classes += [f"has-{fg}-color", "has-text-color"]
    if bg:
        attrs["backgroundColor"] = bg
        classes += [f"has-{bg}-background-color", "has-background"]
    attrs["layout"] = {"type": "default"}
    a = " " + json.dumps(attrs, ensure_ascii=False)
    return f'<!-- wp:group{a} -->\n<{tag} class="{" ".join(classes)}">{inner}</{tag}>\n<!-- /wp:group -->'


def b_buttons(buttons, cls=""):
    out = []
    for label, href, style in buttons:
        attrs = {"className": f"is-style-{style}"} if style else {}
        a = (" " + json.dumps(attrs)) if attrs else ""
        c = f" is-style-{style}" if style else ""
        out.append(f'<!-- wp:button{a} -->\n<div class="wp-block-button{c}"><a class="wp-block-button__link wp-element-button" href="{href}">{label}</a></div>\n<!-- /wp:button -->')
    attrs = {"className": cls} if cls else {}
    a = (" " + json.dumps(attrs)) if attrs else ""
    c = f" {cls}" if cls else ""
    return f'<!-- wp:buttons{a} -->\n<div class="wp-block-buttons{c}">' + "\n\n".join(out) + "</div>\n<!-- /wp:buttons -->"


def b_html(markup):
    return f"<!-- wp:html -->\n{markup}\n<!-- /wp:html -->"


def b_list_links(items, cls="vdt-linkgrid"):
    lis = "\n".join(f'<!-- wp:list-item -->\n<li><a href="{h}">{html.escape(t)}</a></li>\n<!-- /wp:list-item -->' for t, h in items)
    return f'<!-- wp:list {{"className":"{cls}"}} -->\n<ul class="wp-block-list {cls}">{lis}</ul>\n<!-- /wp:list -->'


def section(inner, bg="", fg="", cls="vdt-section"):
    return b_group(b_group(inner, cls="vdt-wrap"), cls=cls, bg=bg, fg=fg, align="full")


def section_head(eyebrow, title, link=None):
    right = b_par(f'<a class="vdt-arrow-link" href="{link[1]}">{link[0]}</a>') if link else ""
    left = b_group(b_par(eyebrow, cls="vdt-eyebrow") + "\n\n" + b_heading(title))
    return b_group(left + ("\n\n" + right if right else ""), cls="vdt-section-head")


def product_cards(cards):
    out = []
    for title, href, img, teaser in cards:
        fig = f'<figure><img src="{img}" alt="" loading="lazy"></figure>' if img else '<figure></figure>'
        t = f'<span class="vdt-product-teaser">{html.escape(teaser)}</span>' if teaser else ""
        out.append(f'<a class="vdt-product is-style-vdt-card" href="{href}">{fig}<span class="vdt-product-body"><span class="vdt-product-title">{html.escape(title)}</span>{t}</span></a>')
    return b_html('<div class="vdt-products">' + "".join(out) + "</div>")


# ---------------------------------------------------------------- pages

def build_home(P, news):
    def img(path):
        return ORIGIN + path
    hero = (
        f'<!-- wp:cover {{"url":"/wp-content/themes/vandentempel/assets/images/hero-vandentempel-4k.jpg","dimRatio":90,"minHeight":620,"align":"full","className":"vdt-hero","layout":{{"type":"default"}}}} -->\n'
        f'<div class="wp-block-cover alignfull vdt-hero" style="min-height:620px"><img class="wp-block-cover__image-background" alt="" src="/wp-content/themes/vandentempel/assets/images/hero-vandentempel-4k.jpg" data-object-fit="cover"/><span aria-hidden="true" class="wp-block-cover__background has-background-dim-90 has-background-dim"></span><div class="wp-block-cover__inner-container">'
        + b_group(
            b_par("Test- en meetapparatuur voor de elektrische infrastructuur", cls="vdt-eyebrow")
            + "\n\n" + b_heading("Zekerheid in spanning", level=1)
            + "\n\n" + b_par("Apparatuur voor meten aan en testen van de elektrische infrastructuur, vanaf opwekking tot en met distributie. Met gedegen advies van specialisten die zelf meet-ervaring hebben.", cls="vdt-lead", size="large")
            + "\n\n" + b_buttons([("Bekijk producten", "/producten/", ""), ("Advies aanvragen", "/contact/", "vdt-ghost")])
            + "\n\n" + b_group(
                b_par("<strong>Sinds 1974</strong>specialist in meet- en testtechniek")
                + "\n\n" + b_par("<strong>5 markten</strong>België, Nederland, Luxemburg, Antillen, Suriname")
                + "\n\n" + b_par("<strong>Eigen werkplaats</strong>onderhoud, reparatie en kalibratie"),
                cls="vdt-hero-stats"),
            cls="vdt-wrap")
        + "</div></div>\n<!-- /wp:cover -->"
    )
    tiles = "".join(
        f'<a class="vdt-tile" href="{h}"><img src="{img(i)}" alt="" loading="lazy"><span>{html.escape(t)}{subcount(P, h)}</span></a>'
        for h, t, i in CATEGORIES)
    cats = section(section_head("Producten", "Onze productgroepen", ("Alle producten", "/producten/")) + "\n\n" + b_html(f'<div class="vdt-tiles">{tiles}</div>'))

    def feat(icon, title, text):
        return b_group(b_html(f'<div class="vdt-feature-icon">{ICONS[icon]}</div>') + "\n\n" + b_heading(title, level=3) + "\n\n" + b_par(text), cls="vdt-feature")
    features = section(
        section_head("Waarom Vandentempel", "Zekerheid in spanning")
        + "\n\n" + b_group(
            feat("advies", "Advies", "Gedegen advies om tot een juiste keuze van meetapparatuur te komen. Uw adviseur heeft zelf meet-ervaring.")
            + "\n\n" + feat("levering", "Levering", "Apparatuur voor meten aan en testen van de elektrische infrastructuur, vanaf opwekking tot en met distributie.")
            + "\n\n" + feat("nazorg", "Nazorg", "Eigen werkplaats met getrainde technici, voor onderhoud, reparaties en kalibraties van uw meetapparatuur.")
            + "\n\n" + feat("training", "Trainingen", "Producttrainingen: theorie én praktijk in het eigen didactische net van Vandentempel."),
            cls="vdt-features"),
        bg="graphite", fg="white")
    highlights = section(
        section_head("Productnieuws", "Nieuw en uitgelicht", ("Alle producten", "/producten/"))
        + "\n\n" + product_cards([(t, new_from_old(link), img(i), d) for t, d, i, link in HIGHLIGHTS]),
        bg="mist")

    def service_card(title, href, image, text):
        return b_group(
            b_html(f'<a href="{href}" class="vdt-card-media"><img src="{img(image)}" alt="" loading="lazy"></a>')
            + "\n\n" + b_group(b_heading(f'<a href="{href}">{title}</a>', level=3) + "\n\n" + b_par(text) + "\n\n" + b_par(f'<a class="vdt-arrow-link" href="{href}">Meer over {title.lower()}</a>'), cls="vdt-card-body"),
            cls="is-style-vdt-card")
    svc = section(
        section_head("Diensten", "Meer dan levering alleen")
        + "\n\n" + b_group(
            service_card("Service", "/service/", "/media/yootheme/cache/68/kalibratie-6855fbad.jpg", "Kalibratie, (preventief) onderhoud en reparatie van elektrotechnische meetapparatuur in onze eigen werkplaats.")
            + "\n\n" + service_card("Trainingen", "/trainingen/", "/media/yootheme/cache/fe/opfriscursus-fe07d7ef.jpg", "Producttrainingen met theorie én praktijk, in het eigen didactische net van Vandentempel.")
            + "\n\n" + service_card("Verhuur", "/verhuur/", "/media/yootheme/cache/98/Verhuur_001_96dpi-98868538.jpg", "Meetapparatuur tijdelijk nodig? Huur apparatuur voor een project of als vervanging tijdens onderhoud."),
            cls="vdt-cards-3"))
    news_cards = "".join(
        f'<a class="vdt-news is-style-vdt-card" href="{n["new"]}">'
        + (f'<figure><img src="{n["images"][0]}" alt="" loading="lazy"></figure>' if n["images"] else "")
        + f'<span class="vdt-news-body"><time datetime="{n["date"] or ""}">{nl_date(n["date"])}</time><span class="vdt-news-title">{html.escape(n["title"])}</span></span></a>'
        for n in news[:3])
    newsblock = section(section_head("Nieuws", "Actueel bij Vandentempel", ("Alle nieuws", "/nieuws/")) + "\n\n" + b_html(f'<div class="vdt-news-grid">{news_cards}</div>'), bg="mist")
    vac = [p for p in P.values() if p["kind"] == "vacancy"]
    jobs = ""
    if vac:
        text = b_group(
            b_par("Werken bij Vandentempel", cls="vdt-eyebrow")
            + "\n\n" + b_heading(f"We zoeken {len(vac)} nieuwe collega's")
            + "\n\n" + b_par("Door toenemende groei van activiteiten zoeken we ondernemende mensen met een elektrotechnische of commerciële achtergrond. Openstaand: " + " en ".join(v["title"] for v in vac) + "."),
            cls="vdt-jobs-text")
        band = b_group(text + "\n\n" + b_buttons([("Bekijk vacatures", "/vacatures/", "")]), cls="vdt-jobs-band")
        jobs = section(band, cls="vdt-section is-tight")
    return "\n\n".join(x for x in [hero, cats, features, highlights, svc, newsblock, jobs, cta_block()] if x)


def cta_block():
    return section(
        b_group(
            b_group(b_heading("Advies nodig over meetapparatuur?") + "\n\n" + b_par("Onze adviseurs hebben zelf meet-ervaring en denken graag met u mee. Bel ons of stuur uw vraag.", size="large"))
            + "\n\n" + b_buttons([("Neem contact op", "/contact/", ""), ("+31 (0)38 444 90 09", "tel:+31384449009", "vdt-ghost")]),
            cls="vdt-cta-inner"),
        cls="vdt-section is-tight vdt-cta-wrap")


MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]


def nl_date(iso):
    if not iso:
        return ""
    y, m, d = (int(x) for x in iso[:10].split("-"))
    return f"{d} {MONTHS[m - 1]} {y}"


def subcount(P, path):
    n = len([c for c in children_of(P, path) if c["kind"] != "product"])
    return f"<small>{n} productgroepen</small>" if n > 1 else ""


def children_of(P, path):
    depth = path.count("/")
    return [p for p in P.values() if p["new"].startswith(path) and p["new"].count("/") == depth + 1]


def parent_path(P, path):
    parts = path.strip("/").split("/")
    while len(parts) > 1:
        parts = parts[:-1]
        cand = "/" + "/".join(parts) + "/"
        if cand in P:
            return cand
    return None


def crumbs(P, path):
    trail, cur = [], parent_path(P, path)
    while cur:
        trail.append((P[cur]["title"], cur))
        cur = parent_path(P, cur)
    if not trail:
        return ""
    links = " / ".join(f'<a href="{h}">{html.escape(t)}</a>' for t, h in reversed(trail))
    return b_par(links, cls="vdt-breadcrumbs")


def lead_image(p):
    for i in p["images"]:
        if "/media/zoo/images/" in i or "/images/producten/" in i:
            return i
    return p["images"][0] if p["images"] else ""


VAC_CONTACT = ("Luuk Groot", "Commercieel Manager", "+31683173300", "+31 (0)6 83 17 33 00", "l.groot@vandentempel.nl")


def make_vacancies(P):
    """Turn vacancy news posts into pages under /vacatures/."""
    vac = sorted([p for p in P.values() if p["kind"] == "news" and "/vacature-" in p["new"]], key=lambda n: n["date"] or "", reverse=True)
    if not vac:
        return
    for n in vac:
        body = n["body"]
        pdf = re.search(r'href="([^"]+\.pdf)"', body)
        role = re.search(r"(?s)<h2>(?:<strong>)?(.*?)(?:</strong>)?\s*</h2>", body)
        region = re.search(r"(?s)</h2>\s*<p><em>(.*?)</em></p>", body)
        title = text_of(role.group(1)) if role else n["title"].replace("Vacature voor ", "")
        # Drop the PDF list, banner image, intro line, role heading and region: they move to the page header/sidebar.
        start = re.search(r"(?s)<p><strong>Wat ga je", body)
        body = body[start.start():] if start else body
        body = re.sub(r"(?s)<p><strong>Meer weten\?</strong></p>.*", "", body)
        body = re.sub(r"<p><strong>(.*?)\s*</strong></p>", lambda m: f"<h2>{m.group(1).strip()}</h2>", body)
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        path = f"/vacatures/{slug}/"
        P[path] = {"old": "", "new": path, "kind": "vacancy", "title": title, "date": n["date"], "teasers": {},
                   "description": f"Vacature {title} bij Vandentempel in Hattem, regio {text_of(region.group(1)) if region else 'Nederland/België'}.",
                   "body": body, "images": [], "region": text_of(region.group(1)) if region else "",
                   "pdf": pdf.group(1) if pdf else "", "news": n["new"]}
    P["/vacatures/"] = {"old": "", "new": "/vacatures/", "kind": "page", "title": "Werken bij Vandentempel", "date": None,
                        "teasers": {}, "images": [], "body": "",
                        "description": "Bouw mee aan zekerheid in spanning. Bekijk onze vacatures in test- en meetapparatuur."}


def vacancy_apply_card(v):
    name, role, tel, tel_txt, mail = VAC_CONTACT
    pdf = f'<br><a href="{v["pdf"]}">Download het volledige vacatureprofiel (pdf)</a>' if v.get("pdf") else ""
    return b_group(
        b_heading("Interesse?", level=3)
        + "\n\n" + b_par(f"Neem contact op met <strong>{name}</strong>, {role.lower()} van Vandentempel.")
        + "\n\n" + b_buttons([("Solliciteer per e-mail", f"mailto:{mail}?subject=Sollicitatie%20{v['title'].replace(' ', '%20')}", ""), (f"Bel {tel_txt}", f"tel:{tel}", "outline")])
        + "\n\n" + b_par(f'<a href="mailto:{mail}">{mail}</a>{pdf}', size="small"),
        cls="is-style-vdt-card vdt-apply-card")


def job_teaser(v):
    """Short summary from the vacancy's own text (role-specific tasks and profile)."""
    t = v["title"].lower()
    if "technisch adviseur" in t:
        return "Adviseren, verkopen en positioneren van hoogwaardige test- en meetapparatuur, zoals van BAUR, Fluke en KoCoS. Met operationele kennis van hoog- en middenspanning."
    if "accountmanager" in t:
        return "Relaties bezoeken, onderhouden en uitbouwen, en de technisch specialisten inschakelen voor de juiste adviezen en offertes. Commercieel gedreven, liefst in een technische omgeving."
    return first_sentences(v["body"], 170)


def vacancies_overview(P):
    vac = sorted([p for p in P.values() if p["kind"] == "vacancy"], key=lambda n: n["date"] or "", reverse=True)
    cards = "".join(
        f'<a class="vdt-job" href="{v["new"]}"><span class="vdt-job-meta">'
        f'<span>{html.escape(v["region"])}</span><span>Hattem of thuis</span></span>'
        f'<span class="vdt-job-title">{html.escape(v["title"])}</span>'
        f'<span class="vdt-job-text">{html.escape(job_teaser(v))}</span>'
        f'<span class="vdt-arrow-link">Bekijk vacature</span></a>'
        for v in vac)
    perks = [("Zelfstandige functie", "Een initiatiefrijke rol met ruimte voor eigen inbreng, binnen een stabiel en gezond bedrijf."),
             ("Leren en ontwikkelen", "Ruimte, tijd en budget voor opleidingen, nieuwe projecten en een persoonlijk ontwikkeltraject."),
             ("Goede voorwaarden", "Pensioenregeling, opleidingsregeling, bedrijfsfitness, thuiswerkplek en een auto."),
             ("Sterke familiecultuur", "Een enthousiast team waarvan velen al jarenlang verbonden zijn aan Vandentempel.")]
    perk_blocks = "\n\n".join(b_group(b_html(f'<div class="vdt-feature-icon">{ICONS[i]}</div>') + "\n\n" + b_heading(t, level=3) + "\n\n" + b_par(d), cls="vdt-feature")
                               for (t, d), i in zip(perks, ["nazorg", "training", "levering", "advies"]))
    name, role, tel, tel_txt, mail = VAC_CONTACT
    return "\n\n".join([
        b_par(f"Door toenemende groei van activiteiten zoeken we ondernemende collega's. Bij Vandentempel werk je al sinds 1974 aan test- en meetapparatuur voor de elektrische infrastructuur, samen met specialisten die zelf meet-ervaring hebben.", size="large"),
        b_heading(f"Openstaande vacatures ({len(vac)})", cls="alignwide"),
        b_html(f'<div class="vdt-jobs alignwide">{cards}</div>'),
        b_heading("Wat we je bieden", cls="alignwide"),
        b_group(perk_blocks, cls="vdt-features alignwide"),
        b_group(
            b_group(b_heading("Vragen over een vacature?") + "\n\n" + b_par(f"Neem contact op met {name}, {role.lower()} van Vandentempel. Bel <a href=\"tel:{tel}\">{tel_txt}</a> of mail naar <a href=\"mailto:{mail}\">{mail}</a>.", size="large"))
            + "\n\n" + b_buttons([("Mail Luuk", f"mailto:{mail}", ""), (f"Bel {tel_txt}", f"tel:{tel}", "vdt-ghost")]),
            cls="vdt-cta-inner alignwide"),
    ])


def page_content(P, p, news):
    path = p["new"]
    if path == "/vacatures/":
        return vacancies_overview(P)
    if p["kind"] == "vacancy":
        others = [v for v in P.values() if v["kind"] == "vacancy" and v["new"] != path]
        more = b_par("Bekijk ook onze andere vacature: " + ", ".join(f'<a href="{o["new"]}">{html.escape(o["title"])}</a>' for o in others) + ".") if others else ""
        return (crumbs(P, path).replace('"vdt-breadcrumbs"', '"vdt-breadcrumbs alignwide"').replace('class="vdt-breadcrumbs"', 'class="vdt-breadcrumbs alignwide"') + "\n\n"
                + '<!-- wp:columns {"align":"wide","className":"vdt-job-detail"} -->\n<div class="wp-block-columns alignwide vdt-job-detail">'
                + '<!-- wp:column {"width":"64%"} -->\n<div class="wp-block-column" style="flex-basis:64%">' + p["body"] + ("\n\n" + more if more else "") + "</div>\n<!-- /wp:column -->\n\n"
                + '<!-- wp:column -->\n<div class="wp-block-column">' + vacancy_apply_card(p) + "</div>\n<!-- /wp:column --></div>\n<!-- /wp:columns -->")
    if path == "/":
        return build_home(P, news)
    if path == "/contact/":
        return contact_page()
    kids = sorted(children_of(P, path), key=lambda c: (c["kind"] == "product", c["title"].lower()))
    parts = [crumbs(P, path)] if path.count("/") > 2 else []
    if path == "/producten/":
        tiles = "".join(f'<a class="vdt-tile" href="{h}"><img src="{ORIGIN + i}" alt="" loading="lazy"><span>{html.escape(t)}</span></a>' for h, t, i in CATEGORIES)
        parts.append(b_par("Vandentempel levert apparatuur voor meten aan en testen van de elektrische infrastructuur, vanaf opwekking tot en met distributie. Kies een productgroep.", size="large"))
        parts.append(b_html(f'<div class="vdt-tiles alignwide">{tiles}</div>'))
        return "\n\n".join(parts) + "\n\n" + cta_block()
    if p["kind"] == "product":
        img = lead_image(p)
        body = p["body"]
        intro_m = re.match(r"(?s)\s*(<p>.*?</p>)", body)
        intro = intro_m.group(1) if intro_m else ""
        rest = body[intro_m.end():] if intro_m else body
        cols = (
            '<!-- wp:columns {"align":"wide","className":"vdt-product-top"} -->\n<div class="wp-block-columns alignwide vdt-product-top">'
            + '<!-- wp:column -->\n<div class="wp-block-column">'
            + (f'<!-- wp:image {{"className":"vdt-product-image"}} -->\n<figure class="wp-block-image vdt-product-image"><img src="{img}" alt="{html.escape(p["title"])}"/></figure>\n<!-- /wp:image -->' if img else "")
            + "</div>\n<!-- /wp:column -->\n\n<!-- wp:column -->\n<div class=\"wp-block-column\">"
            + (f"<!-- wp:paragraph {{\"fontSize\":\"large\"}} -->\n{intro.replace('<p>', '<p class=\"has-large-font-size\">', 1)}\n<!-- /wp:paragraph -->" if intro else "")
            + "\n\n" + b_buttons([("Offerte of advies aanvragen", "/contact/", ""), ("Bel +31 (0)38 444 90 09", "tel:+31384449009", "outline")])
            + "\n\n" + b_par("Ook voor service, kalibratie en verhuur kunt u bij ons terecht.", size="small")
            + "</div>\n<!-- /wp:column --></div>\n<!-- /wp:columns -->"
        )
        parts += [cols, rest]
        return "\n\n".join(x for x in parts if x)
    if p["body"]:
        parts.append(p["body"])
    sub = [k for k in kids if k["kind"] != "product"]
    prods = [k for k in kids if k["kind"] == "product"]
    if sub:
        parts.append(b_heading("Productgroepen" if path.startswith("/producten/") else "Meer informatie", cls="alignwide"))
        if any(p["teasers"].get(k["new"]) for k in sub):
            cards = "".join(
                f'<a class="vdt-subcat" href="{k["new"]}"><span class="vdt-subcat-title">{html.escape(k["title"])}</span><span class="vdt-subcat-text">{html.escape(p["teasers"].get(k["new"], ""))}</span></a>'
                for k in sub)
            parts.append(b_html(f'<div class="vdt-subcats alignwide">{cards}</div>'))
        else:
            parts.append(b_list_links([(k["title"], k["new"]) for k in sub], cls="vdt-linkgrid alignwide"))
    if prods:
        parts.append(b_heading("Producten", cls="alignwide"))
        parts.append(product_cards([(k["title"], k["new"], lead_image(k), p["teasers"].get(k["new"]) or "") for k in prods]).replace('<div class="vdt-products">', '<div class="vdt-products alignwide">'))
    if path.startswith("/producten/") or path in ("/service/", "/verhuur/", "/trainingen/"):
        parts.append(cta_block())
    return "\n\n".join(x for x in parts if x)


def contact_page():
    details = (
        b_heading("Vandentempel, zekerheid in spanning!")
        + "\n\n" + b_par("Wilt u meer weten, advies over meetapparatuur of een offerte? Bel ons, stuur een e-mail of maak een afspraak. Wij komen graag met u in contact.", size="large")
        + "\n\n" + b_buttons([("Mail info@vandentempel.nl", "mailto:info@vandentempel.nl", ""), ("Bel +31 (0)38 444 90 09", "tel:+31384449009", "outline")])
    )
    side = b_group(
        b_heading("Adresgegevens", level=3)
        + "\n\n" + b_par("Vandentempel<br>De Netelhorst 8<br>8051 KE Hattem")
        + "\n\n" + b_par('<a href="tel:+31384449009">+31 (0)38 444 90 09</a><br><a href="mailto:info@vandentempel.nl">info@vandentempel.nl</a>')
        + "\n\n" + b_heading("Openingstijden", level=3)
        + "\n\n" + b_par("Maandag t/m vrijdag: <strong>8.00 - 17.00 uur</strong><br>Zaterdag en zondag: <strong>gesloten</strong>"),
        cls="is-style-vdt-card vdt-contact-card")
    notice = b_group(
        b_par("<strong>Nieuwe rekeningnummers</strong>")
        + "\n\n" + b_par("Technisch Handels- en Adviesbureau Vandentempel B.V.<br>IBAN: NL09 INGB 0113 8386 70 · BIC: INGB NL2A")
        + "\n\n" + b_par("Vandentempel Service B.V.<br>IBAN: NL22 INGB 0113 8388 24 · BIC: INGB NL2A")
        + "\n\n" + b_par("Onze oude rekeningnummers komen te vervallen.", size="small"),
        cls="vdt-notice")
    return (
        '<!-- wp:columns {"align":"wide","className":"vdt-contact"} -->\n<div class="wp-block-columns alignwide vdt-contact">'
        + '<!-- wp:column {"width":"58%"} -->\n<div class="wp-block-column" style="flex-basis:58%">' + details + "\n\n" + notice + "</div>\n<!-- /wp:column -->\n\n"
        + '<!-- wp:column -->\n<div class="wp-block-column">' + side + "</div>\n<!-- /wp:column --></div>\n<!-- /wp:columns -->"
    )


def excerpt_for(p, parent, common):
    if p["new"] in ("/", "/contact/"):
        return ""
    if p["kind"] == "vacancy":
        return f"{p['region']} · Kantoor Hattem of thuis"
    t = (parent or {}).get("teasers", {}).get(p["new"]) if parent else ""
    desc = p["description"] if p["description"] not in common else ""
    for cand in (t, desc, "" if p["kind"] == "product" else first_sentences(p["body"])):
        if cand and cand.strip().lower() != p["title"].strip().lower():
            return cand
    return ""


# ---------------------------------------------------------------- WXR

def cdata(s):
    return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def wxr(P, news, contents, excerpts):
    ids, attach = {}, {}
    next_id = 100
    order = sorted(P.values(), key=lambda p: (p["new"].count("/"), p["new"]))
    for p in order:
        ids[p["new"]] = next_id
        next_id += 1
    items = []
    now = dt.datetime(2026, 10, 30, 9, 0, 0)
    for p in order:
        pid = ids[p["new"]]
        parent = parent_path(P, p["new"])
        is_post = p["kind"] == "news"
        date = (p["date"] + " 09:00:00") if p["date"] else now.strftime("%Y-%m-%d %H:%M:%S")
        slug = p["new"].strip("/").split("/")[-1] if p["new"] != "/" else "home"
        content = contents[p["new"]]
        for url in sorted(set(re.findall(r'(https://vandentempel\.nl/(?:images|media)/[^"\')\s]+\.(?:jpe?g|png|webp|gif))', content, re.I))):
            if url not in attach:
                attach[url] = (next_id, pid)
                next_id += 1
        template = "page-wide" if p["new"] in ("/",) else ""
        meta = f"""
		<wp:postmeta><wp:meta_key>_wp_page_template</wp:meta_key><wp:meta_value>{cdata(template)}</wp:meta_value></wp:postmeta>""" if template else ""
        meta += f"""
		<wp:postmeta><wp:meta_key>_vdt_old_url</wp:meta_key><wp:meta_value>{cdata(p["old"])}</wp:meta_value></wp:postmeta>"""
        items.append(f"""	<item>
		<title>{cdata(p["title"])}</title>
		<link>https://vandentempel.nl{escape(p["new"])}</link>
		<pubDate>{dt.datetime.fromisoformat(date).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
		<dc:creator>{cdata("vandentempel")}</dc:creator>
		<guid isPermaLink="false">https://vandentempel.nl/?p={pid}</guid>
		<description></description>
		<content:encoded>{cdata(content)}</content:encoded>
		<excerpt:encoded>{cdata(excerpts.get(p["new"], ""))}</excerpt:encoded>
		<wp:post_id>{pid}</wp:post_id>
		<wp:post_date>{cdata(date)}</wp:post_date>
		<wp:post_date_gmt>{cdata(date)}</wp:post_date_gmt>
		<wp:comment_status>{cdata("closed")}</wp:comment_status>
		<wp:ping_status>{cdata("closed")}</wp:ping_status>
		<wp:post_name>{cdata(slug)}</wp:post_name>
		<wp:status>{cdata("publish")}</wp:status>
		<wp:post_parent>{0 if is_post or not parent else ids[parent]}</wp:post_parent>
		<wp:menu_order>0</wp:menu_order>
		<wp:post_type>{cdata("post" if is_post else "page")}</wp:post_type>
		<wp:post_password>{cdata("")}</wp:post_password>
		<wp:is_sticky>0</wp:is_sticky>{('''
		<category domain="category" nicename="nieuws">''' + cdata("Nieuws") + "</category>") if is_post else ""}{meta}
	</item>""")
    for url, (aid, parent_id) in attach.items():
        name = url.rsplit("/", 1)[-1]
        items.append(f"""	<item>
		<title>{cdata(re.sub(r"[_-]+", " ", name.rsplit(".", 1)[0]))}</title>
		<link>{escape(url)}</link>
		<pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
		<dc:creator>{cdata("vandentempel")}</dc:creator>
		<guid isPermaLink="false">{escape(url)}</guid>
		<description></description>
		<content:encoded>{cdata("")}</content:encoded>
		<excerpt:encoded>{cdata("")}</excerpt:encoded>
		<wp:post_id>{aid}</wp:post_id>
		<wp:post_date>{cdata(now.strftime("%Y-%m-%d %H:%M:%S"))}</wp:post_date>
		<wp:post_date_gmt>{cdata(now.strftime("%Y-%m-%d %H:%M:%S"))}</wp:post_date_gmt>
		<wp:comment_status>{cdata("closed")}</wp:comment_status>
		<wp:ping_status>{cdata("closed")}</wp:ping_status>
		<wp:post_name>{cdata(re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"))}</wp:post_name>
		<wp:status>{cdata("inherit")}</wp:status>
		<wp:post_parent>{parent_id}</wp:post_parent>
		<wp:menu_order>0</wp:menu_order>
		<wp:post_type>{cdata("attachment")}</wp:post_type>
		<wp:post_password>{cdata("")}</wp:post_password>
		<wp:is_sticky>0</wp:is_sticky>
		<wp:attachment_url>{cdata(url)}</wp:attachment_url>
	</item>""")
    head = f"""<?xml version="1.0" encoding="UTF-8" ?>
<!-- WordPress eXtended RSS export for Vandentempel, generated by scripts/build.py from vandentempel.nl -->
<rss version="2.0" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:wfw="http://wellformedweb.org/CommentAPI/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
	<title>Vandentempel</title>
	<link>https://vandentempel.nl</link>
	<description>Zekerheid in spanning</description>
	<language>nl-NL</language>
	<wp:wxr_version>1.2</wp:wxr_version>
	<wp:base_site_url>https://vandentempel.nl</wp:base_site_url>
	<wp:base_blog_url>https://vandentempel.nl</wp:base_blog_url>
	<wp:author><wp:author_id>1</wp:author_id><wp:author_login>{cdata("vandentempel")}</wp:author_login><wp:author_email>{cdata("info@vandentempel.nl")}</wp:author_email><wp:author_display_name>{cdata("Vandentempel")}</wp:author_display_name><wp:author_first_name>{cdata("")}</wp:author_first_name><wp:author_last_name>{cdata("")}</wp:author_last_name></wp:author>
	<wp:category><wp:term_id>2</wp:term_id><wp:category_nicename>{cdata("nieuws")}</wp:category_nicename><wp:category_parent>{cdata("")}</wp:category_parent><wp:cat_name>{cdata("Nieuws")}</wp:cat_name></wp:category>
"""
    return head + "\n".join(items) + "\n</channel>\n</rss>\n", len(attach)


# ---------------------------------------------------------------- preview

PREVIEW_PAGES = ["/", "/producten/", "/producten/transformator-meetapparatuur/",
                 "/producten/transformator-meetapparatuur/isolatiebeproeving/",
                 "/producten/transformator-meetapparatuur/isolatiebeproeving/capo-12-capaciteit-en-tangens-delta/",
                 "/service/", "/over-vandentempel/", "/contact/", "/nieuws/"]


def preview_header(rel):
    sub = "".join(f'<li><a href="{rel}{h.strip("/")}/index.html">{html.escape(t)}</a></li>' for h, t, _ in CATEGORIES)
    nav = [("Service", "service"), ("Trainingen", "trainingen"), ("Verhuur", "verhuur"), ("Nieuws", "nieuws"), ("Over ons", "over-vandentempel")]
    links = "".join(f'<li><a href="{rel}{h}/index.html">{t}</a></li>' for t, h in nav)
    return f"""<div class="vdt-site-header">
<div class="wp-block-group vdt-topbar has-white-color has-graphite-background-color"><div class="vdt-wrap vdt-row"><p class="has-small-font-size">Specialisten in elektrotechnische meet- en testtechniek sinds 1974</p><p class="has-small-font-size"><a class="vdt-topbar-jobs" href="{rel}vacatures/index.html">Vacatures</a> · <a href="tel:+31384449009">+31 (0)38 444 90 09</a> · <a href="mailto:info@vandentempel.nl">info@vandentempel.nl</a> · <a href="#">FR</a></p></div></div>
<header class="vdt-header has-white-background-color"><div class="vdt-wrap vdt-row">
<a class="vdt-logo" href="{rel}index.html" aria-label="Vandentempel, naar de homepage"><img src="{rel}theme/assets/images/logo.svg" alt="Vandentempel" width="260" height="19"></a>
<input type="checkbox" id="vdt-menu" class="vdt-menu-toggle" aria-label="Menu"><label for="vdt-menu" class="vdt-burger" aria-hidden="true"><span></span></label>
<nav class="vdt-nav vdt-preview-nav" aria-label="Hoofdmenu"><ul>
<li class="has-sub"><a href="{rel}producten/index.html">Producten</a><ul class="vdt-sub">{sub}</ul></li>{links}
<li class="vdt-nav-cta"><a class="wp-block-button__link" href="{rel}contact/index.html">Contact</a></li></ul></nav>
</div></header></div>"""


def preview_page(P, p, content, excerpt, footer, rel, page_names):
    def fix_links(s):
        def repl(m):
            href = m.group(2)
            if href.startswith("/wp-content/themes/vandentempel/"):
                return f'{m.group(1)}"{rel}theme/{href[len("/wp-content/themes/vandentempel/"):]}"'
            if href.startswith("/") and not href.startswith("//"):
                target = href if href.endswith("/") else href + "/"
                if target in page_names:
                    return f'{m.group(1)}"{rel}{target.strip("/") + "/" if target != "/" else ""}index.html"'
                return f'{m.group(1)}"{ORIGIN}/nl{href if href != "/" else "/"}" target="_blank" rel="noopener"'
            return m.group(0)
        return re.sub(r'((?:href|src)=)"([^"]*)"', repl, s)

    is_home = p["new"] == "/"
    head = ""
    if not is_home:
        eyebrow = '<p class="vdt-eyebrow">Nieuws</p>' if p["kind"] == "news" else ""
        date = f'<p class="has-small-font-size">{nl_date(p["date"])}</p>' if p["kind"] == "news" else ""
        lead = f'<p class="vdt-lead has-large-font-size">{html.escape(excerpt)}</p>' if excerpt and p["kind"] != "news" else ""
        head = f'<div class="vdt-page-head has-brand-background-color has-white-color"><div class="vdt-wrap"><div class="vdt-page-head-inner">{eyebrow}<h1>{html.escape(p["title"])}</h1>{lead}{date}</div></div></div>'
    if p["new"] == "/nieuws/":
        content = news_listing(P)
    main_cls = "vdt-content vdt-content--wide" if is_home else "vdt-content"
    return fix_links(f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(p["title"] if not is_home else "Vandentempel, zekerheid in spanning")}</title>
<meta name="description" content="{html.escape(excerpt or 'Specialisten in elektrotechnische meet- en testtechniek sinds 1974.')}">
<link rel="stylesheet" href="{rel}preview-base.css"><link rel="stylesheet" href="{rel}theme/assets/css/theme.css">
</head><body>
<a class="vdt-skip" href="#inhoud">Naar de inhoud</a>
{preview_header(rel)}
<main id="inhoud" class="vdt-main">{head}<div class="{main_cls}{' vdt-page-body' if not is_home else ''}">{content}</div></main>
{footer}
</body></html>""")


def news_listing(P):
    news = sorted([p for p in P.values() if p["kind"] == "news"], key=lambda n: n["date"] or "", reverse=True)
    cards = "".join(
        f'<a class="vdt-news is-style-vdt-card" href="{n["new"]}">'
        + (f'<figure><img src="{n["images"][0]}" alt="" loading="lazy"></figure>' if n["images"] else "")
        + f'<span class="vdt-news-body"><time>{nl_date(n["date"])}</time><span class="vdt-news-title">{html.escape(n["title"])}</span><span class="vdt-news-excerpt">{html.escape(first_sentences(n["body"], 150))}</span></span></a>'
        for n in news)
    return f'<div class="vdt-news-grid alignwide">{cards}</div>'


# ---------------------------------------------------------------- main

def main():
    content_json, root = Path(sys.argv[1]), Path(sys.argv[2])
    media = None
    if "--preview-media" in sys.argv:
        media = Path(sys.argv[sys.argv.index("--preview-media") + 1])
    pages = json.loads(content_json.read_text())
    P = {}
    for p in pages:
        if p["new"] in P and len(P[p["new"]]["body"]) >= len(p["body"]):
            continue
        P[p["new"]] = p
    # "Nieuws" overview is the WordPress posts page: keep the page, drop its old listing.
    if "/nieuws/" in P:
        P["/nieuws/"]["body"] = ""
    make_vacancies(P)
    news = sorted([p for p in P.values() if p["kind"] == "news"], key=lambda n: n["date"] or "", reverse=True)

    counts = {}
    for p in P.values():
        counts[p["description"]] = counts.get(p["description"], 0) + 1
    common = {d for d, n in counts.items() if n > 2}  # site-wide default descriptions
    contents, excerpts = {}, {}
    for path, p in P.items():
        contents[path] = page_content(P, p, news) if path != "/nieuws/" else ""
        par = P.get(parent_path(P, path) or "")
        excerpts[path] = excerpt_for(p, par, common)

    xml, n_att = wxr(P, news, contents, excerpts)
    (root / "import").mkdir(exist_ok=True)
    (root / "import" / "vandentempel-content.xml").write_text(xml)
    redirects = ["source,target,regex,code"] + sorted(
        f'{p["old"].split("?")[0].rstrip("/") or "/nl"},{p["new"]},0,301' for p in P.values() if p["old"])
    (root / "import" / "redirects.csv").write_text("\n".join(redirects) + "\n")

    # Static preview of the key pages.
    prev = root / "preview"
    prev.mkdir(exist_ok=True)
    shutil.copytree(root / "wp-content/themes/vandentempel/assets", prev / "theme/assets", dirs_exist_ok=True)
    shutil.copy(Path(__file__).with_name("preview-base.css"), prev / "preview-base.css")
    footer_part = (root / "wp-content/themes/vandentempel/parts/footer.html").read_text()
    names = set(PREVIEW_PAGES) | {n["new"] for n in news}
    if "--preview-all" in sys.argv:
        names = set(P)
    for path in sorted(names):
        if path not in P:
            continue
        p = P[path]
        depth = 0 if path == "/" else path.strip("/").count("/") + 1
        rel = "../" * depth
        html_out = preview_page(P, p, contents[path], excerpts[path], footer_part, rel, names)
        if media:
            def local(m):
                name = media_name(m.group(1))
                return f'src="{rel}media/{name}"' if (media / name).exists() else m.group(0)
            html_out = re.sub(r'src="(https://vandentempel\.nl/[^"]+)"', local, html_out)
        out = prev / (path.strip("/") + "/index.html" if path != "/" else "index.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html_out)
    kinds = {}
    for p in P.values():
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    print("pages", kinds, "attachments", n_att, "preview", len(names))


if __name__ == "__main__":
    main()
