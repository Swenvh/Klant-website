"""Encode the existing hero for web delivery; preserve size and original file."""
from pathlib import Path
from PIL import Image

assets=Path(__file__).resolve().parents[1]/'dist/assets'
source=assets/'van-ommen-bus-hero.png'
target=assets/'van-ommen-bus-hero.webp'
with Image.open(source) as image:
 image.save(target, 'WEBP', quality=92, method=6)
 with Image.open(target) as result:
  assert result.size==image.size
print(f'Hero WebP: {source.stat().st_size:,} -> {target.stat().st_size:,} bytes; dimensions preserved.')
