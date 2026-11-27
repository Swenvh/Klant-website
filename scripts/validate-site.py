"""Validate the static website and the footer-only local navigation contract."""
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from site_content import LOCATIONS
from lxml import html, etree

root=Path(__file__).resolve().parents[1]
out=root/'dist'
config=json.loads((root/'source/seo-config.json').read_text())
documents={}
for file in sorted(out.rglob('index.html')):
 if file.is_relative_to(out/'client'):continue
 route='/'+str(file.parent.relative_to(out)).strip('.')
 if route!='/':route=route.rstrip('/')+'/'
 documents[route]=html.fromstring(file.read_text())
assert len(documents)==23+len(LOCATIONS)
titles=set()
descriptions=set()
for route,doc in documents.items():
 assert len(doc.xpath('//main//h1'))==1, route
 assert len(doc.xpath('//h1'))==1, route
 previous=0
 for heading in doc.xpath('//main//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]'):
  level=int(heading.tag[1]);assert level<=previous+1, ('heading skip',route,heading.text_content())
  previous=level
 title=doc.find('.//title').text
 assert title not in titles, ('duplicate title', route)
 titles.add(title)
 description=doc.xpath('//meta[@name="description"]/@content')[0]
 assert description and description not in descriptions, ('description', route)
 descriptions.add(description)
 assert doc.xpath('//link[@rel="canonical"]/@href')==[config['origin']+route]
 assert doc.xpath('//meta[@property="og:url"]/@content')==[config['origin']+route]
 social=doc.xpath('//meta[@property="og:image"]/@content')
 assert len(social)==1 and social[0].startswith(config['origin']+'/assets/'), ('og:image',route)
 assert (out/urlsplit(social[0]).path.lstrip('/')).is_file()
 assert doc.xpath('//meta[@name="twitter:card"]/@content')==['summary_large_image']
 expected_noindex=route in {'/404/','/bedankt/offerte/'} or not config['indexable']
 assert ('noindex' in doc.xpath('//meta[@name="robots"]/@content')[0]) is expected_noindex
 graph=json.loads(doc.xpath('//script[@type="application/ld+json"]')[0].text)['@graph']
 assert any(x['@type']=='HousePainter' and x['address']['addressLocality']=='Oldebroek' for x in graph)
 business=next(x for x in graph if x['@type']=='HousePainter')
 assert business['founder']['@id'].endswith('/over-ons/#stef')
 assert len(business['hasOfferCatalog']['itemListElement'])==7
 assert any(x['@type']=='Person' and x['name']=='Stef van Ommen' for x in graph)
 ids=doc.xpath('//@id');assert len(ids)==len(set(ids)), ('duplicate IDs',route)
 for slug in [p['slug'] for p in LOCATIONS]:
  href='/'+slug+'/'
  assert not doc.xpath('//header//a[@href=$href]',href=href), ('local link in header',route)
  assert doc.xpath('//footer//nav[@aria-label="Werkgebied"]//a[@href=$href]',href=href), ('missing footer link',route)
 if route.startswith('/schilder-'):
  expected=route.strip('/').removeprefix('schilder-').capitalize()
  assert any(x['@type']=='Service' and x.get('areaServed',{}).get('name')==expected for x in graph), ('local service schema',route)
 for el in doc.xpath('//a[@href]'):
  url=urlsplit(el.get('href'))
  if url.scheme or url.netloc:continue
  path=url.path or route
  if not path.startswith('/'):continue
  if path not in documents:
   assert (out/path.lstrip('/')).is_file(), ('missing link',route,path)
  elif url.fragment:
   assert documents[path].xpath('//*[@id=$id]',id=unquote(url.fragment)), ('missing anchor',route,path,url.fragment)
 for img in doc.xpath('//img | //*[local-name()="image"]'):
  src=img.get('src') or img.get('href')
  if src and src.startswith('/'):
   assert (out/src.lstrip('/')).is_file(), ('missing image',src)
  if img.tag=='img':assert img.get('alt') is not None, ('missing alt',route)
assert documents['/'].xpath('//a[@href="/offerte/" and normalize-space(.)="Offerte aanvragen"]')
assert not any(doc.xpath('//a[contains(@href,"#offerte")]') for doc in documents.values())
assert documents['/contact/'].xpath('//a[@href="/offerte/"]') and not documents['/contact/'].xpath('//form')
assert not documents['/'].xpath('//div[contains(@class,"hero-location")]')
assert not documents['/'].xpath('//section[contains(@class,"hero")]//p[contains(@class,"eyebrow")]')
assert documents['/offerte/'].xpath('//form[@id="offerte"][@action="/api/offerte"]//button[@type="submit" and contains(.,"Verstuur")]')
assert not documents['/offerte/'].xpath('//form[@id="offerte"]//input[@type="file"]')
assert documents['/bedankt/offerte/'].xpath('//meta[contains(@content,"noindex")]')
assert documents['/offerte/'].xpath('//form[@id="offerte"]//a[@id="quote-whatsapp"]')
assert documents['/privacy/'].xpath('//h1[contains(.,"gegevens")]')
assert documents['/over-ons/'].xpath('//*[contains(@class,"about-copy")]//p[contains(.,"erkend leerbedrijf")]')
assert not documents['/over-ons/'].xpath('//section[contains(@class,"company-facts")]')
assert documents['/404/'].xpath('//meta[contains(@content,"noindex")]')
for route,doc in documents.items():
 assert doc.xpath('//footer//a[@href="/privacy/"]'), ('privacy footer',route)
 assert doc.xpath('//footer//a[@href="/voorwaarden/algemene-voorwaarden-consument.pdf"]') and doc.xpath('//footer//a[@href="/voorwaarden/algemene-voorwaarden-zakelijk.pdf"]'), ('voorwaarden footer',route)
 assert not doc.xpath('//a[contains(@href,"websitevoorwaarden")]'), ('websitevoorwaarden link',route)
sitemap=etree.parse(str(out/'sitemap.xml'))
urls=sitemap.xpath('//*[local-name()="loc"]/text()')
indexable_routes={r for r,d in documents.items() if 'noindex' not in d.xpath('//meta[@name="robots"]/@content')[0]}
assert set(urls)=={config['origin']+r for r in indexable_routes}
assert 'Sitemap: '+config['origin']+'/sitemap.xml' in (out/'robots.txt').read_text()
assert 'User-agent: OAI-SearchBot\nAllow: /' in (out/'robots.txt').read_text()
assert '/afspraken-beheer/' not in (out/'llms.txt').read_text()
assert all(config['origin']+r in (out/'llms.txt').read_text() for r in indexable_routes)
for fact in ('Stef van Ommen','Bovendwarsweg 78','Elburg, Nunspeet, Zwolle, Wezep','Binnenschilderwerk','KvK: 95415033'):
 assert fact in (out/'llms.txt').read_text(), ('llms fact',fact)
css=(out/'style.css').read_text();assert css.count('{')==css.count('}')
print(f'Validated {len(documents)} pages: navigation, links, headings, metadata, schema, assets and sitemap.')
for route,doc in documents.items():
 assert not doc.xpath('//main//details[summary]|//*[@id="vragen"]|//a[contains(@href,"#vragen")]'), ('faq removed',route)
for naam in ['algemene-voorwaarden-consument.pdf','algemene-voorwaarden-zakelijk.pdf']:
 if not (out/'voorwaarden'/naam).exists():print(f'WAARSCHUWING: dist/voorwaarden/{naam} ontbreekt (leg de pdf in source/voorwaarden/).')


# Schrijfstijl: hooguit twee keer "we" per alinea (afspraak 2026-11-24). Waarschuwt, breekt de build niet.
WE_LIMIET=2
import re as _re, glob as _glob
from lxml import html as _lh
_gezien=set()
for _f in sorted(_glob.glob('dist/**/index.html',recursive=True)):
    for _p in _lh.parse(_f).getroot().xpath('//main//p|//main//li'):
        _t=' '.join(_p.text_content().split())
        if _t in _gezien: continue
        _gezien.add(_t)
        _n=len(_re.findall(r"\b[Ww]e\b",_t))
        if _n>WE_LIMIET: print(f'WAARSCHUWING: {_n}x "we" in {_f}: {_t[:90]}')
