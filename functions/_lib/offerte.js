// Offerteaanvragen: validatie, mails en hulpfuncties zonder Cloudflare-specifieke imports,
// zodat tests/offerte.test.mjs ze in Node kan draaien.

export const SERVICES=['Binnenschilderwerk','Buitenschilderwerk','Houtrotreparatie','Onderhoud & renovatie','Spuitwerk','Behangwerk','Zakelijk & VvE-schilderwerk','Meerdere werkzaamheden / ik weet het nog niet'];
export const TYPES=['Particulier','Zakelijk','VvE'];
export const MAX_BODY_BYTES=64*1024;
export const OWNER_EMAIL='info@vanommenschilderwerken.nl';
export const OWNER_PHONE='06 24 99 67 00';

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const clean=value=>typeof value==='string'?value.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'').trim():'';

/** Normaliseert de ingevulde velden. Onbekende velden vallen weg. */
export function normalize(fields){
 const get=name=>clean(fields?.[name]);
 return {name:get('name'),email:get('email').toLowerCase(),phone:get('phone'),city:get('city'),type:get('type'),service:get('service'),requestKey:get('requestKey'),website:get('website')};
}

/** Geeft een foutmelding voor de bezoeker, of null als de aanvraag klopt. */
export function validate(data){
 if(!data||typeof data!=='object')return 'Controleer uw gegevens.';
 if(data.website)return 'De aanvraag kon niet worden verwerkt. Bel Stef gerust op '+OWNER_PHONE+'.';
 if(data.name.length<2||data.name.length>100)return 'Vul uw naam in.';
 if(data.city.length<2||data.city.length>100)return 'Vul uw woonplaats in.';
 if(data.email.length<5||data.email.length>150||!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(data.email))return 'Vul een geldig e-mailadres in.';
 if(data.phone&&(!/^[+\d ()./-]{6,30}$/.test(data.phone)||data.phone.replace(/\D/g,'').length<6))return 'Vul een geldig telefoonnummer in, of laat het veld leeg.';
 if(!TYPES.includes(data.type))return 'Geef aan of de aanvraag particulier, zakelijk of voor een VvE is.';
 if(!SERVICES.includes(data.service))return 'Kies de werkzaamheden.';
 if(data.requestKey&&!UUID.test(data.requestKey))return 'Vernieuw de pagina en probeer opnieuw.';
 return null;
}

const label=data=>`Naam: ${data.name}\nWoonplaats: ${data.city}\nType: ${data.type}\nE-mail: ${data.email}\nTelefoon: ${data.phone||'niet ingevuld'}\nWerkzaamheden: ${data.service}`;

/** Mail naar Stef met de aanvraag. */
export function mailToOwner(data,{from,to=OWNER_EMAIL,id}){
 return {
  from,to:[to],reply_to:data.email,
  subject:`Offerteaanvraag (${data.type.toLowerCase()}): ${data.service} in ${data.city} (${data.name})`,
  text:`Nieuwe offerteaanvraag via de website.\n\n${label(data)}\n\nAntwoord op deze mail om de klant te bereiken.\nAanvraagnummer: ${id}`,
 };
}

/** Bevestiging aan de klant, zonder bijlagen. */
export function mailToCustomer(data,{from,id}){
 return {
  from,to:[data.email],reply_to:OWNER_EMAIL,
  subject:'Uw offerteaanvraag bij Van Ommen Schilderwerken',
  text:`Beste ${data.name},\n\nBedankt voor uw aanvraag. Stef van Ommen neemt contact met u op om het werk te bespreken.\n\nDit heeft u doorgegeven:\n${label(data)}\n\nWilt u nog iets toevoegen of heeft u haast? Bel ${OWNER_PHONE} of antwoord op deze mail.\n\nMet vriendelijke groet,\nStef van Ommen\nVan Ommen Schilderwerken\nBovendwarsweg 78, 8096 PR Oldebroek\n\nAanvraagnummer: ${id}`,
 };
}

/** Controleert het Turnstile-antwoord bij Cloudflare. */
export async function verifyTurnstile(token,secret,ip,transport=fetch){
 if(!token)return false;
 const body=new URLSearchParams({secret,response:token});
 if(ip)body.set('remoteip',ip);
 try{
  const response=await transport('https://challenges.cloudflare.com/turnstile/v0/siteverify',{method:'POST',body});
  const result=await response.json();
  return result.success===true;
 }catch{return false;}
}

/** Verstuurt één mail via Resend. Geeft het mail-id terug, of null als het niet lukte. */
export async function sendMail(payload,apiKey,idempotencyKey,transport=fetch){
 try{
  const response=await transport('https://api.resend.com/emails',{method:'POST',headers:{Authorization:'Bearer '+apiKey,'Content-Type':'application/json','Idempotency-Key':idempotencyKey},body:JSON.stringify(payload)});
  const result=await response.json();
  return response.ok&&typeof result.id==='string'?result.id:null;
 }catch{return null;}
}

