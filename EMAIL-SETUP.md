# Bevestigingsmail na akkoord

De eigenaar kiest in het afgeschermde afsprakenbeheer een definitieve datum en
tijd, controleert het klantadres en geeft expliciet akkoord op mailverzending.
Alleen deze actie verstuurt een bevestiging. Een aanvraag of gewone statuswijziging
verstuurt geen mail. De ontvanger komt uitsluitend uit de opgeslagen aanvraag.

## Activeren

1. Maak een Resend-account op naam van de verantwoordelijke onderneming.
2. Verifieer het afzenderdomein met de DNS-records die Resend verstrekt.
   Verander geen bestaande mailroutering of MX-records van de hoofddomeinmailbox.
3. Stel een verzendsleutel in als servergeheim `RESEND_API_KEY` en zet
   `CONFIRMATION_EMAIL_FROM` op het geverifieerde adres, bijvoorbeeld
   `Van Ommen Schilderwerken <info@vanommenschilderwerken.nl>`.
4. Geef Stef na expliciete overdracht de juiste beheertoegang. De huidige
   `APPOINTMENT_ADMIN_EMAIL` blijft ongewijzigd.
5. Doe met toestemming een echte proefaanvraag met een eigen bereikbaar adres,
   bevestig deze en controleer de ontvangst, antwoorden en verzendregistratie.

De koppeling is nog niet geactiveerd. Er zijn geen echte e-mails verstuurd bij
de ontwikkeling; tests gebruiken uitsluitend een nagebootste verzenddienst.

## Betrouwbaarheid en grenzen

De database bewaart vóór verzending de exacte mailinhoud en het definitieve
moment. Een vaste idempotency key voorkomt dubbele verzending bij retries.
De status wordt pas bevestigd nadat Resend de mail heeft geaccepteerd. Dat is
geen bewijs van aflevering in de inbox. Aflevering/bounces zijn in Resend te
controleren; webhookmeldingen worden nog niet in het beheer getoond.

Bij onzekere verzending blijft de inhoud vaststaan. Opnieuw proberen verstuurt
hetzelfde bericht met dezelfde sleutel. Na 23 uur worden retries geblokkeerd,
omdat de verzenddienst de sleutel 24 uur bewaart. Controleer dan eerst het
providerlog; herstel de registratie alleen op basis van de aangetroffen status.
Er is geen achtergrondtaak die zelfstandig nieuwe berichten verstuurt.

Wijzigen of annuleren na een bevestiging vraagt rechtstreeks contact met de
klant. Een statuswijziging stuurt geen nieuwe mail. De eerste bevestiging blijft
in de database bewaard. Agendasynchronisatie en een kalenderbijlage zijn niet
onderdeel van deze implementatie.

Documentatie: https://resend.com/docs/dashboard/emails/idempotency-keys
en https://resend.com/docs/dashboard/domains/introduction
