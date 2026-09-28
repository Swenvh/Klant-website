from html import escape

# Ordered by the visitor's decision: price and timing, living at home, next steps.
# No invented fixed rates, response times, free visits or warranty periods.
GROUPS = [
 ('kosten-planning', 'Kosten en planning', [
  ('kosten', 'Wat kost het om mijn huis te laten schilderen?',
   'Dat hangt af van wat u wilt laten schilderen, de oppervlakte en de staat van de bestaande verf en het hout. Ook voorbereiding en bereikbaarheid tellen mee. Vertel welke kamers of onderdelen het betreft. Na het bespreken en bekijken van het werk kan Stef een passende offerte maken. Alleen een aantal vierkante meters geeft nog geen betrouwbare totaalprijs.'),
  ('offerte', 'Wat moet er in mijn offerte staan?',
   'U wilt weten welk werk wordt gedaan en wat u daarvoor betaalt. Bespreek daarom de te schilderen onderdelen, voorbereiding, verf en afwerking, afdekken en opruimen, eventuele hulpmiddelen en de totaalprijs inclusief btw. Laat ook vastleggen wat buiten de prijs valt en hoe eventueel extra werk wordt afgesproken. Is iets niet duidelijk? Vraag het vóór u akkoord geeft.'),
  ('start', 'Wanneer kunnen jullie beginnen?',
   'Dat hangt af van de lopende planning en uw schilderwerk. Geef uw gewenste periode door, bijvoorbeeld vóór een verhuizing. Stef bespreekt wat mogelijk is. Een datum in de afsprakenplanner is bedoeld om het werk te bespreken; het is niet de startdatum van het schilderen.'),
  ('duur', 'Hoe lang duurt het schilderwerk?',
   'Dat verschilt per klus. Een kamer vraagt een andere planning dan de hele buitenkant van een huis. Voorbereiden, reparaties en drogen tussen de verflagen kosten ook tijd. Vraag bij het bespreken van de offerte naar de verwachte werkdagen en wanneer u de ruimtes of geschilderde onderdelen weer kunt gebruiken.')]),
 ('voorbereiding', 'Voorbereiding en uw woning', [
  ('meubels', 'Moet ik zelf meubels verplaatsen en alles afdekken?',
   'Spreek vooraf af wat u zelf doet en wat Stef verzorgt. Maak de te schilderen plekken bereikbaar en bespreek het verplaatsen van grote meubels. Haal losse en kwetsbare spullen weg bij de werkplek. Begin niet zelf met schuren of afplakken zonder overleg; zo voorkomt u dubbel werk.'),
  ('thuis', 'Kan ik gewoon thuis blijven tijdens het schilderen?',
   'Bespreek welke kamers u nodig heeft tijdens het werk. We bekijken of werken per ruimte mogelijk is en hoe de werkplek bereikbaar blijft. U hoeft niet vanzelfsprekend de hele dag aanwezig te zijn: afspraken over toegang tot de woning maakt u vooraf met Stef.'),
  ('overlast', 'Hoeveel last heb ik van stof, verfgeur en nat schilderwerk?',
   'Voorbereiden en schilderen kunnen tijdelijk stof, geur en minder bruikbare ruimte geven. Bespreek vooraf hoe de werkplek wordt afgeschermd en welke ruimtes, deuren of trappen tijdelijk niet gebruikt kunnen worden. Vraag ook wanneer de verf voldoende droog is. Houd kinderen en huisdieren tijdens het werk buiten de werkplek.'),
  ('verf', 'Moet ik zelf verf kopen of al een kleur kiezen?',
   'Nee, u hoeft vooraf niets te kopen of al een definitieve kleur te weten. Bespreek eerst het gewenste resultaat en welke materialen in de offerte worden opgenomen. Heeft u al verf of een kleurnummer? Geef dat door, zodat Stef kan beoordelen of dit past bij de ondergrond en het werk.'),
  ('weer', 'Wat gebeurt er als het regent tijdens het buitenwerk?',
   'Regen, temperatuur en een vochtige ondergrond kunnen de uitvoering beïnvloeden. Als het weer niet geschikt is, moet het buitenwerk worden aangepast of uitgesteld. De gevolgen voor de planning worden met u besproken; de voorbereiding en het drogen blijven onderdeel van het werk.')]),
 ('aanvraag-oplevering', 'Van aanvraag tot oplevering', [
  ('kleine-klus', 'Kan ik ook één kamer, een deur of een trap laten schilderen?',
   'U kunt ook een kleinere klus bespreken. Geef aan wat u wilt laten schilderen en waar de woning staat. Dan kan Stef beoordelen welke aanpak en planning daarbij passen. U hoeft dus niet te wachten tot uw hele huis aan de beurt is.'),
  ('aanvragen', 'Hoe vraag ik een prijs aan en moet ik foto’s meesturen?',
   'Vertel wat u wilt laten schilderen, in welke plaats en in welke periode. Een overzichtsfoto en een foto van beschadigingen helpen, maar zijn niet verplicht. U kunt bellen, WhatsApp gebruiken of het offerteformulier invullen. Het offerteformulier maakt een e-mail klaar die u zelf nog verstuurt. Foto’s voegt u toe in uw e-mail of WhatsApp.'),
  ('vast', 'Zit ik na een aanvraag meteen aan schilderwerk vast?',
   'Met het offerteformulier of de afsprakenplanner geeft u uw wensen door. Daarmee geeft u nog geen akkoord voor de uitvoering. Eerst bespreekt u het werk en de offerte. De uitvoering en planning worden na uw akkoord afgestemd. Vraag bij het eerste contact ook naar eventuele kosten voor een bezoek of advies.'),
  ('afspraak', 'Is mijn afspraak direct bevestigd en krijg ik een e-mail?',
   'Nee. Na het invullen van de planner wordt uw voorkeur opgeslagen en ziet u een bevestiging op de website. Er wordt geen automatische e-mail verstuurd. De afspraak staat pas vast wanneer Stef het moment met u heeft afgestemd. Wilt u de voorkeur wijzigen of heeft u nog niets gehoord? Bel of stuur een WhatsApp-bericht met uw naam en de aangevraagde datum.'),
  ('oplevering', 'Wat als ik na afloop nog een plek zie die niet goed is?',
   'Bekijk het eindresultaat samen met Stef en benoem wat u opvalt. Ontdekt u later iets, stuur dan een foto met een korte uitleg of bel hem. Dan kan hij de situatie beoordelen en met u bespreken wat nodig is. Vraag vóór de opdracht welke garantieafspraken en voorwaarden voor uw schilderwerk gelden.')])
]

HOME_IDS={'kosten','start','duur','meubels','thuis','aanvragen'}

def faq_html(compact=False):
 parts=[]
 for group_id,title,questions in GROUPS:
  selected=[q for q in questions if not compact or q[0] in HOME_IDS]
  if not selected:continue
  if not compact:parts.append(f'<section class="faq-group" id="vragen-{group_id}" aria-labelledby="faq-heading-{group_id}"><h3 id="faq-heading-{group_id}">{escape(title)}</h3>')
  for key,question,answer in selected:
   opened=' open' if key=='kosten' else ''
   parts.append(f'<details id="vraag-{key}"{opened}><summary>{escape(question)}<span class="plus" aria-hidden="true"></span></summary><p>{escape(answer)}</p></details>')
  if not compact:parts.append('</section>')
 if compact:
  extra='<a class="text-link" href="/contact/#vragen">Bekijk alle vragen en antwoorden</a>'
 else:
  extra='<nav class="faq-topics" aria-label="Onderwerpen bij veelgestelde vragen">'+''.join(f'<a href="#vragen-{slug}">{escape(title)}</a>' for slug,title,_ in GROUPS)+'</nav>'
 return '<section class="faq customer-faq section-pad section-space" id="vragen" aria-labelledby="customer-faq-title"><div class="faq-intro"><p class="eyebrow">VEELGESTELDE VRAGEN</p><h2 id="customer-faq-title">Dit wilt u weten<br>vóór we beginnen.</h2><p>Over de kosten, uw voorbereiding en wat er bij u thuis gebeurt.</p>'+extra+'<p>Liever uw situatie bespreken?<br><a class="text-link" href="tel:+31624996700">Bel Stef: 06 24 99 67 00</a></p></div><div class="faq-list">'+''.join(parts)+'</div></section>'
