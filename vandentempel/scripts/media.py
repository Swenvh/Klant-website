# Download and downsize images referenced by the preview pages.
import sys, re, hashlib, subprocess, time, io
from pathlib import Path
from PIL import Image
prev, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
def media_name(url):
    ext = re.search(r"\.(jpe?g|png|webp|gif|svg)(?:\?|$)", url, re.I)
    return hashlib.md5(url.encode()).hexdigest()[:16] + "." + (ext.group(1).lower() if ext else "jpg")
urls = set()
for f in prev.rglob("index.html"):
    urls |= set(re.findall(r'src="(https://vandentempel\.nl/[^"]+)"', f.read_text()))
ok = 0
for u in sorted(urls):
    dst = out / media_name(u)
    if dst.exists(): ok += 1; continue
    data = None
    for i in range(4):
        r = subprocess.run(["curl", "-sS", "-m", "40", "-L", u], capture_output=True)
        if r.returncode == 0 and r.stdout[:4] not in (b"<!DO", b"<htm"): data = r.stdout; break
        time.sleep(2 * (i + 1))
    if not data: print("FAIL", u); continue
    try:
        im = Image.open(io.BytesIO(data)); im.thumbnail((1600, 1600))
        fmt = "PNG" if dst.suffix == ".png" else "WEBP" if dst.suffix == ".webp" else "JPEG"
        if fmt == "JPEG" and im.mode not in ("RGB", "L"): im = im.convert("RGB")
        im.save(dst, fmt, quality=82)
    except Exception as e:
        dst.write_bytes(data)
    ok += 1
print("images", ok, "/", len(urls))
