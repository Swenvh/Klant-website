# Offerteformulier: afhandeling op Cloudflare Pages

Het formulier op `/offerte/` verstuurt naar de Pages Function `functions/api/offerte.js`.
Die bewaart de aanvraag in D1, mailt Stef en stuurt de klant een bevestiging via Resend. Spam wordt geweerd met een verborgen veld, een limiet per IP per uur en
Cloudflare Turnstile. Zonder JavaScript werkt het formulier als gewone POST en eindigt op
`/bedankt/offerte/`. De validatie staat in `functions/_lib/offerte.js` en wordt getest in
`tests/offerte.test.mjs`.

## Eenmalig instellen

1. **D1-database**: `npx wrangler d1 create van-ommen-schilderwerken`, zet het `database_id`
   in `wrangler.toml` en draai `npm run db:migrate`.
2. **Resend**: account aanmaken, het domein (bijvoorbeeld vanommenschilderwerken.nl) verifiëren
   met de DNS-records van Resend, een API-sleutel maken en zetten met
   `npx wrangler pages secret put RESEND_API_KEY`. Controleer `MAIL_FROM` en `MAIL_TO` in
   `wrangler.toml`; het afzenderadres moet op het geverifieerde domein staan.
3. **Turnstile**: in het Cloudflare-dashboard een widget maken voor het domein. De site key
   komt in `source/seo-config.json` (`turnstile_site_key`), daarna `npm run build`; de secret
   key met `npx wrangler pages secret put TURNSTILE_SECRET`. Zolang de secret ontbreekt, slaat
   de functie de controle over; zolang de site key ontbreekt, staat er geen widget op de pagina.
   Zet ze dus samen.
4. **Pages-project**: `npm run deploy` bouwt, controleert en publiceert `dist/` met de functions.
   Koppel de D1-binding `DB` in het Pages-project aan de database (wrangler doet dat via
   `wrangler.toml`).
5. **Proefaanvraag** met een eigen e-mailadres: controleer de mail bij Stef, de
   bevestiging bij de klant en de rij in D1 (`npx wrangler d1 execute van-ommen-schilderwerken
   --remote --command "SELECT name,city,customer_type,service,status,created_at FROM quote_requests ORDER BY created_at DESC LIMIT 5"`).

## Lokaal testen

```
cp .dev.vars.example .dev.vars
npm run db:migrate:local
npm run dev            # http://localhost:8788
```

Zonder `RESEND_API_KEY` worden aanvragen opgeslagen met status `mail_niet_ingesteld`.

## Statussen in `quote_requests`

- `nieuw`: opgeslagen, mail nog niet verstuurd.
- `gemaild`: mail naar Stef geaccepteerd door Resend (`mail_owner_id`), bevestiging idem.
- `mail_mislukt`: opgeslagen, maar Resend accepteerde de mail niet. Controleer het Resend-log.
- `mail_niet_ingesteld`: geen `RESEND_API_KEY` of `MAIL_FROM`.

Aanvragen ouder dan twaalf maanden mogen weg (privacyverklaring); er is nog geen automatische
opschoning.
