"""Validate the static website and the footer-only local navigation contract."""
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote
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
assert len(documents)==22
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
 expected_noindex=route in {'/404/','/bedankt/afspraak/'} or not config['indexable']
 assert ('noindex' in doc.xpath('//meta[@name="robots"]/@content')[0]) is expected_noindex
 graph=json.loads(doc.xpath('//script[@type="application/ld+json"]')[0].text)['@graph']
 assert any(x['@type']=='HousePainter' and x['address']['addressLocality']=='Oldebroek' for x in graph)
 business=next(x for x in graph if x['@type']=='HousePainter')
 assert business['founder']['@id'].endswith('/over-stef/#stef')
 assert len(business['hasOfferCatalog']['itemListElement'])==7
 assert any(x['@type']=='Person' and x['name']=='Stef van Ommen' for x in graph)
 visible_questions=doc.xpath('//main//details[summary and .//p]')
 faq_nodes=[x for x in graph if x['@type']=='FAQPage']
 assert (len(faq_nodes)==1) is bool(visible_questions), ('FAQ schema',route)
 if visible_questions:assert len(faq_nodes[0]['mainEntity'])==len(visible_questions), ('FAQ count',route)
 ids=doc.xpath('//@id');assert len(ids)==len(set(ids)), ('duplicate IDs',route)
 for slug in ('schilder-oldebroek','schilder-wezep','schilder-zwolle','schilder-elburg','schilder-nunspeet'):
  href='/'+slug+'/'
  assert not doc.xpath('//header//a[@href=$href]',href=href), ('local link in header',route)
  assert doc.xpath('//footer//nav[@aria-label="Snelle links"]//a[@href=$href]',href=href), ('missing footer link',route)
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
assert documents['/'].xpath('//a[@href="/contact/#offerte" and normalize-space(.)="Offerte Aanvragen"]')
assert not documents['/'].xpath('//div[contains(@class,"hero-location")]')
assert not documents['/'].xpath('//section[contains(@class,"hero")]//p[contains(@class,"eyebrow")]')
assert documents['/contact/'].xpath('//form[@id="offerte"]//button[@type="submit" and contains(.,"e-mailprogramma")]')
assert len(documents['/'].xpath('//section[@id="vragen"]//details'))==6
assert len(documents['/contact/'].xpath('//section[@id="vragen"]//details'))==14
assert documents['/contact/'].xpath('//form[@id="offerte"]//a[@id="quote-whatsapp"]')
assert documents['/privacy/'].xpath('//h1[contains(.,"gegevens")]')
assert documents['/websitevoorwaarden/'].xpath('//h1[contains(.,"website")]')
assert documents['/over-stef/'].xpath('//section[contains(@class,"company-facts")]//dd[contains(.,"Stef van Ommen")]')
assert documents['/bedankt/afspraak/'].xpath('//meta[contains(@content,"noindex")]')
assert documents['/404/'].xpath('//meta[contains(@content,"noindex")]')
for route,doc in documents.items():
 assert doc.xpath('//footer//a[@href="/privacy/"]'), ('privacy footer',route)
 assert doc.xpath('//footer//a[@href="/websitevoorwaarden/"]'), ('terms footer',route)
assert 'geen automatische e-mail' in documents['/afspraak/'].get_element_by_id('appointment-success').text_content()
sitemap=etree.parse(str(out/'sitemap.xml'))
urls=sitemap.xpath('//*[local-name()="loc"]/text()')
indexable_routes={r for r,d in documents.items() if 'noindex' not in d.xpath('//meta[@name="robots"]/@content')[0]}
assert set(urls)=={config['origin']+r for r in indexable_routes}
assert 'Sitemap: '+config['origin']+'/sitemap.xml' in (out/'robots.txt').read_text()
assert 'User-agent: OAI-SearchBot\nAllow: /' in (out/'robots.txt').read_text()
assert '/afspraken-beheer/' not in (out/'llms.txt').read_text()
assert all(config['origin']+r in (out/'llms.txt').read_text() for r in indexable_routes)
for fact in ('Stef van Ommen','Bovendwarsweg 78','Oldebroek, Wezep, Zwolle, Elburg en Nunspeet','Binnenschilderwerk','KvK: 95415033'):
 assert fact in (out/'llms.txt').read_text(), ('llms fact',fact)
css=(out/'style.css').read_text();assert css.count('{')==css.count('}')
print(f'Validated {len(documents)} pages: navigation, links, headings, metadata, schema, assets and sitemap.')
