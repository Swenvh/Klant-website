"""Create responsive delivery copies; preserve the approved original assets."""
from pathlib import Path
from PIL import Image, ImageOps
import json
from fontTools import subset
from fontTools.ttLib import TTFont

root = Path(__file__).resolve().parents[1]
assets = root / 'dist/assets'
manifest = {}
hero_png = assets / 'van-ommen-bus-hero.png'
if hero_png.exists():
    with Image.open(hero_png) as original:
        social = ImageOps.exif_transpose(original).convert('RGB')
        social.thumbnail((1600, 900), Image.Resampling.LANCZOS)
        social.save(assets / 'van-ommen-og.jpg', 'JPEG', quality=86, optimize=True, progressive=True)
for path in sorted(assets.iterdir()):
    if path.suffix.lower() not in ('.jpg', '.jpeg', '.webp') or '-responsive-' in path.name or path.name.startswith(('logo', 'van-ommen-og')):
        continue
    with Image.open(path) as original:
        image = ImageOps.exif_transpose(original).convert('RGB')
        widths = sorted(set(min(w, image.width) for w in (480, 960, 1440, image.width)))
        variants = []
        for width in widths:
            target = assets / f'{path.stem}-responsive-{width}.webp'
            resized = image.resize((width, round(width * image.height / image.width)), Image.Resampling.LANCZOS)
            if not target.exists() or target.stat().st_mtime < path.stat().st_mtime:
                resized.save(target, 'WEBP', quality=86, method=6)
            variants.append({'src': '/assets/' + target.name, 'width': width})
        manifest['/assets/' + path.name] = {'width': image.width, 'height': image.height, 'variants': variants}
(assets / 'responsive-images.json').write_text(json.dumps(manifest))
print(f'Optimized {len(manifest)} photo assets for responsive delivery.')
for path in assets.glob('poppins-*.ttf'):
    if '-latin' in path.stem:
        continue
    target = path.with_name(path.stem + '-latin.ttf')
    if target.exists() and target.stat().st_mtime >= path.stat().st_mtime:
        continue
    font = TTFont(path)
    options = subset.Options()
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=list(range(0x20, 0x250)) + list(range(0x2000, 0x2070)) + [0x20ac])
    sub.subset(font)
    font.save(target)
print('Subset local fonts for Dutch and Western European text.')
