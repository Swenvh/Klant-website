# Website en lokale vindbaarheid

De website heeft 18 bezoekerspagina’s en een afgeschermd aanvraagoverzicht.
De lokale pagina’s voor Oldebroek, Wezep, Zwolle, Elburg en Nunspeet zijn alleen
via de footer met het kopje **Snelle links** opgenomen in de navigatie.
Alle vijf hebben eigen inhoud, vragen, metadata en Service-schema met het
betreffende werkgebied. De bedrijfsvestiging blijft uitsluitend Oldebroek.
Projectfoto’s krijgen
geen onbevestigde plaatsaanduiding.

Elke pagina heeft een eigen titel, beschrijving, canonical, Open Graph- en
Twitter-tekstmetadata. JSON-LD beschrijft het schildersbedrijf, de website,
de pagina en waar van toepassing de kruimelpadnavigatie en dienst.
Er zijn geen beoordelingen, openingstijden, keurmerken, prijzen of garanties
verzonnen. Het overzicht staat in `dist/sitemap.xml`.

De hero is voor snellere weergave als WebP gecodeerd: 399.430 bytes tegenover
2.496.955 bytes voor de PNG (ongeveer 84% kleiner), met dezelfde pixelafmetingen.
Dit is lossy compressie op kwaliteit 92; de originele PNG en het goedgekeurde
HD-logo zijn behouden. De mobiele achtergrond gebruikt hetzelfde WebP-bestand.

## Technische SEO bijgewerkt op 27 september 2026

- Alle 18 bezoekerspagina’s zijn indexeerbaar in hun HTML (`indexable: true`).
  Het beheer houdt noindex en serverautorisatie. De hostingtoegang is nog privé;
  Google kan de website daarom nog niet crawlen. Een openbare lancering vergt
  een wijziging van de doelgroep op verzoek van de eigenaar.
- Het domein preview.vanommenschilderwerken.nl is nog pending met SSL-validatie.
  Canonicals en sitemap gebruiken het bestaande actieve Sites-adres. Bevestig
  bij lancering het actieve productiedomein en wijzig `origin` centraal.
- Elke pagina heeft precies één H1 en een gecontroleerde kopvolgorde. Het
  dienstenoverzicht toont de zeven diensten als tegels; interne links leiden
  naar projecten, contactvragen en relevante diensten.
- Open Graph en Twitter gebruiken de bestaande goedgekeurde busfoto, met
  absolute URL, afmetingen en alternatieve tekst. Er is geen nieuwe foto gemaakt.
- Foto’s hebben responsive WebP-versies en echte pixelafmetingen. Lokale
  lettertypen zijn verkleind tot West-Europese tekens, met font-display swap.
  De hero krijgt voorrang; overige foto’s worden lui geladen. Dit zijn
  optimalisaties, geen gemeten Core Web Vitals-score of garantie.
- HTTP wordt doorgestuurd naar HTTPS. Bestaande pagina-aliases met hoofdletters,
  index.html, .html of ontbrekende eindslash krijgen een permanente 308-redirect.
  Queryparameters blijven bewaard. Bestaande korte slugs blijven behouden.
- sitemap.xml, robots.txt en llms.txt worden centraal gegenereerd. Beheer is
  uitgesloten van sitemap en llms.txt. llms.txt is een informatief overzicht,
  geen indexeringsgarantie of vervanging voor robots.txt.
- Search Console is nog niet geverifieerd: er is geen Google-accountverbinding
  of eigendomstoken beschikbaar. `google_site_verification` staat bewust leeg.
  Vul de echte HTML-verificatiecode in seo-config.json in en publiceer opnieuw;
  verifieer vervolgens een openbare URL-prefixproperty en dien sitemap.xml in.
  Voor domeinverificatie is het door Google verstrekte DNS-TXT-record nodig.

Het offerteformulier opent bewust een e-mailconcept. Het verstuurt niets via
een server. De uitleg, knop en status maken duidelijk dat de bezoeker zelf
de e-mail nog moet versturen; bellen en WhatsApp blijven direct beschikbaar.

De aparte afsprakenplanner op `/afspraak/` slaat aanvragen wel op in D1.
De voorkeursdatum en het dagdeel zijn geen gegarandeerde beschikbaarheid.
De beheerpagina `/afspraken-beheer/` wordt alleen aan de server-side
geautoriseerde beheerder getoond en staat niet in de sitemap of de openbare
bestanden. `APPOINTMENT_ADMIN_EMAIL` wordt via Sites ingesteld op het account
van de eigenaar. Wijzig die instelling pas bij een expliciete overdracht.
De planner bevestigt alleen de opslag van de aanvraag. De beheerder kan na
het kiezen van een definitieve datum en tijd expliciet een bevestigingsmail
versturen. De Resend-koppeling is voorbereid maar vereist nog configuratie;
zie EMAIL-SETUP.md. Een gewone statuswijziging stuurt geen bericht.

De Worker verwerkt de planner-API en de afgeschermde beheerpagina; bestaande
HTML, CSS, scripts en afbeeldingen blijven behouden als statische client.
`npm run build` genereert beide onderdelen. Drizzle-migraties in `drizzle/`
worden door Sites toegepast. Reeds toegepaste migraties niet wijzigen.
`npm run check` controleert de bezoekerspagina’s en test opslag, herhaalde
aanvragen, autorisatie, bevestiging, datumgrenzen en uitval van de database.

Gebruikte richtlijnen:
- https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- https://developers.google.com/search/docs/appearance/structured-data/local-business

## Controleren

De algemene klantvragen staan centraal in `scripts/customer_questions.py`:
zes prioriteitsvragen op de homepage, veertien vragen verdeeld over kosten,
planning, voorbereiding en aanvraag/oplevering op de contactpagina.
De selectie is redactioneel vanuit de klantreis; er zijn geen gemeten
vraagfrequenties of zoekvolumes geclaimd. Gratis bezoek, vaste doorlooptijden,
garantietermijnen en prijzen worden niet zonder bedrijfsbevestiging beloofd.
Het offerteformulier behoudt een WhatsApp-alternatief met de reeds ingevulde
wensen. De afsprakenplanner vermeldt expliciet dat het om een bezoekaanvraag
gaat en dat er geen automatische bevestigingsmail wordt verzonden.

`python scripts/generate-pages.py` genereert alle pagina’s en de sitemap.
`python scripts/validate-site.py` controleert inhoud, lokale links, metadata,
afbeeldingen en de afgesproken scheiding tussen footer en hoofdmenu.

## Afronding op 28 september 2026

- Er zijn een eigen 404-pagina, een bedankpagina na een afspraakaanvraag,
  een privacyverklaring en websitevoorwaarden toegevoegd. De laatste pagina
  gaat alleen over het gebruik van de website; opdrachtvoorwaarden blijven
  onderdeel van de offerte of opdrachtbevestiging.
- De website telt paginaweergaven en belangrijke contactacties zonder cookies,
  IP-adressen, unieke bezoeker-ID's of profielen. Alleen totalen per dag,
  pagina en actie worden opgeslagen. Daarom wordt geen overbodige cookiebanner
  getoond. De beheerder ziet de afgelopen dertig dagen afgeschermd bij de
  afspraakaanvragen; herhaalde bezoeken en bots kunnen worden meegeteld.
- Afspraakaanvragen hebben een bewaarbeleid van twaalf maanden en de anonieme
  totalen veertien maanden. Verouderde regels worden bij een volgende aanvraag
  of beheercontrole automatisch verwijderd.
- De Open Graph-afbeelding is een aparte geoptimaliseerde JPEG van 1600 bij
  900 pixels. De pagina-hero blijft als responsive WebP geladen.
- De Worker geeft onbekende bezoekersroutes de eigen 404-inhoud met echte
  HTTP-status 404 en `noindex`. De bedankpagina is eveneens `noindex` en staat
  niet in sitemap.xml of llms.txt.

## GEO- en AI-vindbaarheid op 28 september 2026

- `OAI-SearchBot`, Googlebot en bingbot zijn expliciet toegestaan in
  robots.txt. Dit verandert niets aan de huidige privétoegang: crawlers kunnen
  de site pas bereiken nadat de eigenaar de site bewust openbaar maakt.
- De bedrijfsentiteit bevat consistente gegevens voor naam, adres, telefoon,
  e-mail, werkgebied, eigenaar, diensten en sociale profielen. Stef van Ommen
  heeft een gekoppelde Person-entiteit; de diensten staan als OfferCatalog en
  Service-entiteiten in JSON-LD.
- Zichtbare vragen en antwoorden worden automatisch als FAQPage-schema
  opgenomen. Het schema wordt uit dezelfde HTML opgebouwd, zodat het altijd
  overeenkomt met wat de bezoeker ziet.
- De Over Stef-pagina bevat een zichtbare feitenlijst met aanspreekpunt,
  vestigingsplaats, werkgebied, diensten en contact. Dit maakt kerninformatie
  begrijpelijk en citeerbaar zonder marketingclaims of verzonnen cijfers.
- Sitemapregels bevatten `lastmod`. `llms.txt` bevat een beknopte feitelijke
  samenvatting en links, maar wordt niet behandeld als rankingfactor. Google
  geeft aan dat goede, indexeerbare en nuttige content de basis blijft en dat
  speciale GEO-markup of AI-tekstbestanden niet vereist zijn.
- Geen vindbaarheid, positie of vermelding in een AI-antwoord wordt
  gegarandeerd. Na de openbare lancering moeten Google Search Console, Bing
  Webmaster Tools en het Google Bedrijfsprofiel worden geverifieerd en met
  exact dezelfde bedrijfsgegevens worden bijgehouden.
