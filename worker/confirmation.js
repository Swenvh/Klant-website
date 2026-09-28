export function mailReady(env){return Boolean(env.RESEND_API_KEY&&env.CONFIRMATION_EMAIL_FROM);}
export function validMoment(date,time,now=new Date()){
 if(typeof date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(date)||typeof time!=='string'||!/^([01]\d|2[0-3]):[0-5]\d$/.test(time))return false;
 const parsed=new Date(date+'T12:00:00Z');
 if(!Number.isFinite(parsed.getTime())||parsed.toISOString().slice(0,10)!==date)return false;
 const parts=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now);
 const get=x=>parts.find(p=>p.type===x).value;
 const current=`${get('year')}-${get('month')}-${get('day')}T${get('hour')}:${get('minute')}`;
 if(date+'T'+time<=current)return false;
 const nominal=Date.parse(date+'T'+time+':00Z');
 const formatter=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
 return [1,2].filter(offset=>formatter.format(new Date(nominal-offset*3600000)).replace(' ','T')===date+'T'+time).length===1;
}
export function confirmationMail(item,date,time,from){
 const label=new Date(date+'T12:00:00Z').toLocaleDateString('nl-NL',{timeZone:'Europe/Amsterdam',weekday:'long',day:'numeric',month:'long',year:'numeric'});
 return {from,to:[item.email],reply_to:'info@vanommenschilderwerken.nl',subject:'Uw afspraak met Van Ommen Schilderwerken is bevestigd',text:`Beste ${item.name},\n\nUw afspraak met Stef van Ommen is bevestigd.\n\nDatum: ${label}\nTijd: ${time} uur (Nederlandse tijd)\nAdres: ${item.address}, ${item.city}\nOnderwerp: ${item.service}\n\nTijdens dit bezoek bespreken we uw schilderwensen en bekijken we het werk. Dit is geen opdrachtbevestiging voor de uitvoering van het schilderwerk.\n\nWilt u de afspraak wijzigen of annuleren? Antwoord op deze e-mail of bel 06 24 99 67 00.\n\nMet vriendelijke groet,\nStef van Ommen\nVan Ommen Schilderwerken\ninfo@vanommenschilderwerken.nl\n06 24 99 67 00`};
}
export async function confirmAppointment(id,input,env,transport=fetch){
 const fail=(error,status=400)=>({status,body:{error}});
 if(input?.approved!==true)return fail('Controleer het e-mailadres, de datum en tijd en geef akkoord op het versturen.');
 if(!mailReady(env))return fail('E-mailverzending is nog niet ingesteld. De afspraak is niet bevestigd en er is geen mail verstuurd.',503);
 let item=await env.DB.prepare('SELECT * FROM appointment_requests WHERE id=?').bind(id).first();
 if(!item)return fail('Aanvraag niet gevonden.',404);
 if(item.confirmation_email_id){
  if(item.confirmed_date!==input.date||item.confirmed_time!==input.time)return fail('Er is al een bevestiging voor een ander moment verstuurd. Stem wijzigingen rechtstreeks met de klant af.',409);
  return {status:200,body:{ok:true,emailAccepted:true,alreadySent:true}};
 }
 if(['geannuleerd','afgerond'].includes(item.status))return fail('Deze aanvraag is afgesloten.',409);
 if(!validMoment(input.date,input.time))return fail('Kies een geldige toekomstige datum en tijd in Nederland.');
 if(!item.confirmation_payload){
  const payload=JSON.stringify(confirmationMail(item,input.date,input.time,env.CONFIRMATION_EMAIL_FROM));
  await env.DB.prepare('UPDATE appointment_requests SET confirmation_payload=?,confirmation_started_at=?,confirmed_date=?,confirmed_time=? WHERE id=? AND confirmation_payload IS NULL AND status NOT IN (?,?)').bind(payload,Date.now(),input.date,input.time,id,'geannuleerd','afgerond').run();
  item=await env.DB.prepare('SELECT * FROM appointment_requests WHERE id=?').bind(id).first();
 }
 if(!item.confirmation_payload||item.confirmed_date!==input.date||item.confirmed_time!==input.time)return fail('Er is al een bevestiging voorbereid voor een ander moment. Controleer eerst de verzendstatus.',409);
 // Retry only inside Resend's 24h idempotency window. Unknown older sends
 // require reconciliation at the provider; never silently send a duplicate.
 if(Date.now()-item.confirmation_started_at>23*3600000)return fail('De verzendstatus is onzeker. Controleer de mail bij de verzenddienst voordat u opnieuw verstuurt.',409);
 try{
  const response=await transport('https://api.resend.com/emails',{method:'POST',headers:{Authorization:'Bearer '+env.RESEND_API_KEY,'Content-Type':'application/json','Idempotency-Key':'appointment-confirmation/'+id},body:item.confirmation_payload,signal:AbortSignal.timeout(12000)});
  const result=await response.json();
  if(!response.ok||typeof result.id!=='string')return fail('De verzenddienst heeft de mail niet bevestigd. Controleer de instellingen en probeer dezelfde bevestiging opnieuw.',502);
  await env.DB.prepare('UPDATE appointment_requests SET confirmation_email_id=?,status=?,updated_at=? WHERE id=? AND confirmation_email_id IS NULL').bind(result.id,'bevestigd',Date.now(),id).run();
  return {status:200,body:{ok:true,emailAccepted:true}};
 }catch{
  return fail('De verzendstatus kon niet worden bevestigd. Probeer dezelfde bevestiging opnieuw; er wordt gecontroleerd op dubbele verzending.',502);
 }
}
