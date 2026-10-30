# Vandentempel: nieuwe WordPress-website

Modernisering van [vandentempel.nl](https://vandentempel.nl/nl/) (nu Joomla met YOOtheme) naar WordPress, met behoud van de huisstijl.

## Wat er in deze map staat

| Map | Inhoud |
|---|---|
| `wp-content/themes/vandentempel/` | Het WordPress-blokthema. Kopieer deze map naar `wp-content/themes/` van de WordPress-installatie. |
| `import/vandentempel-content.xml` | Alle Nederlandse inhoud van de huidige site als WordPress-import (WXR): pagina's, producten, nieuws en afbeeldingen. |
| `import/redirects.csv` | 301-redirects van de oude Joomla-URL's naar de nieuwe URL's, voor de plugin Redirection. |
| `scripts/` | De scripts waarmee de import en de preview zijn gemaakt (`extract.py`, `build.py`). |
| `preview/` | Statische preview van de belangrijkste pagina's (niet in git; maak hem opnieuw met de scripts). |

## Huisstijl

Overgenomen van de huidige site en het logo:

- **Vandentempel-blauw `#0067B1`**: hoofdkleur (logo, knoppen, links, paginakoppen).
- **Antraciet `#363738`**: donkere vlakken (topbalk, footer, "Zekerheid in spanning"-blok).
- **Grijs `#A8A7B7`**: alleen decoratief (niet voor tekst, te weinig contrast).
- Afgeleide tinten voor hover en achtergronden: blauw donker `#00508A`, blauw licht `#E6F0F8`, lichtgrijs `#F4F5F8`.
- **Lettertype Lato** (400, 700, 900), lokaal meegeleverd in het thema (SIL Open Font License, zie `assets/fonts/OFL-Lato.txt`). Geen Google Fonts nodig.
- **Logo**: het originele SVG-woordmerk; voor de donkere footer een witte versie (`logo-white.svg`, alleen de vulkleur aangepast).
- Slogan **"Zekerheid in spanning"** staat in hero, USP-blok en footer.

Er was geen apart brandbook beschikbaar. Kleuren en lettertype komen uit de CSS en het logo van de huidige site. Heeft de klant een brandbook met andere waarden, pas dan alleen `theme.json` (palet) en de twee logobestanden aan.

## Installeren

1. **WordPress 6.5 of nieuwer** installeren. Taal: Nederlands.
2. **Thema**: kopieer `wp-content/themes/vandentempel/` naar de site en activeer het onder Weergave → Thema's.
3. **Permalinks**: Instellingen → Permalinks → "Berichtnaam" (`/%postname%/`).
4. **Inhoud importeren**: Extra → Importeren → WordPress (plugin "WordPress Importer"). Kies `import/vandentempel-content.xml`, wijs de auteur toe en vink **"Download en importeer bijlagen"** aan. De afbeeldingen worden dan van vandentempel.nl naar de mediabibliotheek gehaald en de links in de pagina's worden omgezet. Doe dit terwijl de oude site nog online is.
5. **Voorpagina**: Instellingen → Lezen → "Een statische pagina": voorpagina **Home**, berichtenpagina **Nieuws**.
6. **Redirects**: installeer de plugin Redirection en importeer `import/redirects.csv` (Extra → Redirection → Importeren/Exporteren). Zo blijven oude links en Google-resultaten werken.
7. **Contactformulier**: de oude site had een formulier. Installeer een formulierplugin (bijv. WPForms of Contact Form 7) en voeg het formulier toe op de pagina Contact. De pagina heeft nu mail- en belknoppen.
8. **Menu**: het hoofdmenu staat in de header (Weergave → Editor → Patronen → Header). WordPress zet het bij de eerste bewerking om naar een gewoon navigatiemenu.

## Wat het thema biedt

- Header met topbalk (telefoon, e-mail, FR), hoofdmenu met uitklapmenu voor de acht productgroepen en een contactknop. Plakt bovenaan bij scrollen.
- Homepage: hero "Zekerheid in spanning", productgroepen als beeldtegels, USP-blok (Advies, Levering, Nazorg, Trainingen), productnieuws, diensten (Service, Trainingen, Verhuur), laatste nieuws en een contactblok.
- Productgroep- en subcategoriepagina's met kaarten voor subcategorieën en producten, en een kruimelpad.
- Productpagina's met grote productfoto, intro, knoppen voor offerte en bellen, en daaronder de volledige beschrijving en specificaties.
- Nieuwsoverzicht en nieuwsberichten, zoekpagina en 404-pagina.
- Blokstijlen "Kaart" (groep) en "Omlijnd licht" (knop), bewerkbaar in de editor.
- Toegankelijk: voldoende kleurcontrast, zichtbare focus, "naar de inhoud"-link in de preview, respecteert "minder beweging".

## Bekende beperkingen

- **Niet getest in een draaiende WordPress.** In de bouwomgeving kon WordPress niet worden gedownload. Thema en import zijn gemaakt volgens de WordPress-formaten (theme.json v3, blokmarkup, WXR 1.2), maar controleer na installatie of de editor bij een blok "Blok bevat onverwachte inhoud" meldt. Kies dan "Herstel blok".
- **Geïmporteerde teksten** van de oude site staan als "Klassiek"-blok. Met "Converteren naar blokken" maak je er losse blokken van.
- **Franse site** (`/fr/`) is niet meegenomen. De FR-link in de topbalk wijst nog naar de oude Franse pagina's.
- **Productlabels** (merken, zoals BAUR, Raytech) zijn niet als aparte taxonomie overgenomen.
- **Nieuwsbrief-inschrijving** uit de oude footer is weggelaten. Voeg zo nodig een nieuwsbriefblok toe (bijv. Mailchimp).
- Pagina's die bij het ophalen niet bereikbaar waren, ontbreken. Draai de scripts opnieuw om aan te vullen.

## Preview in één bestand (met shop)

`scripts/combine.py` maakt van de preview één zelfstandig HTML-bestand met alle pagina's, afbeeldingen en het lettertype. Daarin zit ook een **shop met offertelijst** (`scripts/shop_parts.py`): alle producten met zoeken en filters, "Zet op offertelijst" op elke productpagina, een offertelijst met aantallen en een aanvraagformulier dat een e-mail aan info@vandentempel.nl opent.

De shop bestaat alleen in de preview. Voor WordPress is dit later te bouwen met WooCommerce plus een offerteplugin (bijv. "Request a Quote for WooCommerce"), of met een eenvoudige eigen offertelijst.

## Opnieuw opbouwen

```bash
# 1. Pagina's ophalen (elke pagina = md5(pad)[:12].html)
python3 -I scripts/crawl.py <crawl-map> 1500
# 2. Inhoud extraheren
python3 -I scripts/extract.py <crawl-map> content.json
# 3. Import, redirects en preview maken
python3 -I scripts/build.py content.json . --preview-all
python3 -I scripts/media.py preview preview/media
python3 -I scripts/build.py content.json . --preview-all --preview-media preview/media
# 4. Alles in één HTML-bestand, met shop
python3 -I scripts/combine.py preview vandentempel-website.html
```
