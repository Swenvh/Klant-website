# Polite crawler for vandentempel.nl/nl: saves raw HTML per page.
import sys, os, re, time, hashlib, subprocess, json
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
start = ["/nl/", "/nl/producten", "/nl/service", "/nl/trainingen", "/nl/verhuur",
         "/nl/over-vandentempel", "/nl/contact", "/nl/nieuws", "/nl/colofon", "/nl/privacy-beleid"]
seen, queue, index = set(), list(start), {}
maxpages = int(sys.argv[2]) if len(sys.argv) > 2 else 400
def fetch(path):
    url = "https://vandentempel.nl" + path
    for i in range(4):
        r = subprocess.run(["curl", "-sS", "-m", "30", "-L", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
        time.sleep(2 * (i + 1))
    return None
while queue and len(index) < maxpages:
    p = queue.pop(0)
    p = re.sub(r"https?://(www\.)?vandentempel\.nl", "", p).split("#")[0].replace("&amp;", "&")
    if p in seen or not p.startswith("/nl/") or re.search(r"\.(pdf|jpg|png|zip)$|component/|format=|\?start=|print=|/tag/|\?filter|/documents", p):
        continue
    seen.add(p)
    name = hashlib.md5(p.encode()).hexdigest()[:12] + ".html"
    cached = os.path.join(out, name)
    t = open(cached).read() if os.path.exists(cached) else fetch(p)
    if t is None:
        print("FAIL", p, flush=True); continue
    name = hashlib.md5(p.encode()).hexdigest()[:12] + ".html"
    if not os.path.exists(cached):
        open(cached, "w").write(t)
        time.sleep(0.4)
    index[p] = name
    for l in re.findall(r'href="((?:https?://(?:www\.)?vandentempel\.nl)?/nl/[^"#]*)"', t):
        queue.append(l)
json.dump(index, open(os.path.join(out, "_index.json"), "w"), indent=1)
print("pages", len(index), "queued-left", len(queue))
