from pathlib import Path
from lxml import html
from copy import deepcopy
from urllib.parse import quote
from html import escape
import json
from site_content import SERVICE_COPY, LOCATIONS, HOME_INTRO
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
SEO=json.loads((ROOT/'source/seo-config.json').read_text())
ORIGIN=SEO['origin'].rstrip('/')
ROUTES=[]
# Algemene voorwaarden als pdf: leg de bestanden in source/voorwaarden/, de build kopieert ze naar dist/voorwaarden/.
VOORWAARDEN={'consument':'/voorwaarden/algemene-voorwaarden-consument.pdf','zakelijk':'/voorwaarden/algemene-voorwaarden-zakelijk.pdf'}
PUBLIC_ROUTES=[]
LLMS_PAGES=[]  # (route, titel, omschrijving) voor llms.txt
UPDATED=date.today().isoformat()  # lastmod in de sitemap: datum van de build
IMAGE_MAP=json.loads((OUT/'assets/responsive-images.json').read_text())
assert ORIGIN.startswith('https://'), 'The canonical origin must use HTTPS'
def brand_art(identifier):
 # High-resolution restoration, cached once across routes. The viewport removes
 # blank margins; the filter keeps the approved transparent monochrome treatment.
 return f'''<svg class="brand-lockup" xmlns="http://www.w3.org/2000/svg" viewBox="213 92 1749 572" width="277" height="100" aria-hidden="true" focusable="false"><defs><filter id="{identifier}" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -.2126 -.7152 -.0722 0 1"/></filter></defs><image href="/assets/logo-hd.webp" x="0" y="0" width="2172" height="724" filter="url(#{identifier})"/></svg>'''
import hashlib
ASSET_VERSION={name:hashlib.md5((OUT/name).read_bytes()).hexdigest()[:8] for name in ('style.css','app.js')}
base=html.fromstring((ROOT/'source/site-template.html').read_text())
for el in base.xpath('//a[contains(@class,"social-linkedin")]'):
 if SEO.get('linkedin_url'):el.set('href',SEO['linkedin_url'])
 else:el.getparent().remove(el)
for el in base.xpath('//a[@class="leerbedrijf"]'):
 if SEO.get('sbb_url'):el.set('href',SEO['sbb_url'])
 else:el.getparent().remove(el)
for el in base.xpath('//link[@href="/style.css"]'):el.set('href','/style.css?v='+ASSET_VERSION['style.css'])
for el in base.xpath('//script[@src="/app.js"]'):el.set('src','/app.js?v='+ASSET_VERSION['app.js'])
for image in base.xpath('//img[@src="/assets/van-ommen-bus-hero.png"]'):
 image.set('src','/assets/van-ommen-bus-hero.webp')
def cls(n,root=base):return root.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," '+n+' ")]')
def serial(el):return html.tostring(el,encoding='unicode',method='html')
def section(id):return deepcopy(base.get_element_by_id(id))
def insert_content(el,markup):
 for c in list(el):el.remove(c)
 el.text=None
 for c in html.fragments_fromstring(markup):
  if isinstance(c,str):el.text=c
  else:el.append(c)
services=[]
slugs=['binnenschilderwerk','buitenschilderwerk','houtrotreparatie','onderhoud-renovatie','spuitwerk','zakelijk-vve','behangwerk']
# Volgorde in menu, dienstenpagina, zijbalk en voettekst (wens opdrachtgever 2026-11-23): binnen, buiten, zakelijk & VvE, onderhoud & renovatie, daarna de rest.
ORDER=['binnenschilderwerk','buitenschilderwerk','zakelijk-vve','onderhoud-renovatie','houtrotreparatie','spuitwerk','behangwerk']
for i,el in enumerate(cls('service')):
 services.append({'name':el.find('.//h3').text,'slug':slugs[i],'text':cls('service-content',el)[0].find('p').text,'tags':[e.text for e in cls('service-tags',el)[0]],'image':['binnenschilderwerk-gele-kamer.jpg','buitenschilderwerk-rietgedekt.jpg','onderhoud-houtrot-plamuren.jpg','woning-gevel-hoek-na.jpg','spuitwerk-trap.jpg','zakelijk-stalen-pui.jpg','behangwerk-kantoor.jpg'][i]})
services.sort(key=lambda v:ORDER.index(v['slug']))
nav=[('/', 'Home'),('/diensten/','Diensten'),('/projecten/','Projecten'),('/over-ons/','Over ons'),('/contact/','Contact')]
linkmap={'#home':'/','#diensten':'/diensten/','#projecten':'/projecten/','#over':'/over-ons/','#werkwijze':'/over-ons/#werkwijze','#contact':'/contact/','#offerte':'/offerte/'}
def service_url(v):return '/diensten/'+v['slug']+'/'
def comparison(kind='interior'):
 filename='before-after-exterior.html' if kind=='exterior' else 'before-after.html'
 return (ROOT/'source'/filename).read_text()

def cta(title='Uw schilderplannen bespreken?'):
 return f'''<section class="page-cta section-pad"><div><p class="eyebrow">PERSOONLIJK CONTACT</p><h2>{title}</h2><p>Vertel Stef wat u wilt laten schilderen. Samen bespreken we de volgende stap.</p></div><div class="cta-actions"><a class="button" href="/offerte/">Offerte aanvragen</a><a class="text-link" href="tel:+31624996700">Liever bellen? 06 24 99 67 00</a></div></section>'''
def intro(label,title,desc,parent=None):
 parent_link=(f'<span aria-hidden="true">/</span><a href="/projecten/">Projecten</a>' if parent=='projecten' else f'<span aria-hidden="true">/</span><a href="/diensten/">Diensten</a>') if parent else ''
 return f'''<section class="page-intro section-pad"><nav class="breadcrumbs" aria-label="Kruimelpad"><a href="/">Home</a>{parent_link}<span aria-hidden="true">/</span><span aria-current="page">{escape(label)}</span></nav><div class="page-intro-content"><div><p class="eyebrow">VAN OMMEN SCHILDERWERKEN</p><h1>{title}</h1></div><p>{desc}</p></div></section>'''
def cards(compact=False):
 result=[]
 # De homepage toont vier fototegels (volgorde: wens opdrachtgever); de overige staan eronder als tekstlinks.
 HOME_TILES=['binnenschilderwerk','buitenschilderwerk','zakelijk-vve','onderhoud-renovatie']
 shown=sorted([v for v in services if v['slug'] in HOME_TILES],key=lambda v:HOME_TILES.index(v['slug'])) if compact else services
 for i,v in enumerate(shown):
  image=f'<img src="/assets/{v["image"]}" alt="{escape(v["name"])} van Van Ommen Schilderwerken" width="800" height="900" loading="lazy">' if v['image'] else ''
  result.append(f'''<a class="service-tile {'has-photo' if image else 'text-tile'}" href="{service_url(v)}"><div class="tile-media">{image}<span class="tile-number">0{i+1}</span><h3>{escape(v['name'])}</h3></div><div class="tile-body">{'' if compact else '<p>'+escape(v['text'])+'</p>'}<span class="tile-link">{'Meer weten over ' if compact else 'Meer over '}{escape(v['name'][0].lower()+v['name'][1:])}</span></div></a>''')
 more=''
 if compact:
  extra=[v for v in services if v['slug'] not in HOME_TILES]
  links=[f'<a href="{service_url(v)}">{escape(v["name"][0].lower()+v["name"][1:])}</a>' for v in extra]
  more='<p class="service-more">Ook voor '+', '.join(links[:-1])+' en '+links[-1]+'.</p>'
 return '<div class="service-tiles '+('compact' if compact else '')+'">'+''.join(result)+'</div>'+more
def render(route,title,desc,content,active,home=False,gallery=False,private=False,indexable=True):
 s=deepcopy(base);body=s.find('body');body.set('class','page-home' if home else 'page-inner page-'+active.strip('/').replace('/','-'))
 s.find('.//title').text=('Van Ommen Schilderwerken | '+title) if route=='/' else title+' | Van Ommen Schilderwerken'
 s.xpath('//meta[@name="description"]')[0].set('content',desc)
 head=s.find('head')
 head.append(html.Element('meta',name='author',content='Van Ommen Schilderwerken'))
 head.append(html.Element('link',rel='preload',attrib={'as':'font','type':'font/ttf','href':'/assets/poppins-400-latin.ttf','crossorigin':'anonymous'}))
 head.append(html.Element('link',rel='preload',attrib={'as':'font','type':'font/ttf','href':'/assets/ebgaramond-500-latin.ttf','crossorigin':'anonymous'}))
 canonical=html.Element('link',rel='canonical',href=ORIGIN+route);head.append(canonical)
 social_image=ORIGIN+'/assets/van-ommen-og.jpg'
 for name,value in [('robots','index, follow, max-image-preview:large' if SEO['indexable'] and indexable and not private else 'noindex, nofollow'),('twitter:card','summary_large_image'),('twitter:image',social_image),('twitter:image:alt','Bedrijfsbus van Van Ommen Schilderwerken'),('twitter:title',title+' | Van Ommen Schilderwerken'),('twitter:description',desc)]:
  head.append(html.Element('meta',name=name,content=value))
 for name,value in [('og:type','website'),('og:locale','nl_NL'),('og:site_name','Van Ommen Schilderwerken'),('og:title',s.find('.//title').text),('og:description',desc),('og:url',ORIGIN+route)]:
  head.append(html.Element('meta',property=name,content=value))
 for name,value in [('og:image',social_image),('og:image:secure_url',social_image),('og:image:type','image/jpeg'),('og:image:width','1600'),('og:image:height','900'),('og:image:alt','Bedrijfsbus van Van Ommen Schilderwerken')]:
  head.append(html.Element('meta',property=name,content=value))
 if SEO.get('google_site_verification'):
  head.append(html.Element('meta',name='google-site-verification',content=SEO['google_site_verification']))
 insert_content(s.get_element_by_id('main'),content)
 if route=='/contact/' and SEO.get('turnstile_site_key'):
  head.append(html.fromstring('<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>'))
  slot=s.xpath('//form[@id="offerte"]//div[@class="turnstile-slot"]')[0];slot.set('class','cf-turnstile');slot.set('data-sitekey',SEO['turnstile_site_key']);slot.set('data-language','nl');slot.set('data-theme','light')
 if route=='/diensten/':
  for heading in cls('service-tile',s):
   heading.find('.//h3').tag='h2'
 if route.startswith('/diensten/') and route!='/diensten/' and cls('service-article',s):
  article=cls('service-article',s)[0]
  article.append(html.fromstring('<p>Bekijk ook <a href="/projecten/">onze afgeronde schilderprojecten</a>.</p>'))
 privacy=s.get_element_by_id('privacy-dialog')
 privacy.find('p').text='Het offerteformulier op de contactpagina stuurt uw gegevens naar Van Ommen Schilderwerken. De aanvraag wordt op de website bewaard om uw vraag te behandelen. U ontvangt een bevestiging op het ingevulde e-mailadres. Als u via WhatsApp contact opneemt, verstuurt u uw bericht daar.'
 privacy.append(html.fromstring('<p>De website gebruikt geen analyse- of advertentiecookies. Alleen anonieme totaaltellingen per pagina en actie worden bewaard, zonder IP-adres, gebruikersprofiel of unieke bezoeker.</p>'))
 for i,brand in enumerate(cls('brand',s)):
  insert_content(brand,brand_art(f'brand-ink-{i}'))
  brand.set('class',brand.get('class')+' brand-integrated')
 for nav_class in ['desktop-nav','mobile-nav']:
  n=cls(nav_class,s)[0]
  def navlink(url,label):
   current=' aria-current="page"' if url==active or (active.startswith('/diensten/') and url=='/diensten/') else ''
   if url!='/diensten/':return f'<a href="{url}"{current}>{label}</a>'
   # Uitklapbaar dienstenmenu; de link zelf blijft naar het overzicht gaan.
   kind=nav_class.split('-')[0]
   items=''.join(f'<a href="{service_url(v)}"'+(' aria-current="page"' if route==service_url(v) else '')+f'>{escape(v["name"])}</a>' for v in services)
   return (f'<div class="nav-dropdown"><a href="{url}"{current}>{label}</a>'
    f'<button type="button" class="nav-dropdown-toggle" aria-expanded="false" aria-controls="diensten-{kind}"><span class="visually-hidden">Toon alle diensten</span>'
    '<svg viewBox="0 0 12 12" width="14" height="14" aria-hidden="true" focusable="false"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
    f'<div class="nav-dropdown-panel" id="diensten-{kind}"><div class="nav-dropdown-list">{items}<a class="nav-dropdown-all" href="{url}">Alle diensten bekijken</a></div></div></div>')
  links=''.join(navlink(url,label) for url,label in nav)
  if nav_class=='mobile-nav':links+='<a href="tel:+31624996700">Bel Stef: 06 24 99 67 00</a>'
  insert_content(n,links)
 toggle=cls('menu-toggle',s)[0]
 menu_label=html.Element('b',attrib={'class':'menu-label'});menu_label.text='Menu';toggle.insert(0,menu_label)
 for a in s.xpath('//a[@href]'):
  href=a.get('href')
  if href in linkmap:a.set('href',linkmap[href])
  if a.get('data-service'):
   a.set('href','/offerte/?dienst='+quote(a.get('data-service')))
  if 'brand' in a.get('class',''):a.set('aria-label','Van Ommen Schilderwerken, naar de homepage')
 # Keep the scroll-to-top action local on every page.
 for a in cls('footer-bottom',s)[0].findall('a'):a.set('href','#home')
 footer=cls('footer',s)[0]
 footer.insert(1,html.fromstring('<div class="footer-columns"><div class="footer-over"><h2>Van Ommen Schilderwerken</h2><p>Het schildersbedrijf van Stef van Ommen in Oldebroek. Binnen- en buitenschilderwerk, houtrotreparatie, onderhoud en renovatie, spuitwerk en behangwerk, voor woningen en bedrijfspanden in Elburg, Nunspeet, Zwolle, Wezep en Oldebroek.</p></div><nav aria-label="Werkgebied"><h2>Werkgebied</h2>'+''.join(f'<a href="/{place["slug"]}/">Schilder {place["name"]}</a>' for place in LOCATIONS)+'</nav><nav aria-label="Diensten"><h2>Diensten</h2>'+''.join(f'<a href="{service_url(v)}">{escape(v["name"])}</a>' for v in services)+'</nav><div class="footer-contact"><h2>Neem contact op</h2><a class="footer-offerte" href="/offerte/">Offerte aanvragen</a><a href="tel:+31624996700">06 24 99 67 00</a><a href="mailto:info@vanommenschilderwerken.nl">info@vanommenschilderwerken.nl</a><address>Bovendwarsweg 78<br>8096 PR Oldebroek</address>'+('<a class="footer-review" href="'+SEO['review_url']+'" target="_blank" rel="noopener noreferrer">Beoordeel ons op Google</a>' if SEO.get('review_url') else '')+'</div></div>'))
 privacy_button=footer.xpath('.//*[@data-privacy]')
 if privacy_button:
  privacy_button[0].tag='a';privacy_button[0].text='Privacy';privacy_button[0].set('href','/privacy/');privacy_button[0].attrib.pop('data-privacy',None)
 footer_bottom=cls('footer-bottom',s)[0]
 footer_bottom.append(html.fromstring('<a href="'+VOORWAARDEN['consument']+'" type="application/pdf">Algemene voorwaarden consument</a>'))
 footer_bottom.append(html.fromstring('<a href="'+VOORWAARDEN['zakelijk']+'" type="application/pdf">Algemene voorwaarden zakelijk</a>'))
 footer_bottom.append(html.fromstring('<a href="/sitemap/">Sitemap</a>'))
 person={'@type':'Person','@id':ORIGIN+'/over-ons/#stef','name':'Stef van Ommen','jobTitle':'Eigenaar en schilder','url':ORIGIN+'/over-ons/','worksFor':{'@id':ORIGIN+'/#bedrijf'},'sameAs':[u for u in ['https://www.facebook.com/61586685635291','https://www.instagram.com/vanommenschilderwerken/',SEO.get('linkedin_url')] if u]}
 offer_catalog={'@type':'OfferCatalog','name':'Schilderdiensten voor woningen','itemListElement':[{'@type':'Offer','itemOffered':{'@type':'Service','name':v['name'],'url':ORIGIN+service_url(v)}} for v in services]}
 business={'@type':'HousePainter','@id':ORIGIN+'/#bedrijf','identifier':{'@type':'PropertyValue','propertyID':'KvK','value':'95415033'},'name':'Van Ommen Schilderwerken','geo':{'@type':'GeoCoordinates','latitude':52.4252788,'longitude':5.9121044},'hasMap':'https://www.google.com/maps/search/?api=1&query=Bovendwarsweg+78%2C+8096+PR+Oldebroek','description':'Schildersbedrijf uit Oldebroek voor binnen- en buitenschilderwerk, spuitwerk, behangwerk, houtrotreparatie, onderhoud en renovatie. Voor woningen, bedrijfspanden en VvE’s, ook met een onderhoudsplan.','url':ORIGIN+'/','telephone':'+31624996700','email':'info@vanommenschilderwerken.nl','logo':ORIGIN+'/assets/logo-hd.webp','image':ORIGIN+'/assets/buitenschilderwerk-na.jpeg','founder':{'@id':person['@id']},'contactPoint':{'@type':'ContactPoint','contactType':'customer service','telephone':'+31624996700','email':'info@vanommenschilderwerken.nl','availableLanguage':'nl'},'hasOfferCatalog':offer_catalog,'address':{'@type':'PostalAddress','streetAddress':'Bovendwarsweg 78','postalCode':'8096 PR','addressLocality':'Oldebroek','addressCountry':'NL'},'openingHoursSpecification':[{'@type':'OpeningHoursSpecification','dayOfWeek':['Monday','Tuesday','Wednesday','Thursday','Friday'],'opens':'08:00','closes':'17:00'},{'@type':'OpeningHoursSpecification','dayOfWeek':'Saturday','opens':'08:00','closes':'12:00'}],'areaServed':[{'@type':'City','name':p['name']} for p in LOCATIONS],'sameAs':[u for u in ['https://www.instagram.com/vanommenschilderwerken/','https://www.facebook.com/61586685635291/',SEO.get('linkedin_url'),SEO.get('sbb_url')] if u]}
 webpage={'@type':'WebPage','@id':ORIGIN+route+'#pagina','url':ORIGIN+route,'name':title,'description':desc,'inLanguage':'nl-NL','dateModified':UPDATED,'isPartOf':{'@id':ORIGIN+'/#website'},'about':{'@id':ORIGIN+'/#bedrijf'}}
 graph=[business,person,{'@type':'WebSite','@id':ORIGIN+'/#website','url':ORIGIN+'/','name':'Van Ommen Schilderwerken','inLanguage':'nl-NL','publisher':{'@id':ORIGIN+'/#bedrijf'}},webpage]
 crumbs=cls('breadcrumbs',s)
 if crumbs:
  items=[]
  for el in crumbs[0].xpath('./a | ./span[@aria-current="page"]'):
   items.append({'@type':'ListItem','position':len(items)+1,'name':el.text_content(),'item':ORIGIN+(el.get('href') or route)})
  graph.append({'@type':'BreadcrumbList','itemListElement':items})
 if route.startswith('/diensten/') and route!='/diensten/':
  service_name=next(x['name'] for x in services if service_url(x)==route)
  graph.append({'@type':'Service','@id':ORIGIN+route+'#dienst','name':service_name,'serviceType':service_name,'description':desc,'url':ORIGIN+route,'provider':{'@id':ORIGIN+'/#bedrijf'},'areaServed':business['areaServed']})
 place=next((p for p in LOCATIONS if route=='/'+p['slug']+'/'),None)
 if place:
  graph.append({'@type':'Service','@id':ORIGIN+route+'#dienst','name':'Schilderwerk in '+place['name'],'serviceType':'Binnen- en buitenschilderwerk','url':ORIGIN+route,'provider':{'@id':ORIGIN+'/#bedrijf'},'areaServed':{'@type':'City','name':place['name']}})
 schema=html.Element('script',type='application/ld+json');schema.text=json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('<','\\u003c');head.append(schema)
 for img in s.xpath('//img'):
  if img.get('fetchpriority')!='high':img.set('decoding','async')
  info=IMAGE_MAP.get(img.get('src'))
  if info:
   img.set('width',str(info['width']));img.set('height',str(info['height']))
   # The modal script changes its image dynamically; don't pin a stale srcset.
   if img.get('id')!='photo-image':
    img.set('srcset',', '.join(f'{v["src"]} {v["width"]}w' for v in info['variants']))
    img.set('sizes','100vw' if img.get('fetchpriority')=='high' else '(max-width: 700px) 100vw, 50vw')
    img.set('src',[v for v in info['variants'] if v['width']<=1920][-1]['src'])
 if not gallery:
  dialog=s.get_element_by_id('photo-dialog');dialog.getparent().remove(dialog)
 destination=OUT/'.openai/admin-page.html' if private else OUT/route.strip('/')/'index.html' if route!='/' else OUT/'index.html'
 destination.parent.mkdir(parents=True,exist_ok=True)
 destination.write_text('<!doctype html>\n'+serial(s))
 if not private:
  PUBLIC_ROUTES.append(route)
  if indexable:ROUTES.append(route);LLMS_PAGES.append((route,title,desc))

hero_element=deepcopy(cls('hero')[0])
hero_element.xpath('.//div[@class="hero-content"]/p[not(@class)]')[0].text='Geef uw woning een frisse uitstraling. Kwalitatief schilderwerk, binnen en buiten.'
for br in hero_element.xpath('.//div[@class="hero-content"]/p[not(@class)]/br'):
 br.getparent().remove(br)
hero=serial(hero_element)
featured='''<section class="projecten-balk section-pad" aria-labelledby="projecten-balk-title"><div><p class="eyebrow">WIE U VOOR GINGEN</p><h2 id="projecten-balk-title">Projecten</h2></div><a class="text-link" href="/projecten/">Bekijk alle afgeronde projecten</a></section>'''

def werkgebied():
 link=lambda p:f'<a href="/{p["slug"]}/">{escape(p["name"])}</a>'
 lijst=lambda items:', '.join(items[:-1])+' en '+items[-1] if len(items)>1 else ''.join(items)
 plaatsen=lijst([link(p) for p in LOCATIONS[:5]])
 overige=lijst([link(p) for p in LOCATIONS[5:]])
 eromheen=(', en in de plaatsen eromheen, zoals '+overige) if overige else ''
 return f'<section class="werkgebied section-pad section-space" aria-labelledby="werkgebied-title"><div class="section-heading"><div><p class="eyebrow">WERKGEBIED</p><h2 id="werkgebied-title">Waar komt u ons tegen?</h2></div></div><div class="werkgebied-grid"><div class="werkgebied-inhoud"><p class="werkgebied-tekst">Van Ommen Schilderwerken werkt vanuit Oldebroek, aan de noordrand van de Veluwe. Stef komt bij u langs in {plaatsen}{eromheen}. Woont u net buiten dit gebied? Bel even, dan hoort u direct of het past.</p><p class="werkgebied-tel"><span>T.</span><a href="tel:+31624996700">06 24 99 67 00</a></p><a class="text-link" href="/over-ons/">Meer over ons</a></div><figure class="werkgebied-beeld"><img src="/assets/behangwerk-aan-het-werk.jpg" alt="Schilder van Van Ommen Schilderwerken brengt behang met citroenmotief aan op een wand" width="1086" height="1448" loading="lazy"></figure></div></section>'
home=hero+'''<section class="home-services section-pad"><div class="section-heading"><div><p class="eyebrow">WAAR KUNNEN WE U MEE HELPEN?</p><h2>Onze diensten</h2></div><a class="text-link" href="/diensten/">Bekijk alle diensten</a></div>'''+cards(True)+'</section>'+HOME_INTRO+werkgebied()+featured+serial(section('werkwijze'))+cta()
render('/','Schilder in Oldebroek en omgeving','Schildersbedrijf van Stef van Ommen in Oldebroek: binnen- en buitenschilderwerk, houtrotreparatie, spuitwerk en behangwerk in Elburg, Nunspeet en Zwolle.',home,'/',home=True)
content=intro('Diensten','Schilderwerk dat<br>bij uw woning past.','Binnen of buiten, nieuw schilderwerk of onderhoud: kies de werkzaamheden waar u meer over wilt weten.')+'<section class="services-overview section-pad">'+cards()+'</section>'+cta()
render('/diensten/','Schilderdiensten in Oldebroek en omgeving','Binnen- en buitenschilderwerk, houtrotreparatie, spuitwerk, behangwerk, onderhoud en renovatie. Ontdek de diensten van Van Ommen Schilderwerken.',content,'/diensten/')
# Titel en meta description per dienst: zoekwoord + regio vooraan, merknaam achteraan.
SEO_DIENST={
 'binnenschilderwerk':('Binnenschilderwerk Oldebroek, Elburg en Zwolle','Schilder voor binnenschilderwerk in Oldebroek, Elburg, Nunspeet en Zwolle: muren, plafonds, deuren, kozijnen en trappen strak geschilderd. Gratis offerte.'),
 'buitenschilderwerk':('Buitenschilderwerk Oldebroek, Elburg en Zwolle','Schilder voor buitenschilderwerk in Oldebroek, Elburg, Nunspeet en Zwolle: kozijnen, deuren en gevelhout beschermd tegen weer en wind. Gratis offerte.'),
 'houtrotreparatie':('Houtrotreparatie Oldebroek, Elburg en Zwolle','Houtrot in kozijnen of deuren? Van Ommen Schilderwerken herstelt het hout en schildert het opnieuw, in Oldebroek, Elburg, Nunspeet, Zwolle en Wezep.'),
 'onderhoud-renovatie':('Schilderwerk onderhoud en renovatie Oldebroek','Periodiek onderhoud van uw schilderwerk en schilderwerk bij renovatie, voor woningen en bedrijfspanden in Oldebroek, Elburg, Nunspeet, Zwolle en Wezep.'),
 'spuitwerk':('Spuitwerk deuren, kozijnen en keukens Oldebroek','Spuitwerk zonder kwaststrepen voor deuren, kozijnen, trappen en keukenfronten, in Oldebroek, Elburg, Nunspeet, Zwolle en Wezep. Gratis offerte.'),
 'behangwerk':('Behangwerk Oldebroek, Elburg en Zwolle','Behanger en schilder in één: oud behang verwijderen, wanden glad maken en nieuw behang of fotobehang aanbrengen, in Oldebroek, Elburg, Nunspeet en Zwolle.'),
 'zakelijk-vve':('Zakelijk schilderwerk en onderhoudsplan VvE Oldebroek','Schilder voor bedrijfspanden en VvE’s in Oldebroek, Elburg, Nunspeet en Zwolle, met een onderhoudsplan zodat u weet welk schilderwerk wanneer nodig is.'),
}
# Dienstpagina's met fotohero en afwisselende foto- en tekstbanden (wens opdrachtgever 2026-11-23). Alleen bevestigde sterke punten; geen ervaringsjaren of certificaten verzinnen.
STERKE_PUNTEN=['Erkend leerbedrijf (SBB)','Gratis & vrijblijvende offerte','Eén aanspreekpunt van offerte tot oplevering','Voor woningen, bedrijfspanden en VvE’s','Onderhoudsplan voor bedrijfspanden en VvE’s','Werkgebied Noord-Veluwe en regio Zwolle']
# Pas toevoegen als Stef het bevestigt (getal of lidmaatschap invullen), daarna in STERKE_PUNTEN zetten:
#  'Ruim ... jaar ervaring' / 'Sinds ...'
#  '... jaar garantie op het schilderwerk'
#  'Verzekerd voor bedrijfsaansprakelijkheid'
#  'Lid van OnderhoudNL'
#  'Beoordeeld met ... op Google'
SERVICE_LAYOUT={
 'binnenschilderwerk':{
  'hero':('binnenschilderwerk-gele-kamer.jpg','Doorkijk naar een net geschilderde gele kamer met wit plafond'),
  'eyebrow':'BINNENSCHILDERWERK','kop':'Binnenschilderwerk in Oldebroek en omgeving',
  'intro':['Muren die dof zijn geworden, een plafond met vlekken, deuren en kozijnen waar de lak van afbrokkelt. Binnen slijt schilderwerk langzaam, en u ziet het pas als u er goed naar kijkt. Van Ommen Schilderwerken uit Oldebroek schildert het binnenwerk van woningen en bedrijfspanden, van één kamer tot een heel huis.','Stef komt vrijblijvend langs, bekijkt wat er nodig is en maakt een offerte. Bel 06 24 99 67 00 of vraag online een offerte aan.'],
  'banden':[
   {'foto':('binnenschilderwerk-muren-plafonds.jpg','Strak wit geschilderde wanden en plafond met zwarte hoogglans deur en plinten in een woonkeuken'),'kant':'links','eyebrow':'WAT VALT ERONDER','kop':'Wat schilderen we binnen?','tekst':['<ul><li>Muren en plafonds, in latex of een afwasbare muurverf</li><li>Deuren, kozijnen en plinten, in lak</li><li>Trappen, leuningen en balustrades</li><li>Radiatoren en buizen</li><li>Nieuw stucwerk voorbehandelen en sauzen</li></ul>','Stef bekijkt eerst de ondergrond. Losse verf, gaatjes, scheurtjes en oude naden worden bijgewerkt, want verf hecht alleen op een gladde, schone ondergrond. Dan kiest u de kleur en de glansgraad: mat voor de woonkamer en slaapkamers, afwasbaar voor de keuken, de hal en de badkamer. Daarna volgen minimaal twee lagen verf en loopt Stef het werk met u na.'],'donker':{'label':'ZO MIN MOGELIJK OVERLAST','tekst':'Vooraf spreekt u met Stef af welke meubels u verplaatst en wat afgedekt wordt. Vloeren, trappen en meubels gaan onder folie en aan het eind van elke werkdag is de ruimte opgeruimd. Waar het kan gaat het werk kamer voor kamer, zodat u gewoon thuis kunt blijven. De winter is binnen een goede tijd om te schilderen: de verwarming staat aan, de verf droogt goed en u heeft het in het voorjaar klaar.'}},
   {'foto':('hero.jpg','Glanzend wit geschilderd plafond met weerspiegeling van een houten wand'),'kant':'rechts','eyebrow':'VERF EN AFWERKING','kop':'Welke verf past waar?','tekst':['Voor muren en plafonds gebruiken we latex. Een matte latex verbergt kleine oneffenheden en geeft een rustig beeld; een afwasbare latex is handiger op plekken waar handen en spatten komen. Deuren, kozijnen en trappen krijgen lak. Watergedragen lak is geurarm en vergeelt niet, en is sneller droog dan de oude alkydlak. Welke u kiest, hangt af van het gebruik en wat erop zit; dat bespreekt Stef bij de opname.','Wilt u een heel strak resultaat zonder kwaststrepen, bijvoorbeeld op deuren of keukenfronten? Kijk dan bij <a href="/diensten/spuitwerk/">spuitwerk</a>. Een accentwand met behang combineren met schilderwerk kan ook, zie <a href="/diensten/behangwerk/">behangwerk</a>.'],
   },
  ],
  'vraag':('Toe aan binnenschilderwerk in Oldebroek of omgeving?','Bel Stef op 06 24 99 67 00 of vraag online een offerte aan. Hij komt vrijblijvend langs, bekijkt het werk met u en stuurt een offerte met alles erop en eraan.'),
 },
 'buitenschilderwerk':{
  'hero':('buitenschilderwerk-rietgedekt.jpg','Rietgedekte woning met witte gevel en donker houtwerk na buitenschilderwerk'),
  'eyebrow':'BUITENSCHILDERWERK','kop':'Buitenschilderwerk in Oldebroek en omgeving',
  'intro':['Regen, zon, vorst en wind: het houtwerk aan de buitenkant van uw woning of pand krijgt het hele jaar klappen. Verf is daar de enige bescherming tegen. Zodra die scheurt, bladdert of dof wordt, komt er vocht in het hout en begint de schade. Van Ommen Schilderwerken uit Oldebroek houdt uw kozijnen, deuren en gevelhout in goede staat.','Stef komt vrijblijvend langs en bekijkt hoe het houtwerk ervoor staat. Bel 06 24 99 67 00 of vraag online een offerte aan.'],
  'banden':[
   {'foto':('woning-achtergevel-na.jpg','Witte woning met donkere kozijnen, dakranden en gevelbekleding'),'kant':'links','eyebrow':'WAT VALT ERONDER','kop':'Wat schilderen we buiten?','tekst':['<ul><li>Kozijnen, ramen en buitendeuren</li><li>Gevelbetimmering, boeidelen en dakranden</li><li>Dakkapellen en dakgoten van hout</li><li>Garage- en schuurdeuren</li><li>Schuttingen, veranda’s en overkappingen</li></ul>','De voorbereiding bepaalt hoe lang het schilderwerk meegaat. Het houtwerk wordt gereinigd en geschuurd, losse verf gaat eraf en alle kozijnen worden gecontroleerd op <a href="/diensten/houtrotreparatie/">houtrot</a>. Open naden en slechte kitranden vernieuwen we, want daar komt het water naar binnen. Daarna krijgen kale plekken een grondlaag en volgen minimaal twee lagen verf.'],'donker':{'label':'WANNEER BUITEN SCHILDEREN','tekst':'Buiten schilderen kan van het voorjaar tot in het najaar, zolang het droog is en het hout droog is. Bij regen of kou ligt het werk even stil en gaat het verder zodra het weer het toelaat; dat spreekt Stef vooraf met u af. Ook de bereikbaarheid van hoger gelegen houtwerk en wat er rond het huis vrij moet staan, komt bij de opname aan bod.'}},
   {'foto':('woning-uitbouw-na.jpg','Uitbouw met donkere kozijnen en dakrand tegen een witte gevel'),'kant':'rechts','eyebrow':'ONDERHOUD','kop':'Op tijd bijhouden is goedkoper dan herstellen','tekst':['Buitenschilderwerk vraagt gemiddeld elke vier tot zeven jaar aandacht, afhankelijk van de ligging, de kleur en de staat van het hout. Een donkere kleur op de zonkant slijt sneller dan een lichte kleur in de schaduw. Een tussentijdse controle voorkomt dat een klein scheurtje uitgroeit tot een rotte onderdorpel.','Wilt u het onderhoud van uw buitenschilderwerk vooruit plannen? Kijk bij <a href="/diensten/onderhoud-renovatie/">onderhoud en renovatie</a>. Voor bedrijfspanden en VvE’s maakt Stef een onderhoudsplan, zie <a href="/diensten/zakelijk-vve/">zakelijk en VvE</a>.'],
   },
  ],
  'vraag':('Toe aan een buitenbeurt in Oldebroek of omgeving?','Bel Stef op 06 24 99 67 00 of vraag online een offerte aan. Hij komt vrijblijvend langs, bekijkt het houtwerk en stuurt een offerte voor wat er echt nodig is.'),
 },
 'houtrotreparatie':{
  'hero':('onderhoud-houtrot-plamuren.jpg','Houtrot in een kozijnhoek wordt hersteld met plamuur en een plamuurmes'),
  'eyebrow':'HOUTROTREPARATIE','kop':'Houtrotreparatie in Oldebroek en omgeving',
  'intro':['Houtrot zit meestal onder de verf. Het hout wordt zacht, de verf bladdert en de onderkant van een kozijn of deur voelt sponzig aan. Schilderen over aangetast hout helpt niet; de rot gaat eronder gewoon door. Van Ommen Schilderwerken uit Oldebroek herstelt het hout eerst, en schildert het daarna.','Twijfelt u of een kozijn nog goed is? Stef komt vrijblijvend kijken. Bel 06 24 99 67 00 of vraag online een offerte aan.'],
  'banden':[
   {'foto':('houtrot-reparatiepasta.jpg','Houtreparatiepasta op een plamuurmes, klaar om een aangetast kozijn te herstellen'),'kant':'links','eyebrow':'HERKENNEN','kop':'Hoe herkent u houtrot?','tekst':['<ul><li>Zacht of veerkrachtig hout als u erop drukt</li><li>Bladderende of opbollende verf, vooral onderaan</li><li>Donkere plekken en scheuren in het hout</li><li>Open naden bij hoeken en verbindingen</li><li>Kitranden die loslaten</li></ul>','Houtrot ontstaat waar water blijft staan: op onderdorpels, bij hoekverbindingen en achter losse kit. Hoe eerder u het ziet, hoe kleiner de reparatie. Een plek van een paar centimeter is in een ochtend hersteld; wacht u jaren, dan moet soms een heel kozijndeel vervangen worden.'],'donker':{'label':'WAT KUNT U ALVAST DOEN','tekst':'Loop een keer langs alle kozijnen en druk met een vinger op de onderkant. Voelt het zacht, maak dan een foto van dichtbij en een overzichtsfoto en stuur die mee met uw aanvraag. Zo kan Stef vooraf al inschatten wat er speelt. Hoe groot de schade echt is, blijkt pas na het open maken van het hout.'}},
   {'foto':('houtrot-dakrand-voor-na.jpg','Voor en na: een dakrand met een gat van houtrot naast dezelfde dakrand hersteld en wit geschilderd'),'kant':'rechts','eyebrow':'HERSTEL','kop':'Zo herstellen we het','tekst':['Het aangetaste hout gaat weg tot op gezond hout en de plek krijgt tijd om te drogen. Daarna wordt de plek gevuld met een houtreparatiemiddel dat met het hout meewerkt, in model geschuurd en gegrond. Is er te veel weg, dan komt er een nieuw stuk hout in of wordt het onderdeel vervangen. Tot slot schilderen we het hele kozijn, zodat de reparatie niet meer te zien is.','Houtrotreparatie combineren we meestal met het <a href="/diensten/buitenschilderwerk/">buitenschilderwerk</a>, zodat het in één keer klaar is.'],
   },
  ],
  'vraag':('Houtrot in een kozijn of deur?','Bel Stef op 06 24 99 67 00 of vraag online een offerte aan. Hij komt vrijblijvend kijken en zegt eerlijk of herstellen nog kan of dat vervangen verstandiger is.'),
 },
 'onderhoud-renovatie':{
  'hero':('woning-gevel-na.jpg','Woning met strak witte gevel en donkere kozijnen na renovatie'),
  'eyebrow':'ONDERHOUD & RENOVATIE','kop':'Onderhoud van schilderwerk in Oldebroek en omgeving',
  'intro':['Schilderwerk gaat het langst mee als u het bijhoudt. Een scheurtje bijwerken, een kitnaad vernieuwen of een kwetsbare onderdorpel opnieuw in de verf zetten kost weinig; wachten tot de verf eraf hangt kost een hele buitenbeurt. Van Ommen Schilderwerken uit Oldebroek doet het kleine onderhoud en het grote werk bij een verbouwing.','Stef komt vrijblijvend langs en zegt wat nu nodig is en wat kan wachten. Bel 06 24 99 67 00 of vraag online een offerte aan.'],
  'banden':[
   {'voorna':(('woning-gevel-voor.jpg','Hoek van de woning vóór de renovatie: bakstenen gevel en donkere kozijnen'),('woning-gevel-hoek-na.jpg','Dezelfde hoek na de renovatie: witte gevel en donkere gevelbekleding')),'kant':'links','eyebrow':'RENOVATIE','kop':'Schilderwerk bij een renovatie','tekst':['Bij een renovatie of verbouwing pakken we het grotere werk op: nieuwe kozijnen, deuren en stucwerk in de verf, oud schilderwerk herstellen en de hele woning weer één geheel maken. Hiernaast een woning voor en na.','Voor bedrijfspanden en VvE’s zetten we het onderhoud in een plan over meerdere jaren, zie <a href="/diensten/zakelijk-vve/">zakelijk en VvE</a>.']},
   {'foto':('onderhoud-kozijnen-dak.jpg','Vers geschilderde witte en gele kozijnen van een dakopbouw, gezien vanaf het dak'),'kant':'rechts','eyebrow':'ONDERHOUD','kop':'Wat houdt onderhoud in?','tekst':['<ul><li>Controle van al het buitenhoutwerk op scheuren, kale plekken en <a href="/diensten/houtrotreparatie/">houtrot</a></li><li>Beschadigingen bijwerken en kale plekken gronden</li><li>Kitnaden en open verbindingen vernieuwen</li><li>Kwetsbare delen (onderdorpels, zonkant) opnieuw in de verf</li><li>Binnen: beschadigde deuren, kozijnen en wanden bijwerken</li></ul>','Buitenschilderwerk vraagt gemiddeld elke vier tot zeven jaar een beurt, afhankelijk van ligging, kleur en de staat van het hout. Een controle om de twee jaar voorkomt dat kleine schade groot wordt. Binnen gaat schilderwerk langer mee. Stef bekijkt uw woning of pand en adviseert een ritme dat past.'],'donker':{'label':'BIJ EEN VERBOUWING','tekst':'Bij een renovatie stemt Stef het schilderwerk af op de andere vaklieden: na het stucwerk en de installaties, vóór de vloer en de oplevering. Nieuwe kozijnen en deuren worden gegrond en afgelakt, nieuw stucwerk krijgt een voorstrijk en twee lagen latex, en bestaand schilderwerk wordt bijgewerkt zodat oud en nieuw één geheel worden.'}},
  ],
  'vraag':('Wilt u weten hoe uw schilderwerk ervoor staat?','Bel Stef op 06 24 99 67 00 of vraag online een offerte aan. Hij komt vrijblijvend langs, loopt alles na en zegt wat nu nodig is en wat later kan.'),
 },
 'spuitwerk':{
  'hero':('spuitwerk-trap.jpg','Wit gespoten trap met balustrade, met het spuitpistool op de voorgrond'),
  'eyebrow':'SPUITWERK','kop':'Spuitwerk in Oldebroek en omgeving',
  'intro':['Deuren, kozijnen en keukenfronten ziet u van dichtbij en raakt u elke dag aan. Met de kwast blijven er altijd strepen zichtbaar; gespoten wordt het oppervlak glad en egaal, alsof het zo uit de fabriek komt. Van Ommen Schilderwerken uit Oldebroek spuit houtwerk, trappen en keukens in woningen en bedrijfspanden.','Stef komt vrijblijvend langs en bekijkt wat zich laat spuiten. Bel 06 24 99 67 00 of vraag online een offerte aan.'],
  'banden':[
   {'foto':('spuitwerk-trap.jpg','Wit gespoten trap en balustrade'),'kant':'links','eyebrow':'WAT VALT ERONDER','kop':'Wat kunnen we spuiten?','tekst':['<ul><li>Binnendeuren en kozijnen</li><li>Trappen, leuningen en balustrades</li><li>Keukenfronten, kastdeuren en meubels</li><li>Plinten en radiatoren</li><li>Plafonds en wanden met de spuit in latex</li></ul>','Het resultaat valt of staat met de voorbereiding. Het bestaande werk wordt ontvet en geschuurd, beschadigingen bijgewerkt en waar nodig gegrond. Alles eromheen gaat onder tape en folie. Daarna spuiten we in dunne lagen, zodat er geen zakkers ontstaan en de laag overal even dik is.'],'donker':{'label':'TIJDENS HET WERK','tekst':'Spuitwerk droogt snel, maar de ruimte moet tijdens het spuiten en het drogen vrij zijn. We spreken vooraf af welke deuren en ruimtes u een dag niet kunt gebruiken en in welke volgorde we werken, zodat u er zo min mogelijk last van heeft. Deuren en kastdeuren kunnen ook uitgenomen en elders gespoten worden.'}},
   {'foto':('spuitwerk-apparatuur.jpg','Spuitapparatuur met spuitpistool, grondverf en stofafzuiging op een afgedekte vloer'),'kant':'rechts','eyebrow':'KEUKENS','kop':'Een nieuwe keuken zonder te vervangen','tekst':['Een keuken die technisch nog goed is maar gedateerd oogt, hoeft niet weg. Keukenfronten en deurtjes kunnen in een nieuwe kleur gespoten worden; dat kost een fractie van een nieuwe keuken. Stef bekijkt eerst het materiaal van de fronten (hout, mdf, folie) en zegt eerlijk wat haalbaar is en wat niet.','Gaat het om één kamer compleet, dan combineren we spuitwerk met <a href="/diensten/binnenschilderwerk/">binnenschilderwerk</a> voor muren en plafonds.'],
   },
  ],
  'vraag':('Deuren, trap of keuken laten spuiten?','Bel Stef op 06 24 99 67 00 of vraag online een offerte aan. Hij komt vrijblijvend langs en laat zien wat spuitwerk voor uw huis kan doen.'),
 },
 'behangwerk':{
  'hero':('behangwerk-hero.jpg','Schilder van Van Ommen Schilderwerken brengt behang met citroenmotief aan op een wand'),'hero_tekst_rechts':True,
  'eyebrow':'BEHANGWERK','kop':'Behangwerk in Oldebroek en omgeving',
  'intro':['Met behang geeft u een kamer in één dag een andere sfeer: een kleur, een structuur of een patroon dat met verf alleen niet lukt. Maar een strak behangen wand begint bij een gladde ondergrond, en daar gaat het vaak mis. Van Ommen Schilderwerken uit Oldebroek haalt oud behang weg, maakt de wand glad en brengt het nieuwe behang strak aan.','Stef komt vrijblijvend langs en bekijkt de wanden. Bel 06 24 99 67 00 of vraag online een offerte aan.'],
  'banden':[
   {'foto':('behangwerk-structuur.jpg','Wand met structuurbehang in een bladmotief rond een witte deur'),'kant':'links','eyebrow':'WAT VALT ERONDER','kop':'Wat doen we met behang?','tekst':['<ul><li>Oud behang verwijderen, ook meerdere lagen</li><li>Wanden egaliseren en voorstrijken</li><li>Vliesbehang, patroonbehang en structuurbehang aanbrengen</li><li>Fotobehang op maat, naadloos</li><li>Renovlies of glasvlies aanbrengen en sauzen</li></ul>','Eerst halen we het oude behang en losse lagen weg. Gaatjes, scheuren en oneffenheden plamuren we dicht en de wand wordt geschuurd en voorgestreken. Pas dan gaat het nieuwe behang erop, baan voor baan, met aandacht voor de naden en het doorlopen van het patroon bij hoeken, kozijnen en stopcontacten.'],'donker':{'label':'WAT SPREKEN WE AF','tekst':'Vertel om welke wanden of kamers het gaat en of er al behang op zit. Heeft u al een behang op het oog, geef dan het merk en het nummer door; dan rekent Stef uit hoeveel rollen er nodig zijn. Nog geen keus gemaakt? Dan denkt hij mee over wat past bij de ruimte en het licht. We spreken ook af wat vrij moet staan en of het behangwerk gecombineerd wordt met schilderwerk.'}},
   {'voorna':(('behangwerk-fotobehang-luipaard.jpg','Fotobehang met een luipaard op een accentwand, de andere wanden geschilderd'),('behangwerk-fotobehang-paard.jpg','Fotobehang met IJslandse paarden op een accentwand naast lila geschilderde wanden')),'labels':('',''),'kant':'rechts','eyebrow':'COMBINEREN MET VERF','kop':'Een accentwand met behang','tekst':['Eén wand met behang of fotobehang en de andere wanden in een passende kleur geschilderd: dat is de combinatie die het vaakst gekozen wordt. Stef stemt de kleur van de verf af op het behang en plant het <a href="/diensten/binnenschilderwerk/">schilderwerk</a> en het behangwerk in één keer, zodat de kamer in één keer klaar is.'],
   },
  ],
  'vraag':('Een wand of kamer laten behangen?','Bel Stef op 06 24 99 67 00 of vraag online een offerte aan. Hij komt vrijblijvend langs, bekijkt de wanden en rekent uit wat u nodig heeft.'),
 },
 'zakelijk-vve':{
  'hero':('huenestein-1.jpg','Entree van een bedrijfspand met stalen trap, zwarte plafonds en stalen pui'),
  'eyebrow':'ZAKELIJK & VVE-SCHILDERWERK','kop':'Zakelijk schilderwerk en VvE-onderhoud in Oldebroek en omgeving',
  'intro':['Voor een bedrijfspand, een kantoor of een VvE wilt u twee dingen weten: wat kost het en wanneer gebeurt het. Van Ommen Schilderwerken uit Oldebroek schildert bedrijfspanden en appartementencomplexen binnen en buiten, en zet het onderhoud in een plan over meerdere jaren, zodat u de kosten kunt spreiden en achterstallig onderhoud voorkomt.','Stef komt vrijblijvend langs voor een opname van het pand. Bel 06 24 99 67 00 of vraag online een offerte aan.'],
  'banden':[
   {'foto':('zakelijk-stalen-pui.jpg','Stalen glazen pui in een kantoorpand met strak geschilderde wanden'),'kant':'links','eyebrow':'BEDRIJFSPANDEN','kop':'Schilderen terwijl het werk doorgaat','tekst':['<ul><li>Kantoren, showrooms, kantines en gangen</li><li>Entrees, trappenhuizen en sanitaire ruimtes</li><li>Buitenhoutwerk, gevels en kozijnen</li><li>Nieuwbouw en verbouw, afgestemd met de andere vaklieden</li></ul>','We plannen het werk rond uw openingstijden en drukke momenten en werken waar het kan in fases, per ruimte of per verdieping. Ruimtes worden afgezet en afgedekt en aan het eind van de dag is de vloer weer vrij. Bekijk onze projecten bij <a href="/projecten/huenestein/">Huenestein</a>, <a href="/projecten/koopman-bestratingen/">Koopman Bestratingen</a>, <a href="/projecten/allround-zonwering/">Allround Zonwering</a> en de <a href="/projecten/gemeente-oldebroek/">gemeente Oldebroek</a>.'],'donker':{'label':'WAT SPREKEN WE AF','tekst':'Bij de opname bespreken we welke gebouwen en onderdelen het betreft, wie het aanspreekpunt is en welke afspraken er gelden voor medewerkers, huurders of bewoners. Ook de bereikbaarheid, de werktijden en de communicatie naar de gebruikers van het pand leggen we vooraf vast. U heeft bij Van Ommen één aanspreekpunt, van offerte tot oplevering.'}},
   {'foto':('gemeente-oldebroek-1.jpg','Receptiebalie in het gemeentehuis van Oldebroek tijdens het schilderwerk'),'kant':'rechts','eyebrow':'VVE’S EN COMPLEXEN','kop':'Een onderhoudsplan voor meerdere jaren','tekst':['Voor een VvE of appartementencomplex loopt Stef het hele pand na en zet hij in een plan welk schilderwerk wanneer aandacht nodig heeft: dit jaar de zonkant, over twee jaar de rest, en tussendoor een controle. Zo weet het bestuur jaren vooruit waar het aan toe is en kan het werk per gebouwdeel of per jaar verdeeld worden over de begroting.','Een onderhoudsplan begint met een opname en een gesprek over wat de VvE wil. Daarna ontvangt u een plan met prijzen per onderdeel, zonder verplichting.'],
   },
  ],
  'vraag':('Een offerte of onderhoudsplan voor uw pand?','Bel Stef op 06 24 99 67 00 of vraag online een offerte aan. Hij komt vrijblijvend langs voor een opname en bespreekt met u de planning en de fasering.'),
 },
}
def service_layout(v,lay,request):
 hero_img,hero_alt=lay['hero']
 h=f'<section class="dienst-hero{" tekst-rechts" if lay.get("hero_tekst_rechts") else ""}"><img src="/assets/{hero_img}" alt="{escape(hero_alt)}" width="1600" height="900" loading="eager" fetchpriority="high"><div class="dienst-hero-tekst"><h1>{escape(v["name"])}</h1><nav class="breadcrumbs" aria-label="Kruimelpad"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/diensten/">Diensten</a><span aria-hidden="true">/</span><span aria-current="page">{escape(v["name"])}</span></nav></div></section>'
 punten=''.join('<li>'+escape(x)+'</li>' for x in STERKE_PUNTEN)
 plaatsen=', '.join('<a href="/'+pl['slug']+'/">'+escape(pl['name'])+'</a>' for pl in LOCATIONS[:-1])+' en <a href="/'+LOCATIONS[-1]['slug']+'/">'+escape(LOCATIONS[-1]['name'])+'</a>'
 h+='<section class="dienst-intro section-pad"><div class="dienst-intro-tekst"><p class="eyebrow">'+escape(lay['eyebrow'])+'</p><h2>'+escape(lay['kop'])+'</h2>'+''.join('<p>'+escape(t)+'</p>' for t in lay['intro'])+'<p class="dienst-plaatsen">'+escape(v['name'])+' in '+plaatsen+'.</p></div><ul class="dienst-punten" aria-label="Waar u op kunt rekenen">'+punten+'</ul></section>'
 for b in lay['banden']:
  if b.get('voorna'):
   (vi,va),(ni,na)=b['voorna']
   labels=b.get('labels',('Voor','Na'))
   cap=lambda t,extra='':f'<figcaption><span class="voorna-label{extra}">{escape(t)}</span></figcaption>' if t else ''
   foto=f'<div class="dienst-band-voorna"><figure><img src="/assets/{vi}" alt="{escape(va)}" width="1200" height="1600" loading="lazy">{cap(labels[0])}</figure><figure><img src="/assets/{ni}" alt="{escape(na)}" width="1200" height="1600" loading="lazy">{cap(labels[1]," na")}</figure></div>'
  else:
   img,alt=b['foto']
   foto=f'<figure class="dienst-band-foto"><img src="/assets/{img}" alt="{escape(alt)}" width="1200" height="900" loading="lazy"></figure>'
  tekst='<div class="dienst-band-tekst"><p class="eyebrow">'+escape(b['eyebrow'])+'</p><h2>'+escape(b['kop'])+'</h2>'+''.join(t if t.startswith('<ul') else '<p>'+t+'</p>' for t in b['tekst'])+'</div>'
  h+='<section class="dienst-band section-pad '+('foto-links' if b['kant']=='links' else 'foto-rechts')+'">'+(foto+tekst if b['kant']=='links' else tekst+foto)+'</section>'
  if b.get('donker'):
   h+='<section class="dienst-donker section-pad"><p class="eyebrow">'+escape(b['donker']['label'])+'</p><p>'+escape(b['donker']['tekst'])+'</p></section>'
 return h
for v in services:
 side='<aside class="service-sidebar"><p class="eyebrow">ONZE DIENSTEN</p><nav aria-label="Diensten">'+''.join(f'<a href="{service_url(x)}"'+(' aria-current="page"' if x==v else '')+'>'+escape(x['name'])+'</a>' for x in services)+'</nav><div class="sidebar-contact"><p>Even overleggen?</p><a href="tel:+31624996700">Bel Stef<br><strong>06 24 99 67 00</strong></a></div></aside>'
 request='/offerte/?dienst='+quote(v['name'])
 tags=''.join('<li>'+escape(t)+'</li>' for t in v['tags'])
 detail=f'''<article class="service-article"><p class="eyebrow">{'AANDACHT VOOR UW PAND' if v['slug']=='zakelijk-vve' else 'AANDACHT VOOR UW WONING'}</p><h2>{escape(SERVICE_COPY[v['slug']]['heading'])}</h2><p class="article-lead">{escape(v['text'])}</p><p>{escape(SERVICE_COPY[v['slug']]['paragraph'])}</p><h3>Wat kunnen we bespreken?</h3><ul class="scope-list">{tags}</ul><h3>Een aanpak voor uw situatie</h3><p>De staat van de ondergrond en uw wensen bepalen wat nodig is. We bekijken het werk, bespreken de voorbereiding en stemmen de afwerking en planning met u af.</p><p>Vertel ons wat u wilt laten doen. Met een korte beschrijving en enkele foto’s krijgen we een eerste beeld. Daarna bespreken we de volgende stap.</p><div class="article-actions"><a class="button" href="{request}">Vraag een offerte aan </a><a class="text-link" href="/over-ons/#werkwijze">Bekijk onze werkwijze</a></div></article>'''
 copy=SERVICE_COPY[v['slug']]
 detail=detail.replace('<h3>Een aanpak voor uw situatie</h3>','<h3>Wat spreken we vooraf af?</h3><p>'+escape(copy['preparation'])+'</p><h3>'+escape(copy['question'])+'</h3><p>'+escape(copy['answer'])+'</p><h3>Een offerte voor uw '+('pand' if v['slug']=='zakelijk-vve' else 'woning')+'</h3>')
 if v['slug'] in SERVICE_LAYOUT:
  content=service_layout(v,SERVICE_LAYOUT[v['slug']],request)+cta()
 else:
  content=intro(v['name'],escape(v['name']).replace(' &amp; ',' &amp;<br>'),escape(SERVICE_COPY[v['slug']]['summary']),True)+'<section class="service-detail section-pad">'+detail+side+'</section>'+compare+cta()
 render(service_url(v),SEO_DIENST[v['slug']][0],SEO_DIENST[v['slug']][1],content,'/diensten/')
# Projectenpagina: fotokaarten (titel, dienst) en een introblok; voor/na-kaarten springen naar de vergelijking eronder, de rest opent de fotoviewer.
# Projectpagina's: per project een eigen pagina onder /projecten/<slug>/ met een fotogalerij. Alleen bevestigde feiten (plaats, pand) opnemen.
PROJECTPAGINAS=[
 {'slug':'huenestein','titel':'Project Huenestein','plaats':'Elburg','label':'Zakelijk & VvE-schilderwerk','dienst_url':'/diensten/zakelijk-vve/','dienst_naam':'Zakelijk & VvE-schilderwerk',
  'intro':'Binnenschilderwerk in een nieuw bedrijfspand in Elburg: wanden, plafonds en kozijnen strak afgewerkt, van de entree tot de kantine en de sanitaire ruimtes.',
  'kop':'',
  'tekst':[],
  'description':'Bekijk het binnenschilderwerk van Van Ommen Schilderwerken bij Huenestein in Elburg: wanden, plafonds en kozijnen in een modern bedrijfspand.',
  'fotos':[
   ('huenestein-1.jpg','Open trap van staal en eikenhout in de entree van het bedrijfspand, met zwart plafond en stalen pui'),
   ('huenestein-2.jpg','Hal met strak geschilderde wanden, houten deuren met zwarte kozijnen en een zwart plafond'),
   ('huenestein-3.jpg','Verdieping met glazen balustrade, stalen binnenpui en uitzicht op het bedrijventerrein'),
   ('huenestein-4.jpg','Kantine met kookeiland, barkrukken en zwart geschilderd plafond met spots'),
   ('huenestein-5.jpg','Toiletruimte met donkere tegels, houten wastafelmeubel en zwart deurkozijn'),
  ]},
 {'slug':'koopman-bestratingen','titel':'Project Koopman Bestratingen','plaats':'Elburg','label':'Zakelijk & VvE-schilderwerk','dienst_url':'/diensten/zakelijk-vve/','dienst_naam':'Zakelijk & VvE-schilderwerk',
  'intro':'Binnenschilderwerk in het bedrijfspand van Koopman Bestratingen in Elburg: wanden, kozijnen en plinten strak afgewerkt in de gangen, de kantoren en de kantine.',
  'kop':'',
  'tekst':[],
  'description':'Bekijk het binnenschilderwerk van Van Ommen Schilderwerken bij Koopman Bestratingen in Elburg: wanden, kozijnen en plinten in een modern bedrijfspand.',
  'fotos':[
   ('koopman-1.jpg','Lange gang met zandkleurige wanden, witte plinten, zwart systeemplafond en visgraatvloer'),
   ('koopman-2.jpg','Doorkijk vanaf de pantry naar de hal met stalen binnenpuien en zwarte kastenwand'),
   ('koopman-3.jpg','Kantoor met hoog smal raam in zwart kozijn en strak geschilderde wanden'),
   ('koopman-4.jpg','Doorgang met stalen glazen deuren naast een zwarte keukenkast'),
   ('koopman-5.jpg','Kantine met zwarte pantry, witte deur en zwart systeemplafond boven de visgraatvloer'),
  ]},
 {'slug':'buitenschilderwerk-particuliere-woning','titel':'Buitenschilderwerk particuliere woning','plaats':'','label':'Buitenschilderwerk','dienst_url':'/diensten/buitenschilderwerk/','dienst_naam':'Buitenschilderwerk',
  'intro':'Een particuliere woning met een nieuwe buitenkant: de gevel strak wit, de kozijnen, het gevelhout en de plint donker. Bekijk het verschil tussen voor en na.',
  'kop':'',
  'tekst':[],
  'description':'Bekijk hoe een particuliere woning een strakke witte gevel met donkere kozijnen kreeg. Voor-en-nafoto’s van buitenschilderwerk door Van Ommen Schilderwerken.',
  'voorna':(('woning-gevel-voor.jpg','Hoek van de woning vóór het werk: bakstenen gevel, donkere kozijnen en uitbouw met verticale gevelbekleding'),('woning-gevel-hoek-na.jpg','Dezelfde hoek na het werk: strak witte gevel met donkere kozijnen, dakranden en gevelbekleding')),
  'fotos':[
   ('woning-gevel-na.jpg','Voorgevel van de woning na het werk: strak wit gestucte gevel, donkere plint, donkere kozijnen en houten voordeur'),
   ('woning-achtergevel-na.jpg','Achtergevel na het werk: witte bovenverdieping, donkere dakranden en donkere verticale gevelbekleding rond de schuifpui'),
   ('woning-uitbouw-na.jpg','Uitbouw met donkere kozijnen en dakrand tegen de witte gevel, gezien vanaf de zijkant van de woning'),
  ]},
 {'slug':'gemeente-oldebroek','titel':'Gemeente Oldebroek','plaats':'Oldebroek','label':'Zakelijk & VvE-schilderwerk','dienst_url':'/diensten/zakelijk-vve/','dienst_naam':'Zakelijk & VvE-schilderwerk',
  'intro':'De houten receptiebalie in het gemeentehuis van Oldebroek opnieuw afgewerkt: geschuurd en in een donkere kleur gebeitst, terwijl de hal in gebruik bleef.',
  'kop':'',
  'tekst':[],
  'description':'Bekijk hoe Van Ommen Schilderwerken de houten receptiebalie van de gemeente Oldebroek schuurde en opnieuw afwerkte.',
  'fotos':[
   ('gemeente-oldebroek-1.jpg','Receptiebalie met donker houten blad en verlicht wit front met het woord info in de hal van het gemeentehuis, met schildersgereedschap op de afgedekte vloer'),
   ('gemeente-oldebroek-2.jpg','Schuurmachine op het houten balieblad, half geschuurd en half nog donker, met afplaktape langs de randen'),
   ('gemeente-oldebroek-3.jpg','Hoek van de balie met het donker afgewerkte houten blad boven het witte front met het woord info'),
   ('gemeente-oldebroek-4.jpg','Bovenaanzicht van het geschuurde eiken balieblad met afplaktape, klaar voor de nieuwe afwerking'),
  ]},
 {'slug':'allround-zonwering','titel':'Project Allround Zonwering','plaats':'Elburg','label':'Zakelijk & VvE-schilderwerk','dienst_url':'/diensten/zakelijk-vve/','dienst_naam':'Zakelijk & VvE-schilderwerk',
  'intro':'Binnenschilderwerk in het bedrijfspand van Allround Zonwering in Elburg: wanden, trap, deuren en kozijnen strak afgewerkt in lichte en donkere tinten.',
  'kop':'',
  'tekst':[],
  'description':'Bekijk het binnenschilderwerk van Van Ommen Schilderwerken bij Allround Zonwering in Elburg: wanden, trap, deuren en kozijnen in een modern bedrijfspand.',
  'fotos':[
   ('allround-zonwering-1.jpg','Trap met zwarte treden en witte stootborden, lichte trapwand en drie witte deuren in een donkergrijze wand'),
   ('allround-zonwering-2.jpg','Donkergrijze wand met drie witte deuren naast de trap, met gietvloer en systeemplafond'),
   ('allround-zonwering-3.jpg','Zandkleurige wanden bij de garderobe en de pantry met zwart houten kastwerk en wit blad'),
   ('allround-zonwering-4.jpg','Pantry met zwart houten kasten en inbouwapparatuur in een zandkleurige wandnis'),
   ('allround-zonwering-5.jpg','Lichte wanden rond een stalen glazen deur naar de verdieping, met witte plinten en gietvloer'),
   ('allround-zonwering-6.jpg','Twee hoge ramen met zwart geschilderde kozijnen in een zandkleurige wand, met visgraatvloer'),
   ('allround-zonwering-7.jpg','Twee witte deuren met witte kozijnen naast een grijs geschilderde wand, met visgraatvloer'),
   ('allround-zonwering-8.jpg','Gang met zandkleurige wanden, witte plinten en doorkijk naar een achterliggende ruimte, met visgraatvloer'),
  ]},
]
PROJECTEN=[{'titel':pp['titel'],'plaats':pp['plaats'],'image':pp['fotos'][0][0],'alt':pp['fotos'][0][1],'href':'/projecten/'+pp['slug']+'/'} for pp in PROJECTPAGINAS]  # losse foto's zonder project zijn op 2026-11-23 weggehaald (wens opdrachtgever)

def fotostrook():
 """Doorlopende, vanzelf bewegende strook met projectfoto's (contactpagina). Twee keer dezelfde reeks voor een naadloze lus; CSS-animatie, pauze bij hover, stil bij 'minder beweging'."""
 fotos=[(f[0],f[1],pp['titel']) for i in range(3) for pp in PROJECTPAGINAS for f in pp['fotos'][i:i+1]]  # om de beurt per project, zodat buren verschillen
 items=''.join('<li><img src="/assets/'+f+'" alt="'+escape(a)+'" width="1200" height="1600" loading="lazy" decoding="async"></li>' for f,a,t in fotos)
 return ('<section class="fotostrook" aria-labelledby="fotostrook-title"><div class="fotostrook-kop section-pad"><p class="eyebrow">ONS WERK</p><h2 id="fotostrook-title">Foto\'s uit onze projecten</h2><a class="text-link" href="/projecten/">Bekijk alle projecten <span>&rarr;</span></a></div>'
  '<div class="fotostrook-baan"><ul class="fotostrook-reeks">'+items+'</ul><ul class="fotostrook-reeks" aria-hidden="true">'+items+'</ul></div></section>')

def project_carousel():
 """Donkere band met de projecten (plaatspagina's): strook met scroll-snap tot de rand, pijlen aan de zijkant (app.js)."""
 kaarten=''.join('<li><a class="project-kaart" href="'+pr['href']+'"><img src="/assets/'+pr['image']+'" alt="'+escape(pr['alt'])+'" width="1200" height="1600" loading="lazy"><span class="project-kaart-tekst"><strong>'+escape(pr['titel'])+'</strong>'+('<span class="project-kaart-dienst">'+escape(pr['plaats'])+'</span>' if pr['plaats'] else '')+'</span></a></li>' for pr in PROJECTEN)
 return ('<section class="plaats-projecten" aria-labelledby="plaats-projecten-title"><div class="plaats-projecten-kop section-pad"><div><h2 id="plaats-projecten-title">Onze afgeronde projecten</h2><p>Binnen- en buitenschilderwerk bij woningen en bedrijfspanden in de regio.</p></div><a class="button button-outline" href="/projecten/">Projecten <span>&rarr;</span></a></div>'
  '<div class="carrousel-wrap"><button type="button" class="carrousel-knop carrousel-vorige" data-richting="-1" aria-label="Vorige projecten">&#8249;</button>'
  '<ul class="carrousel">'+kaarten+'</ul><button type="button" class="carrousel-knop carrousel-volgende" data-richting="1" aria-label="Volgende projecten">&#8250;</button></div></section>')
def projecten_kaarten():
 kaarten=[]
 for i,p in enumerate(PROJECTEN):
  plaats='<span class="project-kaart-dienst">'+escape(p['plaats'])+'</span>' if p.get('plaats') else ''
  binnen=f'<img src="/assets/{p["image"]}" alt="{escape(p["alt"])}" width="1200" height="800" loading="lazy"><span class="project-kaart-tekst"><strong>{escape(p["titel"])}</strong>{plaats}</span>'
  klasse='project-kaart'+(' '+p['klasse'] if p.get('klasse') else '')
  if p.get('href'):kaarten.append(f'<a class="{klasse}" href="{p["href"]}">{binnen}</a>')
  else:kaarten.append(f'<button class="{klasse}" type="button" data-photo="/assets/{p["image"]}" data-title="{escape(p["titel"])}" aria-label="{escape(p["titel"])}, vergroot de foto">{binnen}</button>')
  if i==0:kaarten.append('<div class="projecten-intro"><h1>Projecten</h1><p>Een overzicht van schilderwerk dat Van Ommen Schilderwerken heeft uitgevoerd: binnen, buiten en behangwerk. Kijk hoe de voorbereiding eruitziet en wat het eindresultaat is.</p><p>Zelf iets laten schilderen of renoveren? Vertel wat u wilt, dan bespreekt Stef het met u.</p><div class="article-actions"><a class="button" href="/offerte/">Offerte aanvragen </a></div></div>')
 return '<section class="projecten-overzicht section-pad" aria-label="Projecten"><div class="projecten-grid">'+''.join(kaarten)+'</div></section>'
content=projecten_kaarten()+cta()
render('/projecten/','Projecten','Bekijk echte foto’s van schilderprojecten van Van Ommen Schilderwerken, van voorbereiding tot afwerking.',content,'/projecten/',gallery=True)
for pp in PROJECTPAGINAS:
 galerij=''.join(f'<button class="project-kaart" type="button" data-photo="/assets/{img}" data-title="{escape(pp["titel"])}, foto {i+1}" aria-label="Foto {i+1} van {escape(pp["titel"].lower())}, vergroot de foto"><img src="/assets/{img}" alt="{escape(alt)}" width="1200" height="1600" loading="lazy"></button>' for i,(img,alt) in enumerate(pp['fotos']))
 tekst=''.join('<p>'+t+'</p>' for t in pp['tekst'])
 voorna=''
 if pp.get('voorna'):
  (vi,va),(ni,na)=pp['voorna']
  voorna='<div class="project-voorna" aria-label="Voor en na"><figure><button type="button" class="project-kaart" data-photo="/assets/'+vi+'" data-title="'+escape(pp['titel'])+', voor" aria-label="Foto voor het werk, vergroot de foto"><img src="/assets/'+vi+'" alt="'+escape(va)+'" width="1200" height="1600" loading="lazy"></button><figcaption><span class="voorna-label">Voor</span>Voor het werk</figcaption></figure><figure><button type="button" class="project-kaart" data-photo="/assets/'+ni+'" data-title="'+escape(pp['titel'])+', na" aria-label="Foto na het werk, vergroot de foto"><img src="/assets/'+ni+'" alt="'+escape(na)+'" width="1200" height="1600" loading="lazy"></button><figcaption><span class="voorna-label na">Na</span>Het eindresultaat</figcaption></figure></div>'
 content=intro(pp['titel'],escape(pp['titel']),escape(pp['intro']),'projecten')+'<section class="project-detail section-pad" aria-label="'+escape(pp['titel'])+'"><div class="project-detail-tekst"><p class="eyebrow">'+((escape(pp['plaats'].upper())+' · ') if pp['plaats'] else '')+escape(pp['label'].upper())+'</p>'+('<h2 id="project-titel">'+escape(pp['kop'])+'</h2>' if pp['kop'] else '')+tekst+'<div class="article-actions"><a class="button" href="/offerte/?dienst='+quote(pp['dienst_naam'])+'">Offerte aanvragen</a><a class="text-link" href="'+pp['dienst_url']+'">Meer over '+escape(pp['dienst_naam'][0].lower()+pp['dienst_naam'][1:])+'</a></div></div>'+voorna+'<div class="project-galerij'+(' enkel' if len(pp['fotos'])==1 else ' vier' if len(pp['fotos'])==4 else ' gelijk' if len(pp['fotos']) not in (5,7,8) else '')+'">'+galerij+'</div></section>'+cta()
 render('/projecten/'+pp['slug']+'/',pp['titel'],pp['description'],content,'/projecten/',gallery=True)
about=section('over');cls('intro-text',about)[0].text='Goed schilderwerk begint met persoonlijk contact.'
_ps=cls('about-copy',about)[0].findall('p')
_ps[1].text='Achter Van Ommen Schilderwerken staat Stef van Ommen. Hij werkt vanuit Oldebroek en schildert woningen, bedrijfspanden en VvE’s in '+', '.join(p['name'] for p in LOCATIONS[:4])+', '+LOCATIONS[4]['name']+' en de plaatsen eromheen.'
_ps[2].text='Stef komt zelf langs, maakt de offerte en voert het werk uit. Hij luistert eerst naar uw wensen, bereidt het werk zorgvuldig voor en legt de afspraken vooraf vast, voor één kamer net zo goed als voor de buitenkant van uw woning. Het bedrijf is een erkend leerbedrijf van SBB.'
facts='''<section class="company-facts section-pad section-space" aria-labelledby="facts-title"><div><p class="eyebrow">IN HET KORT</p><h2 id="facts-title">Wie komt er bij u schilderen?</h2></div><div class="company-facts-tekst"><p>Van Ommen Schilderwerken is het schildersbedrijf van Stef van Ommen in Oldebroek. Stef is eigenaar en schilder in één: hij maakt de offerte en voert het werk zelf uit, voor woningen, bedrijfspanden en VvE’s. Het bedrijf is een erkend leerbedrijf van SBB en leidt vakmensen op.</p><p>Stef werkt in '''+', '.join(p['name'] for p in LOCATIONS[:4])+' en '+LOCATIONS[4]['name']+(', en in de plaatsen eromheen, zoals '+', '.join(p['name'] for p in LOCATIONS[5:-1])+' en '+LOCATIONS[-1]['name'] if len(LOCATIONS)>5 else '')+'''. Bel <a href="tel:+31624996700">06 24 99 67 00</a> of mail naar <a href="mailto:info@vanommenschilderwerken.nl">info@vanommenschilderwerken.nl</a>.</p></div></section>'''
content=intro('Over ons','Gewoon goed<br>schilderwerk.','Van Ommen Schilderwerken uit Oldebroek. Duidelijke afspraken vooraf, netjes werken en opleveren zoals besproken.')+serial(about)+serial(section('werkwijze'))+cta('Kennismaken en uw plannen bespreken?')
render('/over-ons/','Over ons & onze werkwijze','Maak kennis met Van Ommen Schilderwerken uit Oldebroek en lees hoe wij uw schilderwerk aanpakken.',content,'/over-ons/')
contact=section('contact')
form=cls('quote-form',contact)[0]
form.find('h3').tag='h2'
form.find('h2').text='Vraag een offerte aan'
form.find('p').text='Benieuwd wat wij voor u kunnen betekenen? Vraag een offerte aan, dan komen wij vrijblijvend bij u langs om samen het werk aan uw woning of pand te bekijken. Uw wensen en ons advies verwerken wij in een gratis en vrijblijvende offerte. Velden met een * zijn verplicht.'
form.xpath('.//button[@type="submit"]')[0].text='Verstuur mijn aanvraag'
_last=form.xpath('(.//input[@name="service"])[last()]')[0];_last.set('value','Meerdere werkzaamheden / ik weet het nog niet');_last.getnext().text='Meerdere werkzaamheden / ik weet het nog niet'
cls('form-status',form)[0].text=''
note=cls('form-note',form)[0]
insert_content(note,'Uw aanvraag geeft uw wensen door; het is nog geen opdracht om te schilderen. Lees hoe we met uw gegevens omgaan in de <a href="/privacy/">privacyverklaring</a>.')
form.append(html.fromstring('<div class="quote-help"><p>Liever appcontact?</p><a class="text-link" id="quote-whatsapp" href="https://wa.me/31624996700" target="_blank" rel="noopener noreferrer">Bespreek uw wensen via WhatsApp</a><p>U kunt ook bellen: <a href="tel:+31624996700">06 24 99 67 00</a>.</p></div>'))
cls('contact-intro',contact)[0].append(html.fromstring('<div class="contact-voorwaarden"><p class="eyebrow">ALGEMENE VOORWAARDEN</p><p>Op al onze offertes en overeenkomsten zijn algemene voorwaarden van toepassing. Voor consumenten zijn dat de <a href="'+VOORWAARDEN['consument']+'" type="application/pdf">Algemene consumentenvoorwaarden voor de schilders-, onderhouds- en glaszetbranche in Nederland</a>, voor overige opdrachtgevers de <a href="'+VOORWAARDEN['zakelijk']+'" type="application/pdf">Algemene voorwaarden voor de zakelijke markt voor de schilders-, onderhouds- en glaszetbranche in Nederland</a>. Beide zijn gedeponeerd bij de Kamer van Koophandel te Gouda onder nummer 40409386. Op verzoek sturen wij u kosteloos een exemplaar.</p></div>'))
side=cls('contact-intro',contact)[0]
offerte_side=deepcopy(side)
offerte_side.find('p').text='LIEVER DIRECT CONTACT?'
h=offerte_side.find('h2');h.clear();h.text='Bel of app Stef';h.append(html.fromstring('<br>'));h.find('br').tail='gerust even.'
offerte_side.findall('p')[1].clear();offerte_side.findall('p')[1].text='Twijfelt u of iets kan, of wilt u eerst overleggen? Een belletje of appje is zo gedaan.'
content=intro('Offerte aanvragen','Gratis en vrijblijvend<br>een offerte.','Vul uw gegevens in. Stef komt bij u langs, bekijkt het werk met u en stuurt een offerte op maat.')+'<section class="contact section-pad section-space" id="contact">'+serial(form)+serial(offerte_side)+'</section>'
render('/offerte/','Offerte aanvragen','Vraag gratis en vrijblijvend een offerte aan bij Van Ommen Schilderwerken in Oldebroek. Stef komt langs, bekijkt het werk en stuurt een offerte op maat.',content,'/offerte/')
direct='<section class="direct-contact section-pad" aria-labelledby="direct-contact-title"><div class="direct-contact-inner"><div class="direct-contact-copy"><h2 id="direct-contact-title">Direct contact</h2><p>Toe aan nieuw schilderwerk of onderhoud, thuis of in uw bedrijfspand?<br>Neem gerust contact op en bespreek uw plannen.</p><ul class="direct-contact-list"><li><span>T.</span><a href="tel:+31624996700">06 24 99 67 00</a></li><li><span>E.</span><a href="mailto:info@vanommenschilderwerken.nl">info@vanommenschilderwerken.nl</a></li></ul><p class="direct-contact-meta">Bovendwarsweg 78, 8096 PR Oldebroek<br>KvK-nummer: 95415033</p></div><img src="/assets/bus-achterkant.jpg" alt="Bedrijfsbus van Van Ommen Schilderwerken met logo op de zijkant en achterdeuren" width="1536" height="2048" loading="lazy"></div></section>'
voorwaarden=serial(cls('contact-voorwaarden',side)[0])
content=intro('Contact','Uw woning of pand opfrissen?<br>Bespreek het met Stef.','Voor woningen, bedrijfspanden en VvE’s. Bel voor overleg, stuur uw wensen per e-mail of WhatsApp, of vraag direct een offerte aan.')+direct+'<section class="contact-extra section-pad section-space"><div class="contact-offerte"><p class="eyebrow">LIEVER METEEN EEN OFFERTE?</p><p>Vul het formulier in, dan komt Stef vrijblijvend langs.</p><a class="button" href="/offerte/">Offerte aanvragen</a></div>'+voorwaarden+'</section>'+fotostrook()
render('/contact/','Contact','Neem contact op met Stef van Ommen voor uw schilderwerk: bel 06 24 99 67 00, mail, app of vraag een offerte aan.',content,'/contact/')
for place in LOCATIONS:
 route='/'+place['slug']+'/'
 local=intro('Schilder '+place['name'],'Schilder in '+place['name'],escape(place['intro']))
 local+='<section class="local-story section-pad section-space"><article><h2>'+escape(place['heading'])+'</h2><p>'+escape(place['text'])+'</p><h3>'+escape(place['focus'])+'</h3><p>'+escape(place['focus_text'])+'</p><h3>'+escape(place['local_heading'])+'</h3><p>'+escape(place['local'])+'</p>'+('<p>'+place['extra']+'</p>' if place.get('extra') else '')+'<div class="article-actions"><a class="button" href="/offerte/">Offerte aanvragen</a><a class="text-link" href="tel:+31624996700">Bel Stef: 06 24 99 67 00</a></div></article><figure><img src="/assets/'+place['image']+'" alt="'+escape(place['alt'])+'" width="900" height="1200" loading="lazy"><figcaption>Een voorbeeld van ons schilderwerk. <a href="/projecten/">Bekijk onze projecten</a>.</figcaption></figure></section>'
 local+=project_carousel()
 local+='<section class="home-services section-pad"><div class="section-heading"><h2>Schilderdiensten in '+escape(place['name'])+'</h2></div>'+cards(True)+'</section>'+serial(section('werkwijze'))
 local+=cta()
 render(route,'Schilder in '+place['name'],place['description'],local,route)
privacy='''<section class="legal-page section-pad section-space"><p class="eyebrow">PRIVACYVERKLARING</p><h1>Zo gaan we om met uw gegevens.</h1><p class="legal-intro">Van Ommen Schilderwerken gebruikt alleen gegevens die nodig zijn om uw vraag of offerteaanvraag te behandelen. Deze verklaring is bijgewerkt op 23 november 2026.</p><h2>Wie is verantwoordelijk?</h2><p>Van Ommen Schilderwerken, Bovendwarsweg 78, 8096 PR Oldebroek, KvK 95415033. Voor privacyvragen, inzage, correctie of verwijdering kunt u mailen naar <a href="mailto:info@vanommenschilderwerken.nl">info@vanommenschilderwerken.nl</a>.</p><h2>Welke gegevens verwerken we?</h2><p>Bij een offerteaanvraag verwerken we uw naam, e-mailadres, telefoonnummer, woonplaats en de gewenste werkzaamheden. De aanvraag wordt op de website bewaard en per e-mail naar Van Ommen Schilderwerken gestuurd. U ontvangt een bevestiging per e-mail. Tegen misbruik van het formulier zet de website een spamcontrole van Cloudflare (Turnstile) in en bewaart zij tijdelijk een versleutelde afgeleide van uw IP-adres. Als u belt, mailt of WhatsApp gebruikt, verwerken de betrokken communicatiediensten uw gegevens volgens hun eigen privacybeleid.</p><h2>Waarom verwerken we deze gegevens?</h2><p>We gebruiken de gegevens om uw aanvraag te behandelen, contact met u op te nemen, het werk te bespreken en afspraken vast te leggen. De verwerking is nodig om op uw verzoek stappen te nemen vóór een mogelijke overeenkomst en voor het gerechtvaardigde belang om aanvragen te beantwoorden en de website veilig en bruikbaar te houden.</p><h2>Hosting en e-mail</h2><p>De website en de opgeslagen aanvragen draaien bij Cloudflare. De e-mails naar u en naar Van Ommen Schilderwerken worden bezorgd via de e-mailverzenddienst Resend; daarvoor ontvangt Resend uw naam, e-mailadres en de inhoud van de aanvraag.</p><h2>Metingen zonder cookies</h2><p>De website telt alleen geaggregeerde acties, zoals een paginaweergave of klik op bellen, WhatsApp of het offerteformulier. Daarbij worden geen analyse- of advertentiecookies geplaatst en geen bezoekersprofielen of unieke bezoekers opgeslagen. De rapportage toont aantallen per dag en pagina en kan herhaalde of automatische bezoeken bevatten.</p><h2>Bewaren en beveiligen</h2><p>Aanvragen op de website bewaren we maximaal twaalf maanden; e-mails bewaren we zolang dat nodig is om uw aanvraag en een eventuele opdracht af te handelen, en daarna volgens de wettelijke bewaartermijnen. De afgeleide van uw IP-adres voor de spamcontrole wordt na twee uur verwijderd. Geaggregeerde websitemetingen worden opgeschoond zodra ze ouder zijn dan veertien maanden.</p><h2>Uw rechten</h2><p>U kunt vragen om inzage, correctie, verwijdering of beperking van uw persoonsgegevens. Ook kunt u bezwaar maken tegen een verwerking. Mail daarvoor naar het bovenstaande adres. U kunt daarnaast een klacht indienen bij de Autoriteit Persoonsgegevens.</p><h2>Externe links</h2><p>Links naar WhatsApp, Instagram en Facebook brengen u naar een andere dienst. Vanaf dat moment geldt het privacy- en cookiebeleid van die dienst.</p></section>'''
render('/privacy/','Privacyverklaring','Lees welke persoonsgegevens Van Ommen Schilderwerken verwerkt bij contact- en offerteaanvragen en hoe u uw privacyrechten kunt gebruiken.',privacy,'',indexable=True)
thanks='''<section class="thank-you-page section-pad section-space"><p class="eyebrow">AANVRAAG VERSTUURD</p><h1>Bedankt voor uw aanvraag.</h1><p>Uw aanvraag is bij Stef binnen en u ontvangt een bevestiging op het ingevulde e-mailadres. Stef neemt contact met u op om het werk te bespreken. Ziet u geen bevestiging? Kijk in uw spammap of bel <a href="tel:+31624996700">06 24 99 67 00</a>.</p><div class="thank-you-actions"><a class="button" href="/projecten/">Bekijk onze projecten</a><a class="text-link" href="/">Terug naar de homepage</a></div></section>'''
render('/bedankt/offerte/','Aanvraag verstuurd','Uw offerteaanvraag bij Van Ommen Schilderwerken is ontvangen. Stef neemt contact met u op.',thanks,'/contact/',indexable=False)
not_found='''<section class="not-found-page section-pad section-space"><p class="eyebrow">PAGINA NIET GEVONDEN</p><h1>Hier hoeft geen verf overheen.</h1><p>De pagina bestaat niet meer of het adres is niet helemaal goed. Ga terug naar de homepage, bekijk het schilderwerk of neem direct contact op.</p><div class="thank-you-actions"><a class="button" href="/">Naar de homepage</a><a class="text-link" href="/contact/">Contact met Stef</a></div></section>'''
render('/404/','Pagina niet gevonden','Deze pagina bestaat niet. Ga terug naar Van Ommen Schilderwerken of neem contact op met Stef.',not_found,'',indexable=False)
# Sitemap-pagina voor bezoekers en Google: alle openbare pagina's in groepen, uit dezelfde lijsten als sitemap.xml.
def _lijst(items):return '<ul class="sitemap-lijst">'+''.join(f'<li><a href="{r}">{escape(t)}</a></li>' for r,t in items)+'</ul>'
_titels=dict((r,t) for r,t,_ in LLMS_PAGES)
_groepen=[
 ('Algemeen',[('/','Home'),('/diensten/','Diensten'),('/projecten/','Projecten'),('/over-ons/','Over ons'),('/contact/','Contact'),('/offerte/','Offerte aanvragen'),('/privacy/','Privacyverklaring')]),
 ('Diensten',[(service_url(v),v['name']) for v in services]),
 ('Projecten',[('/projecten/'+pp['slug']+'/',pp['titel']) for pp in PROJECTPAGINAS]),
 ('Werkgebied',[('/'+pl['slug']+'/','Schilder '+pl['name']) for pl in LOCATIONS]),
 ('Documenten',[(VOORWAARDEN['consument'],'Algemene voorwaarden consument (pdf)'),(VOORWAARDEN['zakelijk'],'Algemene voorwaarden zakelijk (pdf)')]),
]
sitemap_html='<section class="legal-page sitemap-page section-pad section-space"><p class="eyebrow">OVERZICHT</p><h1>Sitemap</h1><p class="legal-intro">Alle pagina’s van Van Ommen Schilderwerken op een rij.</p>'+''.join('<h2>'+escape(k)+'</h2>'+_lijst(v) for k,v in _groepen)+'</section>'
render('/sitemap/','Sitemap','Overzicht van alle pagina’s van Van Ommen Schilderwerken: diensten, projecten, werkgebied en contact.',sitemap_html,'/sitemap/')
(OUT/'_headers').write_text('''/*
  Strict-Transport-Security: max-age=31536000
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: SAMEORIGIN
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; font-src 'self'; style-src 'self'; script-src 'self' https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'
  Cache-Control: public, max-age=0, must-revalidate
/assets/*
  Cache-Control: public, max-age=604800
/style.css
  Cache-Control: public, max-age=3600, must-revalidate
/app.js
  Cache-Control: public, max-age=3600, must-revalidate
/llms.txt
  Content-Type: text/plain; charset=utf-8
/robots.txt
  Content-Type: text/plain; charset=utf-8
/sitemap.xml
  Content-Type: application/xml; charset=utf-8
/voorwaarden/*
  Content-Type: application/pdf
  Content-Disposition: inline
  Cache-Control: public, max-age=86400
''')
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(ORIGIN+r)+'</loc><lastmod>'+UPDATED+'</lastmod></url>' for r in ROUTES)+'</urlset>\n')
(OUT/'robots.txt').write_text(''.join(f'User-agent: {bot}\nAllow: /\n\n' for bot in ['Googlebot','bingbot','OAI-SearchBot','GPTBot','ChatGPT-User','ClaudeBot','Claude-SearchBot','PerplexityBot','Perplexity-User','Google-Extended','Applebot','*'])+'Sitemap: '+ORIGIN+'/sitemap.xml\n')
(OUT/'llms.txt').write_text('# Van Ommen Schilderwerken\n\n> Schildersbedrijf uit Oldebroek voor woningen, bedrijfspanden en VvE’s, met rechtstreeks contact met eigenaar en schilder Stef van Ommen.\n\n## Bedrijfsgegevens\n\n- Bedrijf: Van Ommen Schilderwerken\n- Eigenaar en aanspreekpunt: Stef van Ommen\n- Vestiging: Bovendwarsweg 78, 8096 PR Oldebroek, Nederland\n- Telefoon: +31 6 24 99 67 00\n- E-mail: info@vanommenschilderwerken.nl\n- KvK: 95415033\n- Erkend leerbedrijf (SBB): ja\n- LinkedIn: https://www.linkedin.com/in/stef-van-ommen-4546003a6/\n- Werkgebied: '+', '.join(p['name'] for p in LOCATIONS[:-1])+' en '+LOCATIONS[-1]['name']+'\n\n## Diensten\n\n- Binnenschilderwerk: muren, plafonds, deuren, kozijnen en trappen.\n- Buitenschilderwerk: kozijnen, deuren en houten geveldelen.\n- Houtrotreparatie: aangetast hout verwijderen, kozijnen herstellen en losse verf en beschadigde plekken beoordelen voordat wordt geschilderd.\n- Onderhoud en renovatie: periodiek onderhoud van bestaand schilderwerk en renovatieschilderwerk bij een verbouwing.\n- Spuitwerk: gladde, egale afwerking zonder kwaststrepen voor deuren, kozijnen en keukenfronten.\n- Behangwerk: oud behang verwijderen, wand voorbereiden en nieuw behang strak aanbrengen.\n- Zakelijk en VvE-schilderwerk: schilderwerk voor bedrijfspanden, VvE’s en appartementencomplexen, met een onderhoudsplan.\n\n## Belangrijk voor klanten\n\nEen prijs hangt af van oppervlakte, ondergrond, voorbereiding, bereikbaarheid en afwerking. Er staan daarom geen verzonnen vaste prijzen online. Een offerteaanvraag is vrijblijvend. Projectfoto’s tonen echt werk van Van Ommen Schilderwerken, maar ieder huis en iedere ondergrond is anders.\n\n## Pagina’s\n'+''.join(f'- [{t}]({ORIGIN+r}): {d}\n' for r,t,d in LLMS_PAGES))
import shutil
(OUT/'voorwaarden').mkdir(exist_ok=True)
for key,href in VOORWAARDEN.items():
 bron=ROOT/'source'/'voorwaarden'/Path(href).name
 if bron.exists():shutil.copyfile(bron,OUT/'voorwaarden'/bron.name)
 else:print(f'LET OP: {bron.relative_to(ROOT)} ontbreekt; de voettekstlink naar de algemene voorwaarden ({key}) geeft een 404 tot het bestand er staat.')
(OUT/'404.html').write_text((OUT/'404/index.html').read_text())  # Cloudflare Pages leest /404.html
print(f'Generated {len(ROUTES)} pages with metadata, structured data and sitemap.')
