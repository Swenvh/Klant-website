from pathlib import Path
from lxml import html
from copy import deepcopy
from urllib.parse import quote
from html import escape
import json
from site_content import SERVICE_COPY, LOCATIONS, HOME_INTRO
from customer_questions import faq_html

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
SEO=json.loads((ROOT/'source/seo-config.json').read_text())
ORIGIN=SEO['origin'].rstrip('/')
ROUTES=[]
PUBLIC_ROUTES=[]
UPDATED='2026-09-28'
IMAGE_MAP=json.loads((OUT/'assets/responsive-images.json').read_text())
assert ORIGIN.startswith('https://'), 'The canonical origin must use HTTPS'
def brand_art(identifier):
 # High-resolution restoration, cached once across routes. The viewport removes
 # blank margins; the filter keeps the approved transparent monochrome treatment.
 return f'''<svg class="brand-lockup" xmlns="http://www.w3.org/2000/svg" viewBox="213 92 1749 572" width="277" height="100" aria-hidden="true" focusable="false"><defs><filter id="{identifier}" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -.2126 -.7152 -.0722 0 1"/></filter></defs><image href="/assets/logo-hd.webp" x="0" y="0" width="2172" height="724" filter="url(#{identifier})"/></svg>'''
base=html.fromstring((ROOT/'source/site-template.html').read_text())
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
slugs=['binnenschilderwerk','buitenschilderwerk','houtwerk-onderhoud','kleur-afwerking','lakwerk','houtrot-kozijnherstel','zakelijk-vve']
# Volgorde op de dienstenpagina: fototegels en teksttegels vormen elk volle rijen; zakelijk & VvE sluit breed af.
ORDER=['binnenschilderwerk','buitenschilderwerk','lakwerk','houtrot-kozijnherstel','houtwerk-onderhoud','kleur-afwerking','zakelijk-vve']
for i,el in enumerate(cls('service')):
 services.append({'name':el.find('.//h3').text,'slug':slugs[i],'text':cls('service-content',el)[0].find('p').text,'tags':[e.text for e in cls('service-tags',el)[0]],'image':['binnenschilderwerk-na.jpeg','buitenschilderwerk-na.jpeg','preparation.jpg','hero.jpg','','',''][i]})
services.sort(key=lambda v:ORDER.index(v['slug']))
nav=[('/', 'Home'),('/diensten/','Diensten'),('/ons-werk/','Ons werk'),('/over-stef/','Over Stef'),('/contact/','Contact')]
linkmap={'#home':'/','#diensten':'/diensten/','#projecten':'/ons-werk/','#over':'/over-stef/','#werkwijze':'/over-stef/#werkwijze','#contact':'/contact/','#offerte':'/contact/#offerte','#vragen':'/contact/#vragen'}
def service_url(v):return '/diensten/'+v['slug']+'/'
def comparison(kind='interior'):
 filename='before-after-exterior.html' if kind=='exterior' else 'before-after.html'
 return (ROOT/'source'/filename).read_text()

def cta(title='Uw schilderplannen bespreken?'):
 return f'''<section class="page-cta section-pad"><div><p class="eyebrow">PERSOONLIJK CONTACT</p><h2>{title}</h2><p>Vertel Stef wat u wilt laten schilderen. Samen bespreken we de volgende stap.</p></div><div class="cta-actions"><a class="button" href="/contact/#offerte">Offerte Aanvragen</a><a class="text-link" href="tel:+31624996700">Liever bellen? 06 24 99 67 00</a></div></section>'''
def intro(label,title,desc,parent=None):
 parent_link=f'<span aria-hidden="true">/</span><a href="/diensten/">Diensten</a>' if parent else ''
 return f'''<section class="page-intro section-pad"><nav class="breadcrumbs" aria-label="Kruimelpad"><a href="/">Home</a>{parent_link}<span aria-hidden="true">/</span><span aria-current="page">{escape(label)}</span></nav><div class="page-intro-content"><div><p class="eyebrow">VAN OMMEN SCHILDERWERKEN</p><h1>{title}</h1></div><p>{desc}</p></div></section>'''
def cards(compact=False):
 result=[]
 # De homepage toont de vier fotodiensten; de overige staan eronder als tekstlinks.
 shown=[v for v in services if v['image']] if compact else services
 for i,v in enumerate(shown):
  image=f'<img src="/assets/{v["image"]}" alt="{escape(v["name"])} van Van Ommen Schilderwerken" width="800" height="900" loading="lazy">' if v['image'] else ''
  result.append(f'''<a class="service-tile {'has-photo' if image else 'text-tile'}{' tile-wide' if v['slug']=='zakelijk-vve' and not compact else ''}" href="{service_url(v)}"><div class="tile-media">{image}<span class="tile-number">0{i+1}</span><h3>{escape(v['name'])}</h3></div><div class="tile-body"><p>{escape(SERVICE_COPY[v['slug']]['summary'] if compact else v['text'])}</p><span class="tile-link">Meer over {escape(v['name'][0].lower()+v['name'][1:])}</span></div></a>''')
 more=''
 if compact:
  extra=[v for v in services if not v['image']]
  links=[f'<a href="{service_url(v)}">{escape(v["name"][0].lower()+v["name"][1:])}</a>' for v in extra]
  more='<p class="service-more">Ook voor '+', '.join(links[:-1])+' en '+links[-1]+'.</p>'
 return '<div class="service-tiles '+('compact' if compact else '')+'">'+''.join(result)+'</div>'+more
def render(route,title,desc,content,active,home=False,gallery=False,private=False,indexable=True):
 s=deepcopy(base);body=s.find('body');body.set('class','page-home' if home else 'page-inner page-'+active.strip('/').replace('/','-'))
 s.find('.//title').text=title+' | Van Ommen Schilderwerken'
 s.xpath('//meta[@name="description"]')[0].set('content',desc)
 head=s.find('head')
 head.append(html.Element('meta',name='author',content='Van Ommen Schilderwerken'))
 head.append(html.Element('link',rel='preload',attrib={'as':'font','type':'font/ttf','href':'/assets/poppins-400-latin.ttf','crossorigin':'anonymous'}))
 canonical=html.Element('link',rel='canonical',href=ORIGIN+route);head.append(canonical)
 social_image=ORIGIN+'/assets/van-ommen-og.jpg'
 for name,value in [('robots','index, follow, max-image-preview:large' if SEO['indexable'] and indexable and not private else 'noindex, nofollow'),('twitter:card','summary_large_image'),('twitter:image',social_image),('twitter:image:alt','Bedrijfsbus van Van Ommen Schilderwerken'),('twitter:title',title+' | Van Ommen Schilderwerken'),('twitter:description',desc)]:
  head.append(html.Element('meta',name=name,content=value))
 for name,value in [('og:type','website'),('og:locale','nl_NL'),('og:site_name','Van Ommen Schilderwerken'),('og:title',title+' | Van Ommen Schilderwerken'),('og:description',desc),('og:url',ORIGIN+route)]:
  head.append(html.Element('meta',property=name,content=value))
 for name,value in [('og:image',social_image),('og:image:secure_url',social_image),('og:image:type','image/jpeg'),('og:image:width','1600'),('og:image:height','900'),('og:image:alt','Bedrijfsbus van Van Ommen Schilderwerken')]:
  head.append(html.Element('meta',property=name,content=value))
 if SEO.get('google_site_verification'):
  head.append(html.Element('meta',name='google-site-verification',content=SEO['google_site_verification']))
 insert_content(s.get_element_by_id('main'),content)
 if route=='/diensten/':
  for heading in cls('service-tile',s):
   heading.find('.//h3').tag='h2'
 if route.startswith('/diensten/') and route!='/diensten/':
  article=cls('service-article',s)[0]
  article.append(html.fromstring('<p>Bekijk ook <a href="/ons-werk/">onze afgeronde schilderprojecten</a> of lees <a href="/contact/#vragen">veelgestelde vragen over kosten en voorbereiding</a>.</p>'))
 if route in ['/afspraak/','/afspraken-beheer/']:
  script=html.Element('script',src='/appointments.js',defer='');head.append(script)
 if route=='/contact/':
  s.get_element_by_id('main').insert(1,html.fromstring('<section class="appointment-invite section-pad"><div><h2>Liever samen uw woning bekijken?</h2><p>Geef een voorkeursdatum door. Stef stemt de afspraak daarna met u af.</p></div><a class="button" href="/afspraak/">Afspraak aanvragen</a></section>'))
 privacy=s.get_element_by_id('privacy-dialog')
 privacy.find('p').text='Het offerteformulier op de contactpagina maakt een bericht klaar in uw eigen e-mailprogramma. U verstuurt dat zelf. Als u via WhatsApp contact opneemt, verstuurt u uw bericht daar. Het offerteformulier slaat uw gegevens niet op deze website op.'
 privacy.append(html.fromstring('<p>De afsprakenplanner werkt anders: uw naam, contactgegevens, adres, voorkeursmoment en toelichting worden op de website opgeslagen om uw aanvraag te behandelen. Alleen de bevoegde beheerder kan deze aanvragen bekijken. Als de beheerder een bevestigingsmail verstuurt, worden uw e-mailadres, naam en afspraakgegevens doorgegeven aan de e-mailverzenddienst Resend. Voor inzage, wijziging of verwijdering kunt u contact opnemen via info@vanommenschilderwerken.nl.</p>'))
 privacy.append(html.fromstring('<p>De website gebruikt geen analyse- of advertentiecookies. Alleen anonieme totaaltellingen per pagina en actie worden bewaard, zonder IP-adres, gebruikersprofiel of unieke bezoeker.</p>'))
 for i,brand in enumerate(cls('brand',s)):
  insert_content(brand,brand_art(f'brand-ink-{i}'))
  brand.set('class',brand.get('class')+' brand-integrated')
 for nav_class in ['desktop-nav','mobile-nav']:
  n=cls(nav_class,s)[0]
  links=''.join(f'<a href="{url}"'+(' aria-current="page"' if url==active or (active.startswith('/diensten/') and url=='/diensten/') else '')+f'>{label}</a>' for url,label in nav)
  if nav_class=='mobile-nav':links+='<a href="tel:+31624996700">Bel Stef: 06 24 99 67 00</a>'
  insert_content(n,links)
 toggle=cls('menu-toggle',s)[0]
 menu_label=html.Element('b',attrib={'class':'menu-label'});menu_label.text='Menu';toggle.insert(0,menu_label)
 for a in s.xpath('//a[@href]'):
  href=a.get('href')
  if href in linkmap:a.set('href',linkmap[href])
  if a.get('data-service'):
   a.set('href','/contact/?dienst='+quote(a.get('data-service'))+'#offerte')
  if 'brand' in a.get('class',''):a.set('aria-label','Van Ommen Schilderwerken, naar de homepage')
 # Keep the scroll-to-top action local on every page.
 for a in cls('footer-bottom',s)[0].findall('a'):a.set('href','#home')
 footer=cls('footer',s)[0]
 footer.insert(1,html.fromstring('<div class="footer-columns"><nav aria-label="Navigatie onderaan"><h2>Op deze website</h2>'+''.join(f'<a href="{url}">{label}</a>' for url,label in nav)+'<a href="/contact/#vragen">Veelgestelde vragen</a></nav><nav aria-label="Snelle links"><h2>Snelle links</h2>'+''.join(f'<a href="/{place["slug"]}/">Schilder {place["name"]}</a>' for place in LOCATIONS)+''.join(f'<a href="{service_url(v)}">{escape(v["name"])}</a>' for v in services)+'</nav><div class="footer-contact"><h2>Neem contact op</h2><a href="tel:+31624996700">06 24 99 67 00</a><a href="mailto:info@vanommenschilderwerken.nl">info@vanommenschilderwerken.nl</a><address>Bovendwarsweg 78<br>8096 PR Oldebroek</address><a href="/contact/#offerte">Offerte aanvragen</a></div></div>'))
 privacy_button=footer.xpath('.//*[@data-privacy]')
 if privacy_button:
  privacy_button[0].tag='a';privacy_button[0].text='Privacy';privacy_button[0].set('href','/privacy/');privacy_button[0].attrib.pop('data-privacy',None)
 footer_bottom=cls('footer-bottom',s)[0]
 footer_bottom.insert(-1,html.fromstring('<a href="/websitevoorwaarden/">Websitevoorwaarden</a>'))
 person={'@type':'Person','@id':ORIGIN+'/over-stef/#stef','name':'Stef van Ommen','jobTitle':'Eigenaar en schilder','url':ORIGIN+'/over-stef/','worksFor':{'@id':ORIGIN+'/#bedrijf'}}
 offer_catalog={'@type':'OfferCatalog','name':'Schilderdiensten voor woningen','itemListElement':[{'@type':'Offer','itemOffered':{'@type':'Service','name':v['name'],'url':ORIGIN+service_url(v)}} for v in services]}
 business={'@type':'HousePainter','@id':ORIGIN+'/#bedrijf','name':'Van Ommen Schilderwerken','description':'Schildersbedrijf uit Oldebroek voor binnen- en buitenschilderwerk, lakwerk, houtrotherstel en kozijnreparatie, houtonderhoud, kleur en afwerking. Voor woningen, bedrijfspanden en VvE’s, ook met een onderhoudsplan.','url':ORIGIN+'/','telephone':'+31624996700','email':'info@vanommenschilderwerken.nl','logo':ORIGIN+'/assets/logo-hd.webp','image':ORIGIN+'/assets/buitenschilderwerk-na.jpeg','founder':{'@id':person['@id']},'contactPoint':{'@type':'ContactPoint','contactType':'customer service','telephone':'+31624996700','email':'info@vanommenschilderwerken.nl','availableLanguage':'nl'},'hasOfferCatalog':offer_catalog,'address':{'@type':'PostalAddress','streetAddress':'Bovendwarsweg 78','postalCode':'8096 PR','addressLocality':'Oldebroek','addressCountry':'NL'},'areaServed':[{'@type':'City','name':p['name']} for p in LOCATIONS],'sameAs':['https://www.instagram.com/vanommenschilderwerken/','https://www.facebook.com/61586685635291/']}
 webpage={'@type':'WebPage','@id':ORIGIN+route+'#pagina','url':ORIGIN+route,'name':title,'description':desc,'inLanguage':'nl-NL','dateModified':UPDATED,'isPartOf':{'@id':ORIGIN+'/#website'},'about':{'@id':ORIGIN+'/#bedrijf'}}
 graph=[business,person,{'@type':'WebSite','@id':ORIGIN+'/#website','url':ORIGIN+'/','name':'Van Ommen Schilderwerken','inLanguage':'nl-NL','publisher':{'@id':ORIGIN+'/#bedrijf'}},webpage]
 crumbs=cls('breadcrumbs',s)
 if crumbs:
  items=[]
  for el in crumbs[0].xpath('./a | ./span[@aria-current="page"]'):
   items.append({'@type':'ListItem','position':len(items)+1,'name':el.text_content(),'item':ORIGIN+(el.get('href') or route)})
  graph.append({'@type':'BreadcrumbList','itemListElement':items})
 if route.startswith('/diensten/') and route!='/diensten/':
  graph.append({'@type':'Service','name':title,'url':ORIGIN+route,'provider':{'@id':ORIGIN+'/#bedrijf'},'areaServed':business['areaServed']})
 place=next((p for p in LOCATIONS if route=='/'+p['slug']+'/'),None)
 if place:
  graph.append({'@type':'Service','@id':ORIGIN+route+'#dienst','name':'Schilderwerk in '+place['name'],'serviceType':'Binnen- en buitenschilderwerk','url':ORIGIN+route,'provider':{'@id':ORIGIN+'/#bedrijf'},'areaServed':{'@type':'City','name':place['name']}})
 questions=[]
 for detail in s.xpath('//main//details[summary and .//p]'):
  question=' '.join(detail.find('summary').text_content().split())
  answer=' '.join(detail.find('.//p').text_content().split())
  if question and answer:questions.append({'@type':'Question','name':question,'acceptedAnswer':{'@type':'Answer','text':answer}})
 if questions:graph.append({'@type':'FAQPage','@id':ORIGIN+route+'#veelgestelde-vragen','mainEntity':questions})
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
    img.set('src',info['variants'][-1]['src'])
 if not gallery:
  dialog=s.get_element_by_id('photo-dialog');dialog.getparent().remove(dialog)
 if not private:
  footer_nav=footer.xpath('.//nav[@aria-label="Navigatie onderaan"]')[0]
  footer_nav.append(html.fromstring('<a href="/afspraak/">Afspraak aanvragen</a>'))
 destination=OUT/'.openai/admin-page.html' if private else OUT/route.strip('/')/'index.html' if route!='/' else OUT/'index.html'
 destination.parent.mkdir(parents=True,exist_ok=True)
 destination.write_text('<!doctype html>\n'+serial(s))
 if not private:
  PUBLIC_ROUTES.append(route)
  if indexable:ROUTES.append(route)

hero_element=deepcopy(cls('hero')[0])
hero_element.xpath('.//div[@class="hero-content"]/p[not(@class)]')[0].text='Geef uw woning een frisse uitstraling. Verzorgd schilderwerk, binnen en buiten.'
for br in hero_element.xpath('.//div[@class="hero-content"]/p[not(@class)]/br'):
 br.getparent().remove(br)
hero=serial(hero_element)
featured='''<section class="featured-work section-pad"><div class="featured-photo featured-after"><img src="/assets/binnenschilderwerk-na.jpeg" alt="Het resultaat van binnenschilderwerk: lichte wanden, een afgewerkte kast en witte plinten" width="957" height="1536" loading="lazy"><span>HET RESULTAAT / BINNENSCHILDERWERK</span></div><div class="featured-copy"><p class="eyebrow">VOOR & NA</p><h2>Een frisse blik.<br>Een zichtbaar verschil.</h2><p>Van de voorbereiding tot de laatste afwerking. Bekijk hoe deze ruimte is opgefrist met verzorgd binnenschilderwerk.</p><a class="button button-outline" href="/ons-werk/#voor-na">Bekijk voor & na </a></div></section>'''
HOME_INTRO+='<section class="appointment-invite section-pad"><div><h2>Uw plannen samen bespreken?</h2><p>Vraag een afspraak aan om uw woning en het schilderwerk te bekijken.</p></div><a class="button" href="/afspraak/">Afspraak aanvragen</a></section>'

home=hero+HOME_INTRO+'''<section class="home-services section-pad"><div class="section-heading"><div><p class="eyebrow">WAT WILT U LATEN SCHILDEREN?</p><h2>Mooi van binnen.<br>Verzorgd van buiten.</h2></div><a class="text-link" href="/diensten/">Bekijk alle diensten</a></div>'''+cards(True)+'</section>'+featured+serial(section('werkwijze'))+faq_html(compact=True)+cta()
render('/','Schilder in Oldebroek en Wezep','Uw woning opfrissen? Van Ommen Schilderwerken uit Oldebroek verzorgt binnen- en buitenschilderwerk. Bekijk ons werk of bespreek uw wensen met Stef.',home,'/',home=True)
content=intro('Diensten','Schilderwerk dat<br>bij uw woning past.','Binnen of buiten, nieuw schilderwerk of onderhoud: kies de werkzaamheden waar u meer over wilt weten.')+'<section class="services-overview section-pad">'+cards()+'</section>'+cta()
render('/diensten/','Onze diensten','Binnen- en buitenschilderwerk, onderhoud en kleurkeuze. Ontdek de diensten van Van Ommen Schilderwerken.',content,'/diensten/')
for v in services:
 side='<aside class="service-sidebar"><p class="eyebrow">ONZE DIENSTEN</p><nav aria-label="Diensten">'+''.join(f'<a href="{service_url(x)}"'+(' aria-current="page"' if x==v else '')+'>'+escape(x['name'])+'</a>' for x in services)+'</nav><div class="sidebar-contact"><p>Even overleggen?</p><a href="tel:+31624996700">Bel Stef<br><strong>06 24 99 67 00</strong></a></div></aside>'
 request='/contact/?dienst='+quote(v['name'])+'#offerte'
 tags=''.join('<li>'+escape(t)+'</li>' for t in v['tags'])
 detail=f'''<article class="service-article"><p class="eyebrow">AANDACHT VOOR UW WONING</p><h2>{escape(v['name'])}</h2><p class="article-lead">{escape(v['text'])}</p><h3>Wat kunnen we bespreken?</h3><ul class="scope-list">{tags}</ul><h3>Een aanpak voor uw situatie</h3><p>De staat van de ondergrond en uw wensen bepalen wat nodig is. We bekijken het werk, bespreken de voorbereiding en stemmen de afwerking en planning met u af.</p><p>Vertel ons wat u wilt laten doen. Met een korte beschrijving en enkele foto’s krijgen we een eerste beeld. Daarna bespreken we de volgende stap.</p><div class="article-actions"><a class="button" href="{request}">Vraag een offerte aan </a><a class="text-link" href="/over-stef/#werkwijze">Bekijk onze werkwijze</a></div></article>'''
 copy=SERVICE_COPY[v['slug']]
 detail=detail.replace('<h3>Een aanpak voor uw situatie</h3>','<h3>'+escape(copy['heading'])+'</h3><p>'+escape(copy['paragraph'])+'</p><h3>Wat spreken we vooraf af?</h3><p>'+escape(copy['preparation'])+'</p><h3>'+escape(copy['question'])+'</h3><p>'+escape(copy['answer'])+'</p><h3>Een offerte voor uw woning</h3>')
 compare=comparison() if v['slug']=='binnenschilderwerk' else comparison('exterior') if v['slug']=='buitenschilderwerk' else ''
 content=intro(v['name'],escape(v['name']).replace(' &amp; ',' &amp;<br>'),'Persoonlijk contact, een zorgvuldige voorbereiding en aandacht voor de afwerking.',True)+'<section class="service-detail section-pad">'+detail+side+'</section>'+compare+cta()
 render(service_url(v),v['name']+' in Oldebroek en Wezep',v['text'],content,'/diensten/')
projects=section('projecten')
projects.set('class',projects.get('class')+' work-page-gallery')
content=intro('Ons werk','Van voorbereiding<br>tot eindresultaat.','Bekijk het verschil voor en na bij binnen- en buitenschilderwerk, en ontdek de details van ons werk.')+comparison()+comparison('exterior')+serial(projects)+cta('Ook uw woning laten schilderen?')
render('/ons-werk/','Ons werk','Bekijk echte foto’s van het schilderwerk van Van Ommen Schilderwerken, van voorbereiding tot afwerking.',content,'/ons-werk/',gallery=True)
about=section('over');cls('intro-text',about)[0].text='Goed schilderwerk begint met persoonlijk contact.'
facts='''<section class="company-facts section-pad section-space" aria-labelledby="facts-title"><div><p class="eyebrow">IN ÉÉN OOGOPSLAG</p><h2 id="facts-title">Wie komt er bij u schilderen?</h2><p>Feiten over het bedrijf, zodat u vooraf weet met wie u contact heeft.</p></div><dl><div><dt>Bedrijf</dt><dd>Van Ommen Schilderwerken</dd></div><div><dt>Aanspreekpunt</dt><dd>Stef van Ommen, eigenaar en schilder</dd></div><div><dt>Vestigingsplaats</dt><dd>Oldebroek</dd></div><div><dt>Werkgebied</dt><dd>Oldebroek, Wezep, Zwolle, Elburg en Nunspeet</dd></div><div><dt>Diensten</dt><dd>Binnen- en buitenschilderwerk, lakwerk, houtrotherstel en kozijnreparatie, houtonderhoud, kleur en afwerking, zakelijk en VvE-schilderwerk met onderhoudsplan</dd></div><div><dt>Contact</dt><dd><a href="tel:+31624996700">06 24 99 67 00</a> · <a href="mailto:info@vanommenschilderwerken.nl">info@vanommenschilderwerken.nl</a></dd></div></dl></section>'''
content=intro('Over Stef','Aangenaam.<br>Stef van Ommen.','Uw aanspreekpunt voor schilderwerk vanuit Oldebroek. We maken samen duidelijke afspraken over uw woning en uw wensen.')+serial(about)+facts+serial(section('werkwijze'))+cta('Kennismaken en uw plannen bespreken?')
render('/over-stef/','Over Stef & onze werkwijze','Maak kennis met Stef van Ommen en lees hoe Van Ommen Schilderwerken uw schilderwerk aanpakt.',content,'/over-stef/')
contact=section('contact')
form=cls('quote-form',contact)[0]
form.find('h3').tag='h2'
form.find('h2').text='Vraag een offerte aan'
form.find('p').text='Vertel wat u wilt laten schilderen en waar uw woning staat. U hoeft geen maten of kleurnummers te weten. De knop maakt een e-mail klaar die u zelf nog verstuurt. Velden met een * zijn verplicht.'
form.xpath('.//button[@type="submit"]')[0].text='Verder in mijn e-mailprogramma'
form.xpath('.//select[@name="service"]/option[last()]')[0].text='Meerdere werkzaamheden / ik weet het nog niet'
cls('form-status',form)[0].text='Uw aanvraag is nog niet verstuurd. Verstuur de klaargezette e-mail in uw e-mailprogramma. Opent er niets? Bel 06 24 99 67 00 of mail naar info@vanommenschilderwerken.nl.'
note=cls('form-note',form)[0]
insert_content(note,'Foto’s zijn handig, maar niet verplicht. Voeg ze toe in uw e-mail. Uw bericht geeft uw wensen door; het is nog geen opdracht om te schilderen. Lees hoe we met uw gegevens omgaan in de <a href="/privacy/">privacyverklaring</a>.')
form.append(html.fromstring('<div class="quote-help"><p>Geen e-mailprogramma ingesteld?</p><a class="text-link" id="quote-whatsapp" href="https://wa.me/31624996700" target="_blank" rel="noopener noreferrer">Bespreek uw wensen via WhatsApp</a><p>U kunt ook bellen: <a href="tel:+31624996700">06 24 99 67 00</a>.</p></div>'))
form.insert(2,html.fromstring('<ol class="quote-next-steps" aria-label="Zo vraagt u een offerte aan"><li>Vul uw wensen in.</li><li>Verstuur de klaargezette e-mail.</li><li>Bespreek met Stef het werk en de offerte.</li></ol>'))
content=intro('Contact','Uw woning opfrissen?<br>Bespreek het met Stef.','Bel voor overleg, stuur uw wensen per e-mail of WhatsApp, of vraag een afspraak aan om het schilderwerk te bekijken.')+serial(contact)+faq_html()
render('/contact/','Contact & offerte','Neem contact op met Stef van Ommen voor uw schilderwerk. Bel 06 24 99 67 00 of stel een offerteaanvraag op.',content,'/contact/')
for place in LOCATIONS:
 route='/'+place['slug']+'/'
 questions=''.join('<details><summary>'+escape(q)+'<span class="plus" aria-hidden="true"></span></summary><p>'+escape(a)+'</p></details>' for q,a in place['questions'])
 local=intro('Schilder '+place['name'],'Schilder in '+place['name'],escape(place['intro']))
 local+='<section class="local-story section-pad section-space"><article><h2>'+escape(place['heading'])+'</h2><p>'+escape(place['text'])+'</p><h3>'+escape(place['focus'])+'</h3><p>'+escape(place['focus_text'])+'</p><div class="article-actions"><a class="button" href="/contact/#offerte">Offerte Aanvragen</a><a class="text-link" href="tel:+31624996700">Bel Stef: 06 24 99 67 00</a></div></article><figure><img src="/assets/'+place['image']+'" alt="'+escape(place['alt'])+'" width="900" height="1200" loading="lazy"><figcaption>Een voorbeeld van ons schilderwerk. <a href="/ons-werk/">Bekijk de foto’s voor en na</a>.</figcaption></figure></section>'
 local+='<section class="home-services section-pad"><div class="section-heading"><h2>Wat wilt u vernieuwen?</h2></div>'+cards(True)+'</section>'+serial(section('werkwijze'))
 local+='<section class="faq section-pad section-space"><div><p class="eyebrow">UW VRAGEN</p><h2>Schilderwerk in '+place['name']+'</h2><p><a class="text-link" href="/contact/#vragen">Meer over kosten, voorbereiding en planning</a></p></div><div class="faq-list">'+questions+'</div></section>'+cta()
 render(route,'Schilder '+place['name']+' voor binnen en buiten',place['description'],local,route)
content=intro('Afspraak aanvragen','Wanneer komt<br>het u uit?','Kies een voorkeursmoment om uw schilderwensen te bespreken. Stef stemt de definitieve afspraak met u af.')+(ROOT/'source/appointment.html').read_text()
render('/afspraak/','Afspraak aanvragen','Vraag een afspraak aan om uw schilderwerk te bespreken. Kies uw voorkeursdatum en dagdeel. Stef bevestigt het moment persoonlijk.',content,'/contact/')
privacy='''<section class="legal-page section-pad section-space"><p class="eyebrow">PRIVACYVERKLARING</p><h1>Zo gaan we om met uw gegevens.</h1><p class="legal-intro">Van Ommen Schilderwerken gebruikt alleen gegevens die nodig zijn om uw vraag of afspraak te behandelen. Deze verklaring is bijgewerkt op 28 september 2026.</p><h2>Wie is verantwoordelijk?</h2><p>Van Ommen Schilderwerken, Bovendwarsweg 78, 8096 PR Oldebroek, KvK 95415033. Voor privacyvragen, inzage, correctie of verwijdering kunt u mailen naar <a href="mailto:info@vanommenschilderwerken.nl">info@vanommenschilderwerken.nl</a>.</p><h2>Welke gegevens verwerken we?</h2><p>Bij een afspraakaanvraag verwerken we uw naam, e-mailadres, telefoonnummer, adres, woonplaats, gewenste werkzaamheden, voorkeursmoment en eventuele toelichting. Het offerteformulier opent een bericht in uw eigen e-mailprogramma; de website slaat die formulierinhoud niet op. Als u belt, mailt of WhatsApp gebruikt, verwerken de betrokken communicatiediensten uw gegevens volgens hun eigen privacybeleid.</p><h2>Waarom verwerken we deze gegevens?</h2><p>We gebruiken de gegevens om uw aanvraag te behandelen, contact met u op te nemen, het werk te bespreken en afspraken vast te leggen. De verwerking is nodig om op uw verzoek stappen te nemen vóór een mogelijke overeenkomst en voor het gerechtvaardigde belang om aanvragen te beantwoorden en de website veilig en bruikbaar te houden.</p><h2>Bevestigingsmail en hosting</h2><p>De website en afspraakgegevens worden technisch verwerkt via de hostingomgeving van de website. Als de bevestigingsmail wordt geactiveerd en Stef een afspraak bevestigt, gaan uw naam, e-mailadres en afspraakgegevens naar e-mailverzenddienst Resend om het bericht te bezorgen. Deze koppeling is nog niet actief zolang geen geverifieerd afzenderadres is ingesteld.</p><h2>Metingen zonder cookies</h2><p>De website telt alleen geaggregeerde acties, zoals een paginaweergave of klik op bellen, WhatsApp, offerte of afspraak. Daarbij worden geen analyse- of advertentiecookies geplaatst en geen bezoekersprofielen of unieke bezoekers opgeslagen. De rapportage toont aantallen per dag en pagina en kan herhaalde of automatische bezoeken bevatten.</p><h2>Bewaren en beveiligen</h2><p>We hanteren een bewaartermijn van twaalf maanden na de laatste wijziging voor afspraakaanvragen en bijbehorende bevestigingsgegevens. Oudere gegevens worden bij een volgende aanvraag of beheercontrole automatisch opgeschoond. Geaggregeerde websitemetingen worden op dezelfde momenten opgeschoond zodra ze ouder zijn dan veertien maanden. De beheerpagina is afgeschermd en alleen beschikbaar voor de aangewezen beheerder.</p><h2>Uw rechten</h2><p>U kunt vragen om inzage, correctie, verwijdering of beperking van uw persoonsgegevens. Ook kunt u bezwaar maken tegen een verwerking. Mail daarvoor naar het bovenstaande adres. U kunt daarnaast een klacht indienen bij de Autoriteit Persoonsgegevens.</p><h2>Externe links</h2><p>Links naar WhatsApp, Instagram en Facebook brengen u naar een andere dienst. Vanaf dat moment geldt het privacy- en cookiebeleid van die dienst.</p></section>'''
render('/privacy/','Privacyverklaring','Lees welke persoonsgegevens Van Ommen Schilderwerken verwerkt bij contact- en afspraakaanvragen en hoe u uw privacyrechten kunt gebruiken.',privacy,'',indexable=True)
terms='''<section class="legal-page section-pad section-space"><p class="eyebrow">WEBSITEVOORWAARDEN</p><h1>Duidelijkheid over deze website.</h1><p class="legal-intro">Deze voorwaarden gaan over het gebruik van de website. De afspraken over een schilderopdracht staan altijd in de offerte of opdrachtbevestiging. Bijgewerkt op 28 september 2026.</p><h2>Informatie en aanvragen</h2><p>De website geeft algemene informatie over diensten en werkwijze. Een offerte- of afspraakaanvraag is vrijblijvend en is nog geen overeenkomst voor schilderwerk. Een afspraak staat pas vast nadat Stef de definitieve datum en tijd persoonlijk of per bevestigingsmail heeft bevestigd.</p><h2>Offerte en uitvoering</h2><p>De omvang van het werk, voorbereiding, materialen, planning, prijs, betaling en eventuele aanvullende afspraken worden per opdracht vastgelegd. Bij verschil tussen deze website en een schriftelijke offerte of opdrachtbevestiging geldt het schriftelijke document.</p><h2>Foto's en voorbeelden</h2><p>Projectfoto’s en voor-en-naresultaten laten voorbeelden zien. Iedere woning, ondergrond en opdracht is anders; aan een voorbeeld kan daarom geen identiek resultaat, vaste prijs of vaste doorlooptijd worden ontleend.</p><h2>Beschikbaarheid</h2><p>We onderhouden de website zorgvuldig, maar kunnen niet beloven dat deze altijd zonder onderbreking beschikbaar is. Lukt een formulier niet, neem dan contact op via telefoon of e-mail.</p><h2>Intellectuele eigendom</h2><p>De teksten, vormgeving, het logo en eigen beeldmateriaal op deze website mogen niet zonder voorafgaande toestemming worden gekopieerd of commercieel gebruikt, behalve voor zover de wet dat toestaat.</p><h2>Externe diensten</h2><p>De website bevat links naar onder meer WhatsApp, Instagram en Facebook. Van Ommen Schilderwerken beheert deze diensten niet en is niet verantwoordelijk voor hun inhoud of beschikbaarheid.</p><h2>Contact</h2><p>Heeft u een vraag over deze website of de voorwaarden? Neem contact op via <a href="mailto:info@vanommenschilderwerken.nl">info@vanommenschilderwerken.nl</a> of <a href="tel:+31624996700">06 24 99 67 00</a>.</p></section>'''
render('/websitevoorwaarden/','Websitevoorwaarden','Lees de voorwaarden voor het gebruik van de website van Van Ommen Schilderwerken en het verschil tussen een aanvraag en een opdracht.',terms,'',indexable=True)
thanks='''<section class="thank-you-page section-pad section-space"><p class="eyebrow">AANVRAAG OPGESLAGEN</p><h1>Bedankt voor uw aanvraag.</h1><p>Uw voorkeursmoment is ontvangen. Stef neemt persoonlijk contact met u op om de datum en tijd af te stemmen. De afspraak staat nog niet definitief in de agenda.</p><div class="thank-you-actions"><a class="button" href="/">Terug naar de homepage</a><a class="text-link" href="tel:+31624996700">Liever bellen? 06 24 99 67 00</a></div><p class="field-help">Geen bevestiging gezien of wilt u iets wijzigen? Neem contact op met uw naam en de aangevraagde datum.</p></section>'''
render('/bedankt/afspraak/','Afspraakaanvraag ontvangen','Uw afspraakaanvraag bij Van Ommen Schilderwerken is opgeslagen. Stef neemt contact met u op om het moment af te stemmen.',thanks,'',indexable=False)
not_found='''<section class="not-found-page section-pad section-space"><p class="eyebrow">PAGINA NIET GEVONDEN</p><h1>Hier hoeft geen verf overheen.</h1><p>De pagina bestaat niet meer of het adres is niet helemaal goed. Ga terug naar de homepage, bekijk het schilderwerk of neem direct contact op.</p><div class="thank-you-actions"><a class="button" href="/">Naar de homepage</a><a class="text-link" href="/contact/">Contact met Stef</a></div></section>'''
render('/404/','Pagina niet gevonden','Deze pagina bestaat niet. Ga terug naar Van Ommen Schilderwerken of neem contact op met Stef.',not_found,'',indexable=False)
content=intro('Aanvragen beheren','Afspraakaanvragen','Bekijk nieuwe aanvragen en houd bij welke afspraken u met klanten heeft afgestemd.')+(ROOT/'source/appointment-admin.html').read_text()
render('/afspraken-beheer/','Aanvragen beheren','Afgeschermd beheer van afspraakaanvragen.',content,'/contact/',private=True)
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(ORIGIN+r)+'</loc><lastmod>'+UPDATED+'</lastmod></url>' for r in ROUTES)+'</urlset>\n')
(OUT/'robots.txt').write_text('User-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: Googlebot\nAllow: /\n\nUser-agent: bingbot\nAllow: /\n\nUser-agent: *\nAllow: /\n\nSitemap: '+ORIGIN+'/sitemap.xml\n')
(OUT/'llms.txt').write_text('# Van Ommen Schilderwerken\n\n> Schildersbedrijf uit Oldebroek voor woningen, bedrijfspanden en VvE’s, met rechtstreeks contact met eigenaar en schilder Stef van Ommen.\n\n## Bedrijfsgegevens\n\n- Bedrijf: Van Ommen Schilderwerken\n- Eigenaar en aanspreekpunt: Stef van Ommen\n- Vestiging: Bovendwarsweg 78, 8096 PR Oldebroek, Nederland\n- Telefoon: +31 6 24 99 67 00\n- E-mail: info@vanommenschilderwerken.nl\n- KvK: 95415033\n- Werkgebied: Oldebroek, Wezep, Zwolle, Elburg en Nunspeet\n\n## Diensten\n\n- Binnenschilderwerk: muren, plafonds, deuren, kozijnen en trappen.\n- Buitenschilderwerk: kozijnen, deuren en houten geveldelen.\n- Houtwerk en onderhoud: beoordeling van losse verf en beschadigde plekken voordat wordt geschilderd.\n- Kleur en afwerking: hulp bij kleurkeuze en het kiezen van een passende afwerking.\n- Lakwerk: slijtvaste afwerking van deuren, kozijnen, trappen en leuningen.\n- Houtrotherstel en kozijnreparatie: aangetast hout verwijderen en kozijnen herstellen voordat wordt geschilderd.\n- Zakelijk en VvE-schilderwerk: schilderwerk voor bedrijfspanden, VvE’s en appartementencomplexen, met een onderhoudsplan.\n\n## Belangrijk voor klanten\n\nEen prijs hangt af van oppervlakte, ondergrond, voorbereiding, bereikbaarheid en afwerking. Er staan daarom geen verzonnen vaste prijzen online. Een offerte- of afspraakaanvraag is vrijblijvend. Een afspraak staat pas vast nadat Stef het moment heeft afgestemd. Projectfoto’s tonen echt werk van Van Ommen Schilderwerken, maar ieder huis en iedere ondergrond is anders.\n\n## Pagina’s\n'+''.join(f'- [{r.strip("/").replace("-"," ") or "Home"}]({ORIGIN+r})\n' for r in ROUTES))
(OUT/'.openai/seo-runtime.json').write_text(json.dumps({'origin':ORIGIN,'routes':PUBLIC_ROUTES}))
print(f'Generated {len(ROUTES)} pages with metadata, structured data and sitemap.')
