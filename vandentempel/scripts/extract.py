"""Extract clean content from the crawled vandentempel.nl/nl pages.

Usage: python3 -I extract.py <crawl-dir> <out.json>

The crawl dir holds one HTML file per page, named md5(path)[:12].html (see
crawl.py). Output is a JSON list of pages with title, kind, cleaned HTML body,
images and the old and new URL paths.
"""

import hashlib
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ORIGIN = "https://vandentempel.nl"
START = ["/nl/", "/nl/producten", "/nl/service", "/nl/trainingen", "/nl/verhuur",
         "/nl/over-vandentempel", "/nl/contact", "/nl/nieuws", "/nl/colofon", "/nl/privacy-beleid"]

ALLOWED = {"p", "h2", "h3", "h4", "ul", "ol", "li", "strong", "b", "em", "i", "a", "img",
           "table", "thead", "tbody", "tr", "th", "td", "br", "sup", "sub", "blockquote"}
RENAME = {"b": "strong", "i": "em", "h1": "h2", "h5": "h3", "h6": "h4"}
BLOCK = {"p", "h2", "h3", "h4", "ul", "ol", "table", "blockquote"}
DROP_WITH_CONTENT = {"script", "style", "noscript", "form", "button", "select", "svg", "iframe", "nav"}


def norm(path):
    path = re.sub(r"https?://(www\.)?vandentempel\.nl", "", path)
    return path.split("#")[0].replace("&amp;", "&")


def new_path(old):
    """Map an old Joomla path to the WordPress permalink."""
    p = old.split("?")[0].rstrip("/")
    if p in ("/nl", ""):
        return "/"
    p = p[len("/nl"):]
    p = p.replace("/item/", "/")
    p = p.replace("/service-apparaten/verhuur", "/verhuur")
    p = re.sub(r"/nieuws/\d+-", "/nieuws/", p)
    return p + "/"


class Cleaner(HTMLParser):
    """Rebuilds HTML keeping only simple semantic tags."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.stack, self.drop = [], [], 0
        self.images = []
        self.lists = []  # per open <ul>/<ol>: "tab", "switch" or "list"

    def handle_starttag(self, tag, attrs):
        tag = RENAME.get(tag, tag)
        cls = dict(attrs).get("class") or ""
        if tag in ("ul", "ol"):
            # UIkit tabs: drop the tab labels, keep the panel contents as plain blocks.
            kind = "tab" if "uk-tab" in cls or "uk-subnav" in cls else "switch" if "uk-switcher" in cls else "list"
            self.lists.append(kind)
            if kind == "tab":
                self.drop += 1
                return
            if kind == "switch":
                return
        if tag == "li" and self.lists and self.lists[-1] == "switch":
            return
        if tag in DROP_WITH_CONTENT:
            self.drop += 1
            return
        if self.drop or tag not in ALLOWED:
            return
        a = dict(attrs)
        if tag == "a":
            href = a.get("href") or ""
            if "/tag/" in href:  # product tags: drop link and text
                self.drop += 1
                self.stack.append("tag")
                return
            if href.startswith("javascript:") or not href:
                self.stack.append(None)
                return
            if href.startswith("/nl/") or re.match(r"https?://(www\.)?vandentempel\.nl/nl/", href):
                href = new_path(norm(href))
            elif href.startswith("/images/") or href.startswith("/media/"):
                href = ORIGIN + href
            self.out.append(f'<a href="{html.escape(href)}">')
            self.stack.append("a")
            return
        if tag == "img":
            src = a.get("src") or a.get("data-src") or ""
            if not src or src.startswith("data:"):
                return
            if src.startswith("/"):
                src = ORIGIN + src
            alt = a.get("alt") or a.get("title") or ""
            self.images.append(src)
            self.out.append(f'<img src="{html.escape(src)}" alt="{html.escape(alt)}">')
            return
        if tag == "br":
            self.out.append("<br>")
            return
        self.out.append(f"<{tag}>")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        tag = RENAME.get(tag, tag)
        if tag == "a" and self.stack and self.stack[-1] == "tag":
            self.stack.pop()
            self.drop = max(0, self.drop - 1)
            return
        if tag in ("ul", "ol") and self.lists:
            kind = self.lists.pop()
            if kind == "tab":
                self.drop = max(0, self.drop - 1)
                return
            if kind == "switch":
                return
        if tag == "li" and self.lists and self.lists[-1] == "switch":
            return
        if tag in DROP_WITH_CONTENT:
            self.drop = max(0, self.drop - 1)
            return
        if self.drop or tag not in ALLOWED or tag in ("img", "br"):
            return
        # Close the nearest matching open tag.
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] == tag or (tag == "a" and self.stack[i] is None):
                closing = self.stack[i:]
                del self.stack[i:]
                for t in reversed(closing):
                    if t and t != "tag":
                        self.out.append(f"</{t}>")
                return

    def handle_data(self, data):
        if not self.drop:
            self.out.append(html.escape(data, quote=False))

    def result(self):
        for t in reversed(self.stack):
            if t and t != "tag":
                self.out.append(f"</{t}>")
        s = "".join(self.out)
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"(<br>\s*){3,}", "<br><br>", s)
        # Loose text between blocks becomes a paragraph.
        # Drop empty elements, repeatedly (an empty link leaves an empty item behind).
        prev = None
        while prev != s:
            prev = s
            s = re.sub(r"<(p|h2|h3|h4|li|td|th|strong|em|ul|ol)>\s*(<br>\s*)*</\1>", "", s)
            s = re.sub(r'<a href="[^"]*">\s*</a>', "", s)
        return s.strip()


def wrap_loose_text(s):
    """Put text that sits outside block tags into paragraphs."""
    parts = re.split(r"(</?(?:p|h2|h3|h4|ul|ol|table|blockquote)>)", s)
    out, depth = [], 0
    for part in parts:
        m = re.match(r"<(/?)(p|h2|h3|h4|ul|ol|table|blockquote)>", part)
        if m:
            depth += -1 if m.group(1) else 1
            out.append(part)
        elif depth == 0 and re.sub(r"<[^>]+>|\s|&nbsp;", "", part):
            out.append(f"<p>{part.strip()}</p>")
        elif depth > 0:
            out.append(part)
    s = "".join(out)
    s = re.sub(r"<p>\s*(<br>\s*)+", "<p>", s)
    s = re.sub(r"(\s*<br>)+\s*</p>", "</p>", s)
    s = re.sub(r"<p>\s*</p>", "", s)
    return s


def clean(fragment):
    c = Cleaner()
    c.feed(fragment)
    return wrap_loose_text(c.result()), c.images


def main_fragment(page):
    body = page[page.find("<body"):]
    end = body.find("<!-- Builder #module-386")
    if end < 0:
        end = len(body)
    start = body.find('id="tm-main"')
    if start >= 0:
        start = body.find(">", start) + 1
    if start <= 0 or start > end:
        # Builder pages: content starts after the header/navigation.
        start = body.find("</header>")
        nxt = body.find("<!-- Builder #", start)
        if 0 <= nxt < end:
            start = nxt
    return body[start:end]


def teasers(fragment):
    """Map child link -> teaser text from a ZOO category listing."""
    out = {}
    pat = r'(?s)<h[23][^>]*>\s*<a href="([^"]+)"[^>]*>(.*?)</a>\s*</h[23]>(.*?)(?=<h[23][^>]*>\s*<a href=|<div class="uk-width|</div>\s*</div>\s*<hr|$)'
    for href, _title, rest in re.findall(pat, fragment):
        txt = html.unescape(re.sub(r"<[^>]+>|\s+", " ", rest)).strip()
        if txt:
            out[norm(href)] = txt[:300]
    return out


def intro_only(fragment):
    """Text before the first child listing on a category page."""
    m = re.search(r'<div class="uk-grid|<div class="items|<div class="uk-child-width|<h[23][^>]*>\s*<a href=', fragment)
    return fragment[: m.start()] if m else fragment


def first_h1(fragment):
    m = re.search(r"(?s)<h1[^>]*>(.*?)</h1>", fragment)
    return html.unescape(re.sub(r"<[^>]+>|\s+", " ", m.group(1))).strip() if m else ""


def main():
    crawl, out = Path(sys.argv[1]), Path(sys.argv[2])
    files = {f.name: f for f in crawl.glob("*.html")}
    paths = set(START)
    for f in files.values():
        for link in re.findall(r'href="((?:https?://(?:www\.)?vandentempel\.nl)?/nl/[^"#]*)"', f.read_text(errors="replace")):
            paths.add(norm(link))
    by_name = {hashlib.md5(p.encode()).hexdigest()[:12] + ".html": p for p in paths}

    pages = []
    for name, f in sorted(files.items()):
        old = by_name.get(name)
        if not old:
            continue
        raw = f.read_text(errors="replace")
        tm = re.search(r"(?s)<title>(.*?)</title>", raw)
        if not tm:  # error or redirect body, not a real page
            continue
        frag = main_fragment(raw)
        title = first_h1(frag) or html.unescape(tm.group(1)).split(" - ")[0].strip()
        frag = re.sub(r"(?s)<h1[^>]*>.*?</h1>", "", frag, count=1)
        frag = re.sub(r'(?s)<div class="uk-margin element element-itemprevnext">.*?</ul>\s*</div>', "", frag)
        kind = "product" if "/item/" in old else "news" if re.match(r"/nl/nieuws/\d+-", old) else "page"
        tz = teasers(frag) if kind == "page" else {}
        listing = bool(tz) or "/item/" in frag
        body, images = clean(intro_only(frag) if kind == "page" and listing else frag)
        _, all_images = clean(frag)
        body = body.replace("<p>Uitgebreide beschrijving</p>", "<h2>Uitgebreide beschrijving</h2>")
        date = None
        m = re.search(r"(?:datetime|published_time|datePublished|dateCreated)[^0-9]{0,12}(\d{4}-\d{2}-\d{2})", raw)
        if m and kind == "news":
            date = m.group(1)
        meta = re.search(r'<meta name="description" content="([^"]*)"', raw)
        pages.append({
            "old": old,
            "new": new_path(old),
            "kind": kind,
            "title": title,
            "teasers": {new_path(k): v for k, v in tz.items()},
            "date": date,
            "description": html.unescape(meta.group(1)).strip() if meta else "",
            "body": body,
            "images": list(dict.fromkeys(images or all_images)),
        })
    out.write_text(json.dumps(pages, ensure_ascii=False, indent=1))
    kinds = {}
    for p in pages:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    print(len(pages), "pages", kinds)


if __name__ == "__main__":
    main()
